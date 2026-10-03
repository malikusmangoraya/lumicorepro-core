#!/usr/bin/env python3
# Rebuild FIRST 5 as international full-stack (own folder each), zip+link, deploy, probe.
import sys, re, zipfile, json
from pathlib import Path
sys.path.insert(0, r"D:\lumicorepro-core\scripts")

import importlib
dp = importlib.import_module("deploy_all_pages")

FIRST5 = ["atlas-mobility", "aurora-cloud", "aurelia-estates", "aurum-fitness", "ember-salt"]
OWNER = "malikusmangoraya"
BAD = ("example.com", "placeholder", "your-site", "yourdomain", "localhost", "<your-user>")

rows = []
for slug in FIRST5:
    link = f"https://{OWNER}.github.io/{slug}"
    rows.append((slug, link, "rebuild-pending"))

print(json.dumps(rows, indent=1))
