"""Phase A - extract page strings and translate them into every shipped locale.

Reads each project's page components, extracts visitor-visible copy, assigns
stable keys, translates with the configured AI provider, and writes the
results into every locale JSON. Does not touch page sources, so it cannot
break a build; wiring is a separate verified pass.

Translation cache: generated-projects/I18N_TRANSLATION_CACHE.json
Re-running only translates strings that are not already cached.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "generated-projects"
CACHE = PROJECTS / "I18N_TRANSLATION_CACHE.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from i18n_extract_strings import extract_file  # noqa: E402

TARGETS = ["ar", "de", "es", "fr", "hi", "id", "ja", "ko", "pt", "ru", "tr", "ur", "zh"]
BATCH = 15

# Providers are tried in rotation. Per-model quotas move around during a long
# sweep, so a model that returns 429/503 is put on a cooldown and skipped until
# it expires instead of burning retries. DeepSeek has no credit, and the
# OpenAI/Grok keys are rejected, so none of those are listed.
PROVIDERS = ["gemini-2.5-flash", "gemini-2.0-flash", "openrouter",
             "gemini-2.0-flash-exp", "gemini-flash-latest"]
COOLDOWN = {"gemini-2.5-flash": 300.0, "openrouter": 120.0}
_cool = {}


def load_env() -> dict:
    p = ROOT / "ai-agent" / ".env"
    env = {}
    if p.exists():
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                v = v.strip()
                if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                    v = v[1:-1]
                env[k.strip()] = v
    return env


ENV = load_env()


def _gemini(prompt: str, model: str, timeout: int = 180) -> str:
    key = ENV.get("GEMINI_API_KEY", "")
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={key}")
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 8192}}
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    return d["candidates"][0]["content"]["parts"][0]["text"].strip()


def _openrouter(prompt: str, timeout: int = 180) -> str:
    key = ENV.get("OPENROUTER_API_KEY", "")
    model = ENV.get("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")
    body = {"model": model, "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1, "max_tokens": 8192}
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    return d["choices"][0]["message"]["content"].strip()


def call_provider(prompt: str, provider: str) -> str:
    if provider.startswith("gemini"):
        return _gemini(prompt, provider)
    if provider == "openrouter":
        return _openrouter(prompt)
    raise ValueError(f"unknown provider {provider}")


def complete(prompt: str, attempts: int = 8) -> str:
    """Call providers with rotation and per-model cooldown; raise if all fail."""
    last = None
    for attempt in range(attempts):
        now = time.time()
        for provider in PROVIDERS:
            if _cool.get(provider, 0) > now:
                continue  # still cooling down
            try:
                out = call_provider(prompt, provider)
                _cool.pop(provider, None)
                return out
            except urllib.error.HTTPError as e:
                last = f"{provider} HTTP {e.code}"
                if e.code in (429, 500, 502, 503, 504):
                    # back off this model, but let the loop try the next one
                    _cool[provider] = time.time() + COOLDOWN.get(
                        provider, 90.0 * (attempt + 1))
            except Exception as exc:  # noqa: BLE001
                last = f"{provider} {type(exc).__name__}"
        time.sleep(min(30, 5 * (attempt + 1)))
    raise RuntimeError(f"all providers failed/cooling, last={last}")


def translate_batch(strings: list, retries: int = 3) -> dict:
    """Return {lang: [translated strings]} for one batch of source strings."""
    listing = json.dumps(strings, ensure_ascii=False)
    prompt = (
        "You are a professional software localizer. Translate each string in the "
        "JSON array into every one of these languages: " + ", ".join(TARGETS) + ".\n"
        "Rules:\n"
        "- Return ONLY valid JSON, no prose, no markdown fence.\n"
        "- Shape: {\"<lang>\": [\"...\", \"...\"], ...} with one key per language and "
        "the SAME number of entries as the input, in the SAME order.\n"
        "- Preserve any placeholder tokens like {t('x')} or {count} verbatim.\n"
        "- Use natural, professional marketing tone; keep brand names untranslated.\n"
        "- Do not translate HTML entities; keep &copy; and similar as-is.\n\n"
        f"Input strings:\n{listing}"
    )
    try:
        raw = complete(prompt)
    except Exception as exc:  # noqa: BLE001
        print(f"    batch failed ({exc})", flush=True)
        return {}
    for _ in range(3):
        try:
            raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
            data = json.loads(raw)
            if isinstance(data, dict):
                out = {}
                for lg in TARGETS:
                    v = data.get(lg)
                    if isinstance(v, list) and len(v) == len(strings):
                        out[lg] = v
                if out:
                    return out
        except Exception:  # noqa: BLE001
            pass
        # one repair attempt: ask the model to emit clean JSON only
        try:
            raw = complete("Your previous reply was not valid JSON. Re-emit ONLY the "
                           "JSON object, no prose, no fence, same languages and order:\n"
                           + raw[:6000])
        except Exception:  # noqa: BLE001
            break
    print("    batch failed (json shape)", flush=True)
    return {}


def load_cache() -> dict:
    if CACHE.exists():
        try:
            return json.loads(CACHE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_cache(c: dict):
    """Merge-safe write.

    A long sweep can be interrupted, and a stale writer must never clobber
    translations another run already stored. Re-read the file, merge our
    entries in, and only ever keep a version of an entry that is complete
    (all target languages present).
    """
    on_disk = load_cache()
    merged = dict(on_disk)
    for k, v in c.items():
        if not isinstance(v, dict):
            continue
        complete = all(t in v and v[t] for t in TARGETS)
        existing = merged.get(k)
        existing_complete = (
            isinstance(existing, dict) and all(t in existing and existing[t] for t in TARGETS)
        )
        if complete or not existing_complete:
            merged[k] = v
    tmp = CACHE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(merged, ensure_ascii=False, indent=0), encoding="utf-8")
    tmp.replace(CACHE)
    c.clear()
    c.update(merged)


def main():
    slugs = sys.argv[1:] or [d.name for d in sorted(PROJECTS.iterdir())
                             if (d / "frontend" / "package.json").exists()]
    cache = load_cache()

    def is_done(s: str) -> bool:
        """Only treat a string as translated when every target language exists."""
        e = cache.get(s)
        return bool(e) and all(t in e and e[t] for t in TARGETS)

    total_new = 0
    failed_total = 0
    for slug in slugs:
        src = PROJECTS / slug / "frontend" / "src" / "pages"
        if not src.exists():
            continue
        strings, order = [], {}
        for f in sorted(src.glob("*.jsx")):
            for kind, s in extract_file(f):
                if s not in order:
                    order[s] = f"{f.stem}"
                    strings.append(s)
        if not strings:
            continue
        todo = [s for s in strings if not is_done(s)]
        print(f"[{slug}] {len(strings)} strings, {len(todo)} need translation", flush=True)
        if not todo:
            continue
        done = 0
        failed_here = 0
        for i in range(0, len(todo), BATCH):
            batch = todo[i:i + BATCH]
            res = translate_batch(batch)
            if not res:
                # Do NOT write an English-only placeholder: an entry without all
                # target languages must stay untranslated so a later run retries it.
                failed_here += len(batch)
                print(f"    batch failed, {len(batch)} strings deferred", flush=True)
                time.sleep(4)
                continue
            for idx, s in enumerate(batch):
                entry = cache.setdefault(s, {})
                entry.setdefault("en", s)
                for lg in res:
                    entry[lg] = res[lg][idx]
            done += len(batch)
            total_new += len(batch)
            print(f"    {done}/{len(todo)}", flush=True)
            save_cache(cache)
            time.sleep(1.2)
        failed_total += failed_here
        save_cache(cache)
        if failed_here:
            print(f"    -> {failed_here} deferred for a later run", flush=True)
    save_cache(cache)
    still_missing = sum(1 for s in cache if not is_done(s))
    print(f"\nnewly translated: {total_new} | failed batches: {failed_total} | "
          f"cache size: {len(cache)} | entries awaiting retry: {still_missing}")


if __name__ == "__main__":
    main()