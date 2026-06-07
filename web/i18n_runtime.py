"""Runtime i18n: load the .mo catalog for the active language and return
it as a {msgid: msgstr} dict for embedding in the HTML page.

This avoids an extra HTTP request and makes translations available
synchronously before any user-facing JS runs.
"""
from __future__ import annotations

import os
from typing import Optional

# Lazy-loaded catalog cache: (locale, domain) -> {msgid: msgstr}
_CATALOG_CACHE: dict[tuple, dict[str, str]] = {}


def _load_catalog(locale: str, domain: str = "messages") -> dict[str, str]:
    """Read a compiled .mo file and return a flat msgid -> msgstr dict.

    Falls back to an empty dict if the .mo doesn't exist (so dev mode
    without compiled translations still works — strings just show in English).
    """
    cache_key = (locale, domain)
    if cache_key in _CATALOG_CACHE:
        return _CATALOG_CACHE[cache_key]

    base = os.path.join(os.path.dirname(__file__), "translations")
    mo_path = os.path.join(base, locale, "LC_MESSAGES", f"{domain}.mo")
    if not os.path.isfile(mo_path):
        _CATALOG_CACHE[cache_key] = {}
        return {}

    try:
        from babel.messages.mofile import read_mo
        with open(mo_path, "rb") as f:
            catalog = read_mo(f)
        out = {}
        for m in catalog:
            if m.id:  # skip empty header
                out[m.id] = m.string or m.id
        _CATALOG_CACHE[cache_key] = out
        return out
    except Exception:
        _CATALOG_CACHE[cache_key] = {}
        return {}


def get_runtime_catalog(locale: Optional[str] = None) -> dict[str, str]:
    """Return the active locale's translation catalog for the browser.

    Args:
        locale: the active language code (e.g. 'en', 'id'). If None or
            'en', returns an empty dict (English is the source, so no
            mapping needed — JS falls back to msgid).
    """
    if not locale or locale == "en":
        return {}
    return _load_catalog(locale)
