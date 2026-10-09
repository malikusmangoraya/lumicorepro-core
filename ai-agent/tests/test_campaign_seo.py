"""Regression tests for the campaign SEO identity contract.

Every deployed campaign site shipped with the same three defects:

  1. og:image pointed at a truncated repo slug  -> 404
  2. twitter:image pointed at an invented <brand>.com domain -> 404
  3. JSON-LD @id/url/logo used that invented domain, contradicting
     og:url/canonical so the entity had no resolvable identity

The first version of the JSON-LD fix substituted only scheme+host, which made
it non-idempotent: a second run turned /ember-salt/#website into
/ember-salt/ember-salt/#website. These tests pin the repaired behaviour so it
cannot regress.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import fix_campaign_seo as fcs  # noqa: E402
import international_pass1_global as ipg  # noqa: E402

BASE = "https://malikusmangoraya.github.io/ember-salt"

BROKEN = """<!doctype html>
<html lang="en">
  <head>
    <title>Ember &amp; Salt &#8212; Fire, salt, and honest cooking.</title>
    <link rel="canonical" href="https://ember-salt.com/" />
    <meta property="og:url" content="https://malikusmangoraya.github.io/ember" />
    <meta property="og:image" content="https://malikusmangoraya.github.io/ember/og-image.svg" />
    <meta property="og:locale" content="en_US" />
    <meta name="twitter:image" content="https://ember-salt.com/og-image.svg" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400" rel="stylesheet" />
    <link rel="icon" type="image/svg+xml" href="./favicon.svg" />
    <script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    { "@type": "Organization", "@id": "https://ember-salt.com/#organization",
      "url": "https://ember-salt.com/",
      "logo": { "@type": "ImageObject", "url": "https://ember-salt.com/logo.svg" } },
    { "@type": "WebSite", "@id": "https://ember-salt.com/#website",
      "url": "https://ember-salt.com/" }
  ]
}
    </script>
  </head>
  <body><div id="root"></div></body>
