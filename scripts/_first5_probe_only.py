#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""First 5 international brands -> OWN folder + OWN zip + OWN canonical repo.
Uses deploy_all_pages's OWN verified helpers (slugify, deploy, current_link)."""
import sys, urllib.request, urllib.error, re, zipfile
from pathlib import Path

CORE = Path(r"D:\lumicorepro-core")
sys.path.insert(0, str(CORE / "scripts"))
import deploy_all_pages as d

OWNER = "malikusmangoraya"
FIVE = ["atlas-mobility", "aurora-cloud", "aurelia-estates",
        "aurum-fitness", "ember-salt"]
BAD = ("example.com", "placeholder", "your-site", "yourdomain", "localhost",
       "<your-user>", "yourdomain.io", "your-site-slug", "example")


def slugify(brand: str) -> str:
    return d.slugify(brand)


def link(slug: str) -> str:
    return f"https://{OWNER}.github.io/{slug}"


def probe(url: str):
    try:
        return urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": "lumi"}), timeout=30).status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        return "ERR:" + type(e).__name__


for slug in FIVE:
    url = link(slug)
    status = probe(url)
    print(f"{status}  {url}")
    e = d.BRANDS.get(slug, {})
    print(f"   brand_key_present={slug in d.BRANDS} | name={e.get('name','?')} | "
          f"industry={e.get('industry','?')}")
