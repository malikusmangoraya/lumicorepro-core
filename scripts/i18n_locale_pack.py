#!/usr/bin/env python3
"""Repo-side access to the agent's translation pack.

The pack itself lives in `ai-agent/agent/i18n_pack.py`, because the generator is
its primary owner and `ai-agent/` must stay self-contained for buyers who run
the agent on its own. This module only re-exports it so repo tooling
(`i18n_fill_locales.py`, `audit_products.py`) and the generator can never drift
apart: there is exactly one table of translations in the repository.

    from i18n_locale_pack import TRANSLATIONS, needs_translation
"""

from __future__ import annotations

import pathlib
import sys

_AGENT_DIR = pathlib.Path(__file__).resolve().parent.parent / "ai-agent"
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

from agent.i18n_pack import (  # noqa: E402,F401  (re-exported on purpose)
    LOCALES,
    NON_TRANSLATABLE,
    SAME_AS_ENGLISH,
    TOTAL_STRINGS,
    TRANSLATIONS,
    has_locale,
    is_correct_as_english,
    is_untranslatable,
    needs_translation,
    translate,
)

__all__ = [
    "LOCALES",
    "NON_TRANSLATABLE",
    "SAME_AS_ENGLISH",
    "TOTAL_STRINGS",
    "TRANSLATIONS",
    "has_locale",
    "is_correct_as_english",
    "is_untranslatable",
    "needs_translation",
    "translate",
]


if __name__ == "__main__":  # pragma: no cover - convenience probe
    print(f"translation pack: {TOTAL_STRINGS} strings x {len(LOCALES)} locales")
    print("locales:", ", ".join(LOCALES))
