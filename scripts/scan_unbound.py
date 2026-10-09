"""Find identifiers used in JSX that are never imported or declared.

`<p>{BRAND}</p>` compiles cleanly and only throws at render time, so a build
cannot catch it. Scan every JSX expression for capitalised identifiers and
report the ones with no binding in the file.
"""
import pathlib
import re
import sys

DEL = pathlib.Path(r"D:\lumicorepro-core\delivery")
TARGETS = ["kestrel-fleet", "maison-noir", "ledgerline", "kinetiq-health"]

# globals / built-ins that legitimately have no import
ALLOWED = {
    "React", "Math", "JSON", "Object", "Array", "String", "Number", "Boolean",
    "Date", "Promise", "Error", "Map", "Set", "URL", "URLSearchParams",
    "Intl", "console", "window", "document", "localStorage", "navigator",
    "location", "history", "fetch", "setTimeout", "clearTimeout", "NaN",
    "Infinity", "undefined", "true", "false", "null",
}

IDENT = re.compile(r"\{([^{}]*)\}", re.S)
WORD = re.compile(r"\b([A-Z][A-Za-z0-9_]*)\b")
DECL = re.compile(r"\b(?:const|let|var|function|class)\s+([A-Za-z0-9_]+)")

total = 0
for slug in TARGETS:
    src = DEL / slug / "frontend" / "src"
    problems = []
    for f in sorted(src.rglob("*.jsx")) + sorted(src.rglob("*.js")):
        t = f.read_text(encoding="utf-8", errors="ignore")
        bound = set(WORD.findall("".join(re.findall(r"import\s+(?:[\w*{}\s,]+\s+from\s+)?['\"][^'\"]+['\"]", t))))
        bound |= set(DECL.findall(t))
        for m in re.finditer(r"import\s+([^;]+?)\s+from\s+['\"]", t):
            bound |= set(re.findall(r"[A-Za-z0-9_]+", m.group(1)))
        # destructured / map params
        bound |= set(re.findall(r"\(\s*([A-Z][A-Za-z0-9_]*)\s*\)\s*=>", t))
        bound |= set(re.findall(r"([A-Z][A-Za-z0-9_]*)\s*=>", t))
        bound |= set(re.findall(r"\{\s*([A-Z][A-Za-z0-9_]*)\s*\}", t))
        bound |= set(re.findall(r"\{\s*([A-Z][A-Za-z0-9_]*)\s*,", t))
        for expr in IDENT.findall(t):
            if "<" in expr or "(" in expr and "=>" not in expr and "function" not in expr:
                # keep simple expressions only
                if not re.fullmatch(r"[A-Za-z0-9_$.\s'\"()+\-*/%?:!<>=|&[\]]*", expr):
                    continue
            # drop string literals and JSX text, then look at what is left
            bare = re.sub(r"'[^']*'", "''", expr)
            bare = re.sub(r'"[^"]*"', '""', bare)
            bare = re.sub(r">[^<]*<", "", bare)   # JSX text between tags
            for name in WORD.findall(bare):
                if name in ALLOWED or name in bound:
                    continue
                problems.append((f.relative_to(src), name))
    uniq = sorted(set(problems))
    print(f"{slug}: {len(uniq)} unbound identifier(s)")
    for path, name in uniq[:25]:
        print(f"    {name:<22} {path}")
    total += len(uniq)

print(f"\ntotal unbound: {total}")
