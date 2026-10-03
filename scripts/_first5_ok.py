#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""First5 international REBUILD via deployer's own BRANDS+deploy."""
import sys
from pathlib import Path
sys.path.insert(0, r"D:\lumicorepro-core\scripts")
import deploy_all_pages as d

FIVE = [k for k in sorted(d.BRANDS)
        if not k.startswith(("build", "generated", "generated-website",
                              "electronics", "tourism", "personal",
                              "food", "resupro", "ui-style", "rest",
                              "style", "electron", "bloom"))][:5]
print("first_five_keys:", FIVE)

for slug in FIVE:
    try:
        link = d.current_link(Path(d.BRANDS[slug])) if isinstance(d.BRANDS[slug], str) else "?"
        print("canonical:", slug, "->", link)
    except Exception as e:
        print("ERR", slug, type(e).__name__, str(e)[:80])
print("SCRIPT_OK")
