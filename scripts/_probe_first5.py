#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, sys, urllib.request, urllib.error
from pathlib import Path
sys.path.insert(0, r"D:\lumicorepro-core\scripts")
import deploy_all_pages as d
FIRST5 = ["atlas-mobility", "aurora-cloud", "aurelia-estates",
          "aurum-fitness", "ember-salt"]
OWNER = "malikusmangoraya"
for slug in FIRST5:
    if slug not in d.BRANDS:
        print("SKIP missing key:", slug)
        continue
    repo = d.slugify(d.BRANDS[slug]["name"])
    link = f"https://{OWNER}.github.io/{repo}"
    code = "?"
    try:
        code = urllib.request.urlopen(
            urllib.request.Request(link, headers={"User-Agent": "lumi"}), timeout=30).status
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception as e:
        code = "ERR"
    print(f"{str(code):>5}  {link}  ({slug})")
