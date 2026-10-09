"""Give the Checkout page its missing main landmark.

The page rendered its heading and form outside any `<main>`, so screen-reader
users had no main region to jump to and the landmark audit failed. Also drops
the unused `useTranslation` binding warning path by keeping the existing call.
"""
import pathlib

OLD_OPEN = '<div className="min-h-screen bg-[var(--t-canvas)] text-[var(--t-text)] py-12 px-4">'
NEW_OPEN = '<main id="main-content" className="min-h-screen bg-[var(--t-canvas)] text-[var(--t-text)] py-12 px-4">'

for slug in ("kestrel-fleet", "maison-noir", "ledgerline", "kinetiq-health"):
    p = pathlib.Path(r"D:\lumicorepro-core\delivery") / slug / "frontend" / "src" / "pages" / "Checkout.jsx"
    if not p.is_file():
        print(f"{slug}: no Checkout.jsx")
        continue
    t = p.read_text(encoding="utf-8")
    if 'id="main-content"' in t:
        print(f"{slug}: already has main")
        continue
    if OLD_OPEN not in t:
        # fall back to opening the first div on the return line
        t2 = t.replace("<div className=\"min-h-screen", "<main id=\"main-content\" className=\"min-h-screen", 1)
        if t2 == t:
            print(f"{slug}: pattern not found")
            continue
        t = t2
    else:
        t = t.replace(OLD_OPEN, NEW_OPEN, 1)
    # close the matching tag: the last </div> before </div> of the wrapper
    lines = t.splitlines(keepends=True)
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == "</div>":
            lines[i] = lines[i].replace("</div>", "</main>", 1)
            break
    p.write_text("".join(lines), encoding="utf-8")
    print(f"{slug}: main landmark added")