</html>
"""


@pytest.fixture
def repaired(tmp_path, monkeypatch):
    """patch_seo() applied to a throwaway project, returned as HTML text."""
    frontend = tmp_path / "ember-salt" / "frontend"
    frontend.mkdir(parents=True)
    index = frontend / "index.html"
    index.write_text(BROKEN, encoding="utf-8")
    monkeypatch.setattr(ipg, "PROJECTS", tmp_path)
    ipg.patch_seo("ember-salt", BASE, ["en", "ar"])
    return index.read_text(encoding="utf-8")


# ---------------------------------------------------------------- the defects


def test_og_image_points_at_real_repo(repaired):
    assert f'<meta property="og:image" content="{BASE}/og-image.svg"' in repaired


def test_twitter_image_points_at_real_repo(repaired):
    assert f'<meta name="twitter:image" content="{BASE}/og-image.svg"' in repaired


def test_canonical_points_at_real_repo(repaired):
    assert f'href="{BASE}/"' in repaired


def test_jsonld_ids_are_resolvable(repaired):
    assert f'"@id": "{BASE}/#organization"' in repaired
    assert f'"@id": "{BASE}/#website"' in repaired
    assert f'"url": "{BASE}/logo.svg"' in repaired


def test_invented_brand_domain_is_gone(repaired):
    assert "ember-salt.com" not in repaired


def test_truncated_slug_is_gone(repaired):
    assert "github.io/ember/og-image" not in repaired


# -------------------------------------------------------------- preservation


def test_third_party_urls_survive(repaired):
    assert "https://fonts.googleapis.com/css2?family=Poppins" in repaired
    assert '"@context": "https://schema.org"' in repaired


def test_favicon_reference_survives(repaired):
    assert "./favicon.svg" in repaired


def test_utf8_content_is_not_mangled(repaired):
    assert "&#8212;" in repaired


# -------------------------------------------------------------- idempotency


def test_repeated_passes_converge(repaired):
    once = ipg.rewrite_seo_html(repaired, BASE, ["en", "ar"])
    twice = ipg.rewrite_seo_html(once, BASE, ["en", "ar"])
    assert once == twice


def test_path_does_not_grow_per_pass(repaired):
    out = repaired
    for _ in range(3):
        out = ipg.rewrite_seo_html(out, BASE, ["en", "ar"])
    assert "/ember-salt/ember-salt/" not in out


def test_hreflang_block_is_not_duplicated(repaired):
    out = repaired
    for _ in range(3):
        out = ipg.rewrite_seo_html(out, BASE, ["en", "ar"])
    assert out.count("LUMI-HREFLANG-START") == 1


def test_document_does_not_grow_per_pass(repaired):
    """Stripping and re-injecting the hreflang block must not accumulate
    whitespace, or every deploy would add a blank line forever."""
    lengths = set()
    out = repaired
    for _ in range(4):
        lengths.add(len(out))
        out = ipg.rewrite_seo_html(out, BASE, ["en", "ar"])
    assert len(lengths) == 1


def test_inline_script_urls_are_untouched():
    """The JSON-LD rewrite is scoped to ld+json; a page's own module scripts
    may legitimately reference third-party endpoints."""
    html = (
        "<!doctype html><html><head><title>t</title>\n"
        '<link rel="canonical" href="https://ember-salt.com/" />\n'
        '<script type="application/ld+json">\n'
        '{ "@id": "https://ember-salt.com/#organization",'
        ' "url": "https://ember-salt.com/logo.svg" }\n'
        "</script>\n"
        "<script type=\"module\">\n"
        '  const stripe = { url: "https://api.stripe.com/v1" };\n'
        '  const ga = { url: "https://www.google-analytics.com/" };\n'
        "</script>\n"
        "</head><body></body></html>"
    )
    out = ipg.rewrite_seo_html(html, BASE, ["en"])
    assert f'"@id": "{BASE}/#organization"' in out
    assert f'"url": "{BASE}/logo.svg"' in out
    assert "https://api.stripe.com/v1" in out
    assert "https://www.google-analytics.com/" in out


def test_jsonld_rewrite_does_not_escape_into_inline_scripts():
    html = (
        "<!doctype html><html><head><title>t</title>\n"
        '<script type="application/ld+json">\n'
        '{ "@id": "https://ember-salt.com/#organization" }\n'
        "</script>\n"
        '<script>window.cfg = { "url": "https://ember-salt.com/legacy" };</script>\n'
        "</head><body></body></html>"
    )
    out = ipg.rewrite_seo_html(html, BASE, ["en"])
    assert "https://ember-salt.com/legacy" in out


# ------------------------------------------------- the auditor itself is sane


def test_auditor_reports_the_known_defects():
    problems = fcs.seo_problems(BROKEN, BASE)
    joined = "\n".join(problems)
    assert "og:image" in joined
    assert "twitter:image" in joined
    assert "#organization" in joined


def test_auditor_is_quiet_on_repaired_html(repaired):
    assert fcs.seo_problems(repaired, BASE) == []


@pytest.fixture
def shipped_html():
    """BROKEN but with metadata already pointing at the real Pages URL, so
    these asset tests exercise file presence only, not the rewriter."""
    return BROKEN.replace(
        "https://malikusmangoraya.github.io/ember/og-image.svg",
        f"{BASE}/og-image.svg",
    ).replace(
        'content="https://ember-salt.com/og-image.svg"',
        f'content="{BASE}/og-image.svg"',
    )


def test_missing_asset_is_detected(tmp_path, shipped_html):
    root = tmp_path / "ember-salt"
    root.mkdir()
    index = root / "index.html"
    index.write_text(shipped_html, encoding="utf-8")
    missing = fcs.missing_assets(index, BASE)
    assert any("og-image.svg" in problem for problem in missing)


def test_present_asset_is_not_reported(tmp_path, shipped_html):
    root = tmp_path / "ember-salt"
    root.mkdir()
    index = root / "index.html"
    index.write_text(shipped_html, encoding="utf-8")
    for name in ("og-image.svg", "favicon.svg"):
        (root / name).write_text("<svg/>", encoding="utf-8")
    assert fcs.missing_assets(index, BASE) == []


def test_vite_public_dir_counts_as_served_root(tmp_path, shipped_html):
    """frontend/index.html resolves static files from frontend/public/."""
    frontend = tmp_path / "ember-salt" / "frontend"
    public = frontend / "public"
    public.mkdir(parents=True)
    index = frontend / "index.html"
    index.write_text(shipped_html, encoding="utf-8")
    for name in ("og-image.svg", "favicon.svg"):
        (public / name).write_text("<svg/>", encoding="utf-8")
    assert fcs.missing_assets(index, BASE) == []


def test_every_campaign_has_a_pages_url():
    for slug in fcs.CAMPAIGNS:
        assert fcs.base_url(slug) == (
            f"https://{fcs.OWNER}.github.io/{slug}"
        )


def test_campaign_list_matches_generator():
    """The repair tool and the generator must not drift apart on scope."""
    generated = {p.name for p in ipg.PROJECTS.glob("*") if p.is_dir()}
    missing = set(fcs.CAMPAIGNS) - generated
    assert not missing, f"campaigns with no generated project: {sorted(missing)}"