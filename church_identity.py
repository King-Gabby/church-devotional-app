"""
utils/church_identity.py
Church Identity system — controlled branding personalisation.

Stores state in st.session_state and persists to JSON.
Designed for future migration to Supabase / SQLite without interface changes.

Public API:
    load_identity()          → loads from JSON into session_state
    save_identity()          → persists session_state to JSON
    get_identity()           → returns current identity dict
    ACCENT_THEMES            → dict of preset theme tokens
"""

import json
import os
import streamlit as st

_IDENTITY_FILE = "church_identity.json"

# ── Curated accent presets only — no arbitrary hex input ─────
ACCENT_THEMES: dict[str, dict] = {
    "Gold Ember": {
        "gold":        "#c8922a",
        "gold_lt":     "#daa84a",
        "gold_dim":    "rgba(200,146,42,0.09)",
        "gold_border": "rgba(200,146,42,0.18)",
        "gold_hi":     "rgba(200,146,42,0.30)",
        "label":       "Gold Ember",
    },
    "Royal Indigo": {
        "gold":        "#7c6fc0",
        "gold_lt":     "#9d92d8",
        "gold_dim":    "rgba(124,111,192,0.10)",
        "gold_border": "rgba(124,111,192,0.20)",
        "gold_hi":     "rgba(124,111,192,0.32)",
        "label":       "Royal Indigo",
    },
    "Ivory Dawn": {
        "gold":        "#b8956a",
        "gold_lt":     "#d4b08a",
        "gold_dim":    "rgba(184,149,106,0.09)",
        "gold_border": "rgba(184,149,106,0.20)",
        "gold_hi":     "rgba(184,149,106,0.32)",
        "label":       "Ivory Dawn",
    },
    "Crimson Covenant": {
        "gold":        "#b05060",
        "gold_lt":     "#cc7080",
        "gold_dim":    "rgba(176,80,96,0.09)",
        "gold_border": "rgba(176,80,96,0.20)",
        "gold_hi":     "rgba(176,80,96,0.32)",
        "label":       "Crimson Covenant",
    },
    "Olive Sanctuary": {
        "gold":        "#7a9e6a",
        "gold_lt":     "#96bc86",
        "gold_dim":    "rgba(122,158,106,0.09)",
        "gold_border": "rgba(122,158,106,0.20)",
        "gold_hi":     "rgba(122,158,106,0.32)",
        "label":       "Olive Sanctuary",
    },
}

THEME_NAMES = list(ACCENT_THEMES.keys())

_IDENTITY_DEFAULTS = {
    "church_name":     "The Word",
    "church_subtitle": "Daily Devotional",
    "accent_theme":    "Gold Ember",
    "logo_bytes":      None,   # raw bytes or None
}


def load_identity() -> None:
    """Load persisted identity from JSON into session_state (once per session)."""
    if st.session_state.get("_identity_loaded"):
        return
    data = {}
    if os.path.exists(_IDENTITY_FILE):
        try:
            with open(_IDENTITY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    for key, default in _IDENTITY_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = data.get(key, default)
    st.session_state["_identity_loaded"] = True


def save_identity() -> None:
    """Persist current identity session_state to JSON."""
    payload = {
        k: st.session_state.get(k, v)
        for k, v in _IDENTITY_DEFAULTS.items()
        if k != "logo_bytes"   # bytes not JSON-serialisable
    }
    with open(_IDENTITY_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def get_identity() -> dict:
    """Return the current church identity as a plain dict."""
    return {k: st.session_state.get(k, v) for k, v in _IDENTITY_DEFAULTS.items()}


def get_accent_css(theme_name: str) -> str:
    """
    Return a <style> block that overrides the CSS accent variables
    for the chosen preset. Inlined into the page after the base CSS.
    """
    t = ACCENT_THEMES.get(theme_name, ACCENT_THEMES["Gold Ember"])
    return f"""
<style>
:root {{
  --gold:        {t['gold']};
  --gold-lt:     {t['gold_lt']};
  --gold-dim:    {t['gold_dim']};
  --gold-border: {t['gold_border']};
  --gold-hi:     {t['gold_hi']};
}}
</style>"""