"""
Design Vault — turn real design assets into agent-native design systems.

The vault lives at <repo>/registry/design-vault/<source>/. Each source folder
is a legally-obtained design asset pack (e.g. a HorizonX UI kit the user
downloaded under their subscription, or an in-house Figma export):

    registry/design-vault/horizonx/
        style-tokens.json      # optional hand-curated tokens (most accurate)
        any-page.html ...      # self-contained HTML → auto-extracted tokens

The module scans the vault, extracts the design language
(colors → palette, fonts, radii/shadows → CSS), and registers each source as
a usable `ui_style` — so `restyle_project(project, name, 'horizonx')` applies
that exact design system to generated projects.

No copyrighted source file leaves the user's machine: only the extracted
design tokens (colors/fonts/primitives) are registered in the agent.
"""
from pathlib import Path
import json
import re
from typing import Dict, Any

from utils.logger import agent_logger

# ── Locate the repo registry no matter where this module is imported from ──
_ROOT = Path(__file__).resolve().parent.parent.parent
VAULT_DIR = _ROOT / 'registry' / 'design-vault'
MANIFEST = _ROOT / 'registry' / 'design-vault-manifest.json'


def _hex_freq(text: str) -> list:
    """Count #hex occurrences in CSS/style text; return sorted (color, count)."""
    counts: Dict[str, int] = {}
    for m in re.finditer(r'#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b', text):
        h = m.group(0).lower()
        counts[h] = counts.get(h, 0) + 1
    return sorted(counts.items(), key=lambda x: -x[1])


def _is_gray(h: str) -> bool:
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    if len(h) != 6:
        return True
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return max(r, g, b) - min(r, g, b) < 28


def _darkest_non_gray(text_hex: list) -> str:
    """Pick the darkest non-gray hex as the heading color."""
    best = None
    for h, _ in text_hex:
        if _is_gray(h):
            continue
        if best is None:
            best = h
            continue
        # compare relative luminance (simple sum)
        hh = h.lstrip('#')
        hsum = sum(int(hh[i:i + 2], 16) for i in (0, 2, 4))
        bsum = sum(int(best.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
        if hsum < bsum:
            best = h
    return best or '#0f172a'


def _extract_fonts(html: str) -> Dict[str, str]:
    """Best-effort font family extraction (Google font first, then any family)."""
    fonts = {}
    gf = re.search(
        r'fonts\.googleapis\.com/css2\?family=([^&"\']+)', html
    )
    if gf:
        fam = gf.group(1).replace('+', ' ')
        fonts['display'] = fam.split(':')[0].replace(',', ', ')
    fams = re.findall(r"font-family\s*:\s*['\"]([^'\";]+)['\"]", html)
    fams += re.findall(r"font-family:\s*([^;}\n]+)", html)
    for f in fams:
        f = f.strip().strip('"').strip("'")
        if f and f.lower() not in ('inherit', 'sans-serif'):
            fonts.setdefault('sans', f.split(',')[0].strip())
    return fonts


def _extract_primitives(html: str) -> str:
    """Pull recurring radii/shadows as a reusable .card-panel CSS snippet."""
    radii = re.findall(r'border-radius:\s*([0-9.]+r?em|[\d.]+px)', html)
    shadows = re.findall(r'box-shadow:\s*([^;}\n]+)', html)
    r = ''
    if radii:
        top = max({x for x in radii}, key=radii.count)
        r += f'  .card-panel {{ border-radius: {top}; }}\n'
    if shadows:
        top = max({x for x in shadows}, key=shadows.count)
        r += f'  .card-panel {{ box-shadow: {top.strip()}; }}\n'
    return r


def _tokens_from_html(source: Path, html: str) -> Dict[str, Any]:
    text_hex = _hex_freq(html)
    if not text_hex:
        return {}
    colored = [h for h, _ in text_hex if not _is_gray(h)]
    primary = colored[0] if len(colored) > 0 else '#6366f1'
    accent = colored[1] if len(colored) > 1 else '#f59e0b'
    heading = _darkest_non_gray(text_hex)
    body_bg = next((h for h, _ in text_hex if h == '#ffffff'), '#f8fafc')
    fonts = _extract_fonts(html)
    return {
        'palette': {
            'primary': primary,
            'accent': accent,
            'heading': heading,
            'navBg': body_bg,
            'footerBg': heading,
        },
        'fonts': fonts,
        'css_extra': _extract_primitives(html),
        'source': str(source),
    }


def scan_vault() -> Dict[str, Dict[str, Any]]:
    """Register every design-vault source as a usable ui_style."""
    vault_styles: Dict[str, Dict[str, Any]] = {}
    if not VAULT_DIR.exists():
        return vault_styles
    for source in sorted(VAULT_DIR.iterdir()):
        if not source.is_dir() or source.name.startswith('.'):
            continue
        style_name = source.name
        tokens_file = source / 'style-tokens.json'
        htmls = list(source.glob('*.html')) + list(source.glob('*.htm'))
        tokens: Dict[str, Any] = {}

        if tokens_file.exists():
            try:
                data = json.loads(tokens_file.read_text(encoding='utf-8'))
                tokens = data.get('tokens') or data
            except Exception as e:
                agent_logger.warning(f"Design vault {style_name}: bad tokens.json {e}")
        elif htmls:
            for hfile in htmls:
                try:
                    tokens = _tokens_from_html(source, hfile.read_text(encoding='utf-8'))
                except Exception:
                    continue
                if tokens:
                    tokens['tokens_from'] = hfile.name
                    break

        if not tokens:
            agent_logger.warning(f"Design vault {style_name}: no extractable design")
            continue
        vault_styles[style_name] = {
            'palette': tokens.get('palette', {}),
            'fonts': tokens.get('fonts', {}),
            'css_extra': tokens.get('css_extra', ''),
            'source': tokens.get('source', str(source)),
        }
    return vault_styles


def write_manifest() -> Dict[str, Any]:
    """Persist the registered vault styles for the generation report."""
    vault = scan_vault()
    manifest = {
        'description': 'Design Vault — legally-obtained design assets registered '
                       'as agent-native ui_styles. Only extracted tokens are stored.',
        'sources': list(vault.keys()),
        'detail': vault,
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest


# Module-level cache so restyle_project can read it without re-scanning
VAULT_STYLES: Dict[str, Dict[str, Any]] = scan_vault()


def refresh() -> Dict[str, Any]:
    global VAULT_STYLES
    VAULT_STYLES = scan_vault()
    return write_manifest()