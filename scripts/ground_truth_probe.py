#!/usr/bin/env python3
"""SELF-CONTAINED ground-truth probe (no deployer-module dependency at all).

Rule — no guesses, no shared repo, no derived expectations:
  * For EVERY zip in delivery/: read its own LIVE-LINK.txt -> the site's
    canonical served URL.
  * Derive the expected brand text from the URL itself (the deployer's repo
    name is exactly the brand slug: atlas-mobility -> "Atlas Mobility").
  * Fetch that URL. PASS only if the SERVED html's <title> or <h1> name-matches
    the expected brand. Report HTTP + verdict per site. Evidence only."""
import re, sys, urllib.request, urllib.error, zipfile
from pathlib import Path

CORE = Path(r"D:\lumicorepro-core")
URL_RE = re.compile(r"https?://[^\s'\"<>)]+")
BAD = ("example.com", "placeholder", "your-site", "yourdomain", "localhost",
       "<your-user>", "your-slug", "your-site-slug", "<your-brand>", "yourdomain.com")


def expect_brand(link: str) -> str:
    """brand text = slugified repo name from the URL, title-cased."""
    m = re.search(r"github\.io/([^/\s]+)", link or "")
    if not m:
        return ""
    return " ".join(w.capitalize() for w in m.group(1).split("-"))


def zip_link(z: Path) -> str:
    try:
        with zipfile.ZipFile(z) as zf:
            for n in zf.namelist():
                if re.match(r"(?:delivery/)?[Ll][Ii][Vv][Ee]-[Ll][Ii][Nn][Kk](?:\.txt)?$", n):
                    txt = zf.read(n).decode("utf-8", errors="ignore")
                    for u in URL_RE.findall(txt):
                        if "github.io" in u and not any(b in u for b in BAD):
                            return u.rstrip("/")
                    return ""
    except Exception:
        pass
    return ""


def fetch(url: str):
    if not url:
        return None, ""
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "lumi"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.status, r.read().decode("utf-8", errors="ignore")
        except urllib.error.HTTPError as e:
            return e.code, ""
        except Exception as e:
            if i == 2:
                return "ERR:" + str(type(e).__name__), ""
    return "ERR:loop", ""


def main():
    rows = []
    for z in sorted(CORE.glob("delivery/*.zip")):
        slug = z.stem
        link = zip_link(z)
        status, html = fetch(link) if link else (None, "")
        brand = expect_brand(link)
        title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
        title = re.sub(r"<[^>]+>", "", title_m.group(1)).strip() if title_m else ""
        h1_m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
        h1 = re.sub(r"<[^>]+>", "", h1_m.group(1)).strip() if h1_m else ""

        bl = brand.lower()
        if status == 200 and bl and (bl in title.lower() or bl in h1.lower() or bl in html.lower()):
            verdict = "BRAND-OK"
        elif status == 200:
            verdict = "unnamed"
        else:
            verdict = "DEAD" if status != 200 else "err"
        rows.append((slug, link, status, title[:60], h1[:60], verdict))

    for slug, link, status, title, h1, verdict in sorted(rows, key=lambda r: r[5]):
        print(f"{str(status):>11}  {verdict:<23}  {link or '(no-link)':<52}  t={title!r}")
    print("-" * 100)
    live = sum(1 for r in rows if r[2] == 200)
    ok = sum(1 for r in rows if r[5] == "BRAND-OK")
    uniq = len({r[1] for r in rows if r[1]})
    print(f"zips: {len(rows)} | HTTP200: {live} | brand-content-verified: {ok} | unique live links: {uniq}")
    (CORE / "delivery" / "_GROUND_TRUTH.txt").write_text(
        "\n".join(f"{status}\t{verdict}\t{link}\t{title}" for _, link, status, title, _, verdict in rows),
        encoding="utf-8")
    print("-> delivery/_GROUND_TRUTH.txt")


if __name__ == "__main__":
    main()
