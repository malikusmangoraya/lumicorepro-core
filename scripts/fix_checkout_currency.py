"""Fix the Checkout page passing currency as an object.

`<CheckoutFlow currency={{currency}} />` handed the component
`{ currency: 'USD' }`, so `Intl.NumberFormat({ currency: { currency: 'USD' } })`
threw `Invalid currency code : [object Object]` and the checkout page never
rendered. CheckoutFlow expects a plain ISO code.
"""
import pathlib
import re

DEL = pathlib.Path(r"D:\lumicorepro-core\delivery")

for slug in ("kestrel-fleet", "maison-noir", "ledgerline", "kinetiq-health"):
    p = DEL / slug / "frontend" / "src" / "pages" / "Checkout.jsx"
    if not p.is_file():
        print(f"{slug}: no Checkout.jsx")
        continue
    t = p.read_text(encoding="utf-8")
    if "currency={{currency}}" not in t:
        print(f"{slug}: already correct")
        continue
    t = t.replace("currency={{currency}}", "currency={currency}")
    p.write_text(t, encoding="utf-8")
    print(f"{slug}: currency prop fixed")
