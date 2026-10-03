"""Phase 2: add Stripe SDK, checkout/admin routes, fix placeholders."""
import json, re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "generated-projects"

def _read(p):
    return p.read_text(encoding="utf-8", errors="ignore")

def _write(p, content):
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists() and p.read_text(encoding="utf-8", errors="ignore") == content:
        return False
    p.write_text(content, encoding="utf-8")
    return True

def patch_project(slug):
    fp = GEN / slug / "frontend"
    if not (fp / "src" / "main.jsx").exists():
        return [f"{slug}: skipped (no main.jsx)"]
    src = fp / "src"
    msgs = []
    changed = False

    # A: stripe SDK
    pkg = fp / "package.json"
    if pkg.exists():
        try:
            p = json.loads(_read(pkg))
            deps = p.get("dependencies", {})
            if "@stripe/stripe-js" not in deps:
                deps["@stripe/stripe-js"] = "^2.4.0"
                p["dependencies"] = deps
                _write(pkg, json.dumps(p, indent=2, ensure_ascii=False) + "\n")
                msgs.append(f"{slug}: added @stripe/stripe-js")
                changed = True
        except Exception:
            pass

    # B: scaffold Checkout + Admin pages
    pages = src / "pages"
    pages.mkdir(parents=True, exist_ok=True)
    for name, title in [("Checkout", "Checkout"), ("Admin", "Admin")]:
        p = pages / f"{name}.jsx"
        if not p.exists():
            p.write_text(f"""import React from 'react';
import {{ useTranslation }} from 'react-i18next';
import CheckoutFlow from '@/components/checkout/CheckoutFlow';
import {{ useCurrency }} from '@/context/CurrencyContext';

export default function {name}() {{
  const {{ t }} = useTranslation();
  const {{ currency }} = useCurrency();
  return (
    <div className="min-h-screen bg-[var(--t-canvas)] text-[var(--t-text)] py-12 px-4">
      <h1 className="text-3xl font-bold mb-8">{title}</h1>
      {('<CheckoutFlow currency={{currency}} submitEndpoint="/api/orders" />' if name=='Checkout' else '<div className="grid grid-cols-1 md:grid-cols-3 gap-6"><div className="bg-[var(--t-surface)] rounded-xl p-6">Orders</div><div className="bg-[var(--t-surface)] rounded-xl p-6">Users</div><div className="bg-[var(--t-surface)] rounded-xl p-6">Analytics</div></div>')}
    </div>
  );
}}
""", encoding="utf-8")
            msgs.append(f"{slug}: scaffolded pages/{name}.jsx")
            changed = True

    # C: patch App.jsx — imports + routes
    app = src / "App.jsx"
    if app.exists():
        txt = _read(app)
        a = txt
        # add lazy imports
        if 'const Checkout = lazy' not in txt:
            idx = txt.find('const Home = lazy')
            if idx != -1:
                end = txt.find('\n', txt.find('))', idx))
                if end != -1:
                    txt = txt[:end+1] + 'const Checkout = lazy(() => import("./pages/Checkout"));\n' + txt[end+1:]
        if 'const Admin = lazy' not in txt:
            idx = txt.find('const Home = lazy')
            if idx != -1:
                end = txt.find('\n', txt.find('))', idx))
                if end != -1:
                    txt = txt[:end+1] + 'const Admin = lazy(() => import("./pages/Admin"));\n' + txt[end+1:]
        # add routes before the * route
        star_route = '<Route path="*" element={<Home />} />'
        if star_route in txt and ('path="/checkout"' not in txt or 'path="/admin"' not in txt):
            new_routes = ''
            if 'path="/checkout"' not in txt:
                new_routes += '<Route path="/checkout" element={<Checkout />} />\n            '
            if 'path="/admin"' not in txt:
                new_routes += '<Route path="/admin" element={<Admin />} />\n            '
            txt = txt.replace(star_route, new_routes + star_route, 1)
        if txt != a:
            _write(app, txt)
            msgs.append(f"{slug}: patched App.jsx routes")
            changed = True

    # D: fix placeholders
    for comp in ["Contact.jsx", "Login.jsx", "Register.jsx"]:
        p = src / "components" / comp
        if not p.exists():
            p = src / "pages" / comp
        if not p.exists():
            continue
        t = _read(p)
        if 'placeholder="' in t or "placeholder='" in t:
            t = re.sub(r'placeholder="[^"]*"', 'placeholder="Enter your full name"', t)
            t = re.sub(r"placeholder='[^']*'", "placeholder='Enter your full name'", t)
            _write(p, t)
            msgs.append(f"{slug}: fixed placeholder in {comp}")
            changed = True
    return msgs, changed

def build_changed(changed):
    print(f"\ntouched {len(changed)} projects; rebuilding…")
    for slug in sorted(changed):
        fe = GEN / slug / "frontend"
        if not (fe / "package.json").exists():
            continue
        r = subprocess.run(
            "npm.cmd run build",
            cwd=str(fe),
            shell=True,
            capture_output=True, text=True,
            timeout=180,
        )
        print(f"  {slug}: {'OK' if r.returncode == 0 else 'FAILED'}")
        if r.returncode != 0:
            print("    " + r.stderr[-1000:].replace("\n", "\n    "))

def main():
    changed = set()
    for proj in sorted(GEN.iterdir()):
        fe = proj / "frontend"
        if not (fe / "src" / "main.jsx").exists():
            continue
        msgs, ch = patch_project(proj.name)
        if ch:
            changed.add(proj.name)
        for m in msgs:
            print(m)
    build_changed(sorted(changed))

if __name__ == "__main__":
    main()
