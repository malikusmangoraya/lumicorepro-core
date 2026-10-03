"""React Emit - stage 3 of the component graph.

Asks a model for the JSX, then validates the answer before anyone is allowed to
write it to disk. A model that returns prose, a fenced block with a trailing
comment, or markup with raw hex colours is a normal outcome, not an edge case, so
the checks here are the difference between a usable component and a broken build.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence

MAX_COMPONENT_LINES = 400
# A line cap alone is not a size cap: a minified one-line component passes it while
# still being unreadable and unreviewable, so length is checked too.
MAX_COMPONENT_CHARS = 20000

_FENCE_BLOCK = re.compile(r"```(?:jsx|tsx|javascript|js|react)?[ \t]*\r?\n(.*?)```", re.S | re.I)
_RAW_HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
_H1_COUNT = re.compile(r"<h1\b", re.I)
_IMPORT_FROM = re.compile(r"""^\s*import\s+.*?\s+from\s+['"]([^'"]+)['"]""", re.M)
_EXPORT_DEFAULT = re.compile(r"export\s+default\s+", re.I)


def strip_code_fence(text: str) -> str:
    """Pull the code out of a markdown fence, if there is one."""
    if not text:
        return ""
    match = _FENCE_BLOCK.search(text)
    return (match.group(1) if match else text).strip()


def validate_component(code: str, allowed_tokens: Sequence[str] = ()) -> List[str]:
    """Return a list of problems. Empty list means the component is shippable."""
    problems: List[str] = []
    if not code or not code.strip():
        return ["empty output"]
    if "```" in code:
        problems.append("unclosed markdown fence in output")
    if not _EXPORT_DEFAULT.search(code):
        problems.append("missing `export default`")
    if not _H1_COUNT.search(code):
        problems.append("missing h1 (page-level component needs exactly one)")
    elif len(_H1_COUNT.findall(code)) > 1:
        problems.append("more than one h1")
    if len(code.splitlines()) > MAX_COMPONENT_LINES:
        problems.append("component exceeds %d lines" % MAX_COMPONENT_LINES)
    if len(code) > MAX_COMPONENT_CHARS:
        problems.append("component exceeds %d characters" % MAX_COMPONENT_CHARS)

    raw_hex = _RAW_HEX.findall(code)
    if raw_hex:
        problems.append("raw hex colour(s) %s - use design tokens" % ", ".join(sorted(set(raw_hex))[:3]))

    if allowed_tokens:
        used = set(re.findall(r"var\(\s*(--[\w-]+)", code))
        unknown = sorted(t for t in used if t not in set(allowed_tokens))
        if unknown:
            problems.append("undeclared token(s) %s" % ", ".join(unknown[:3]))

    for mod in _IMPORT_FROM.findall(code):
        if mod.startswith("@/components/"):
            problems.append("import from '@/components/...' will not resolve in the consumer project (%s)" % mod)
    return problems


def humanize_component_name(name: str) -> str:
    """'PricingTable' -> 'Pricing table'. Produces real, readable copy."""
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", str(name or ""))
    text = re.sub(r"[_\-]+", " ", text).strip()
    if not text:
        return "Component"
    return text[:1].upper() + text[1:]


def region_label(tag: str, index: int) -> str:
    """Short human heading for a non-primary region.

    The layout brief's `job` field (e.g. 'identity + primary action') is an
    internal design note and must never be rendered as user-visible copy.
    """
    labels = {
        "header": "Header",
        "nav": "Sections",
        "hero": "Overview",
        "content": "Details",
        "footer": "Footer",
        "aside": "Related",
    }
    return labels.get(tag, f"Section {index}")


def fallback_component(name: str, region_spec: Sequence[Dict[str, Any]]) -> str:
    """Deterministic component used when no provider is available.

    It follows the same layout contract as the model path, so the graph always
    produces a valid React component and offline runs stay useful. Landmarks come
    from the element itself (`header`/`nav`/`main`/`aside`/`footer` already map to
    banner/navigation/main/complementary/contentinfo) rather than an aria-label, and
    the hero carries the single h1.
    """
    safe = re.sub(r"[^A-Za-z0-9]", "", name) or "GeneratedComponent"
    title = humanize_component_name(name)
    body: List[str] = []
    seen: Dict[str, int] = {}
    # A page-level component must expose exactly one h1. The hero normally carries
    # it, but layouts without a hero (form/single) still need one, so the first
    # surviving region is promoted.
    wants_h1 = not any(str(r.get("name")) == "hero" for r in region_spec)
    for region in region_spec:
        tag = str(region.get("name", "content"))
        if tag == "footer":
            el, cls = "footer", "py-10"
        elif tag == "header":
            el, cls = "header", "py-6"
        elif tag == "nav":
            el, cls = "nav", "py-3"
        elif tag == "hero":
            el, cls = "section", "py-16"
        elif tag == "aside":
            el, cls = "aside", "py-8"
        else:
            el, cls = "main", "py-12"
        seen[el] = seen.get(el, 0) + 1
        if seen[el] > 1:
            continue
        index = len(body) + 1
        if tag == "hero":
            heading, size, label = "h1", "text-3xl md:text-5xl font-semibold", title
            wants_h1 = False
        elif wants_h1:
            heading, size, label = "h1", "text-2xl font-semibold", title
            wants_h1 = False
        else:
            heading, size, label = "h2", "text-2xl font-semibold", region_label(tag, index)
        attrs = ' aria-label="Primary"' if tag == "nav" else ""
        body.append(
            '    <{el} className="{cls}"{attrs}>\n'
            '      <div className="mx-auto w-full max-w-6xl px-4">\n'
            '        <{heading} className="{size} text-[var(--t-text)]">{label}</{heading}>\n'
            "      </div>\n"
            "    </{el}>".format(el=el, cls=cls, attrs=attrs, heading=heading, size=size, label=label)
        )
    return (
        "import React from 'react';\n"
        "\n"
        "export default function {name}() {{\n"
        "  return (\n"
        '    <div className="min-h-screen bg-[var(--t-bg)] text-[var(--t-text)] font-[var(--t-font)]">\n'
        "{body}\n"
        "    </div>\n"
        "  );\n"
        "}}\n"
    ).format(name=safe, body="\n".join(body))


def emit_react_component(
    context_prompt: str,
    layout_prompt: str,
    component_name: str = "GeneratedComponent",
    region_spec: Sequence[Dict[str, Any]] = (),
    allowed_tokens: Sequence[str] = (),
    provider: Any = None,
) -> Dict[str, Any]:
    """Node 3. Returns the final component plus how it was produced."""
    if provider is None:
        code = fallback_component(component_name, region_spec)
        return {
            "code": code,
            "source": "fallback",
            "valid": not validate_component(code, allowed_tokens),
            "problems": validate_component(code, allowed_tokens),
        }

    prompt = "\n\n".join(
        [
            "You are a senior React engineer. Return ONLY the component source, no prose, no explanation.",
            "Output must be a single JSX file using function components and Tailwind utility classes.",
            context_prompt,
            layout_prompt,
            "Return exactly one file. Name the component %s and export it as default." % component_name,
        ]
    )

    raw: Optional[str] = None
    error = ""
    try:
        raw = provider.generate_code(prompt)
    except Exception as exc:  # provider failures must not break the graph
        error = str(exc)[:200]

    code = strip_code_fence(raw or "")
    problems = validate_component(code, allowed_tokens)
    if problems:
        # A model answer that fails validation is worse than the deterministic
        # one, so fall back instead of shipping markup that will not build.
        fallback = fallback_component(component_name, region_spec)
        return {
            "code": fallback,
            "source": "fallback",
            "valid": True,
            "problems": problems,
            "provider_error": error,
            "rejected_output": code[:800],
        }

    return {"code": code, "source": "provider", "valid": True, "problems": [], "provider_error": error}
