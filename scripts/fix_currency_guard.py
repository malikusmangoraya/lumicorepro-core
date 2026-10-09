"""Apply the same CurrencyContext guard to every ported project."""
import pathlib

OLD = """      return localStorage.getItem('lumi-currency') || 'USD';"""
NEW = """      // A previous version stored a whole currency object here, so the stored
      // value is not trusted to be a bare ISO code.
      const raw = localStorage.getItem('lumi-currency');
      if (!raw) return 'USD';
      let value = raw;
      try { value = JSON.parse(raw); } catch (e) { /* plain string */ }
      const code = typeof value === 'string' ? value : value && value.code;
      if (typeof code === 'string' && CURRENCIES.includes(code.toUpperCase())) {
        return code.toUpperCase();
      }
      return 'USD';"""

for slug in ("maison-noir", "ledgerline", "kinetiq-health", "kestrel-fleet"):
    p = pathlib.Path(r"D:\lumicorepro-core\delivery") / slug / "frontend" / "src" / "context" / "CurrencyContext.jsx"
    if not p.is_file():
        print(f"{slug}: no CurrencyContext")
        continue
    t = p.read_text(encoding="utf-8")
    if "CURRENCIES.includes" in t:
        print(f"{slug}: already guarded")
        continue
    if OLD not in t:
        print(f"{slug}: pattern not found")
        continue
    p.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print(f"{slug}: guarded")
