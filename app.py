"""
app.py — The Word  |  Church Devotional Platform
A sacred reading space. Calm. Intentional. Immersive.

Run:  streamlit run app.py
Env:  GEMINI_API_KEY  (in .env or Streamlit secrets)
"""

import time
import streamlit as st
from datetime import datetime

from verse_service import (
    fetch_verse, get_verse_for_topic, get_daily_verse,
    get_journey_verse, validate_ref,
    ALL_TOPICS, JOURNEY_TOPICS, JOURNEYS,
)
from devotional_engine import (
    generate_devotional, generate_sermon,
    generate_prayer, generate_study,
)
from formatters import (
    format_instagram, format_whatsapp, format_twitter, format_full,
)
from storage import (
    save_devotional, load_history, history_csv_bytes, clear_history,
    load_favorites, save_favorite, remove_favorite, is_favorite,
    get_cached_daily, cache_daily, topic_counts, get_streak,
)
from fallbacks import get_offline_devotional
from church_identity import (
    load_identity, save_identity, get_identity,
    get_accent_css, ACCENT_THEMES, THEME_NAMES,
)

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="The Word",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# SESSION STATE  — single initialisation block, no scattered guards
# ─────────────────────────────────────────────────────────────
_DEFAULTS: dict = {
    "devotional":      None,            # active devotional dict
    "sermon":          None,            # active sermon dict
    "prayer_result":   None,            # active prayer dict
    "study":           None,            # active study dict
    "journey_day":     1,               # journey day selector
    "sel_topic":       ALL_TOPICS[0],   # topic selector
    "mode":            "today",         # active nav section key
    "last_gen_time":   0.0,             # cooldown: epoch seconds of last generation
    "generating":      False,           # guard: prevents duplicate calls on rerun
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v
load_identity()  # merge any persisted JSON identity over defaults


# ══════════════════════════════════════════════════════════════
#  DESIGN SYSTEM — Cathedral Minimalism v3
#  + Church Identity accent system
#  + Improved sidebar hierarchy
#  + Warmer surfaces, better contrast
# ══════════════════════════════════════════════════════════════
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;0,700;1,300;1,400;1,600&family=EB+Garamond:ital,wght@0,400;0,500;1,400;1,500&display=swap" rel="stylesheet">

<style>
/* ═══════════════════════════════════════════════════════════
   1. DESIGN TOKENS — warm charcoal, cathedral minimalism
   Gold vars are overridden per-theme by get_accent_css()
   ═══════════════════════════════════════════════════════════ */
:root {
  /* Surface stack — 6 distinct warm tones (visible separation) */
  --bg:           #1a1510;   /* page — warm dark charcoal             */
  --bg-raised:    #211c15;   /* sidebar background                    */
  --bg-card:      #2a2318;   /* card surface                          */
  --bg-card-h:    #332c1e;   /* card hover                            */
  --bg-input:     #211c15;   /* text inputs, selects                  */
  --bg-dropdown:  #2d2519;   /* dropdown panel                        */
  --bg-dropdown-h:#3a3022;   /* dropdown item hover                   */

  /* Gold system — overridden by theme preset */
  --gold:         #c8922a;
  --gold-lt:      #daa84a;
  --gold-dim:     rgba(200,146,42,0.09);
  --gold-border:  rgba(200,146,42,0.18);
  --gold-hi:      rgba(200,146,42,0.30);

  /* Typography — improved contrast throughout */
  --text-prim:    #f0e6d0;   /* scripture, headings — bright warm     */
  --text-body:    #cfc0a0;   /* body copy — readable                  */
  --text-sec:     #a09070;   /* nav labels, secondary                 */
  --text-mute:    #6a5840;   /* metadata, footnotes                   */
  --text-prayer:  #bcc8ec;   /* prayer card                           */
  --text-nav:     #b0a080;   /* sidebar nav items — brighter than sec */
  --text-nav-act: #e8d0a0;   /* active nav item                       */

  /* Spacing */
  --sp-2xs: 0.2rem;
  --sp-xs:  0.35rem;
  --sp-sm:  0.6rem;
  --sp-md:  1rem;
  --sp-lg:  1.5rem;
  --sp-xl:  2rem;
  --sp-2xl: 3rem;

  /* Shape */
  --r-xs:   4px;  --r-sm: 6px;
  --r-md:   10px; --r-lg: 14px;
  --r-pill: 9999px;

  /* Motion */
  --t-fast: 0.14s ease;
  --t-med:  0.24s ease;

  /* Shadows */
  --sh-card:  0 2px 16px rgba(0,0,0,0.28);
  --sh-scrip: 0 6px 36px rgba(0,0,0,0.40);
}

/* ═══════════════════════════════════════════════════════════
   2. BASE
   ═══════════════════════════════════════════════════════════ */
html {
  font-size: 16px;
  -webkit-text-size-adjust: 100%;
  text-size-adjust: 100%;
}
body {
  font-family: 'EB Garamond', Georgia, serif;
  color: var(--text-body);
  background-color: var(--bg);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
.stApp {
  background:
    radial-gradient(ellipse 80% 45% at 8% 0%,  rgba(200,146,42,0.05) 0%, transparent 60%),
    radial-gradient(ellipse 55% 35% at 92% 100%, rgba(38,44,90,0.06)  0%, transparent 60%),
    var(--bg);
  min-height: 100vh;
}
.main .block-container {
  max-width: 880px;
  padding: var(--sp-xl) var(--sp-lg) 6rem;
  margin: 0 auto;
}

/* ═══════════════════════════════════════════════════════════
   3. SIDEBAR ARCHITECTURE
   3-zone layout: brand/identity → nav → utilities
   ═══════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
  background-color: var(--bg-raised);
  background-image: linear-gradient(170deg,
    rgba(200,146,42,0.025) 0%, transparent 35%);
  border-right: 1px solid var(--gold-border);
  min-width: 240px !important;
}
[data-testid="stSidebar"] > div:first-child {
  padding: 0 !important;
}

/* ── Zone 1: App brand ── */
.sb-app-brand {
  padding: 1.3rem 1.2rem 0.9rem;
  text-align: center;
  border-bottom: 1px solid var(--gold-border);
}
.sb-app-symbol {
  display: block;
  font-size: 1.1rem;
  color: var(--gold);
  letter-spacing: 0.7em;
  margin-left: 0.7em; /* compensate letter-spacing */
  animation: ember 5s ease-in-out infinite alternate;
}
.sb-app-name {
  display: block;
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--text-prim);
  letter-spacing: 0.05em;
  margin-top: 0.4rem;
  line-height: 1;
}
.sb-app-tagline {
  display: block;
  font-family: 'EB Garamond', serif;
  font-size: 0.64rem;
  color: var(--text-mute);
  letter-spacing: 0.18em;
  text-transform: uppercase;
  margin-top: 0.28rem;
}

/* ── Zone 1b: Church identity block ── */
.sb-church-block {
  padding: 0.7rem 1.2rem 0.9rem;
  text-align: center;
  border-bottom: 1px solid rgba(200,146,42,0.08);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.2rem;
}
.sb-church-logo {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid var(--gold-border);
  margin-bottom: 0.2rem;
}
.sb-church-name {
  font-family: 'Cormorant Garamond', serif;
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-sec);
  letter-spacing: 0.04em;
  line-height: 1.2;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sb-church-subtitle {
  font-family: 'EB Garamond', serif;
  font-size: 0.68rem;
  color: var(--text-mute);
  font-style: italic;
  letter-spacing: 0.04em;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sb-streak {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.15rem 0.6rem;
  background: var(--gold-dim);
  border: 1px solid var(--gold-border);
  border-radius: var(--r-pill);
  font-family: 'EB Garamond', serif;
  font-size: 0.72rem;
  color: var(--gold-lt);
  margin-top: 0.25rem;
}

/* ── Zone 2: Navigation ── */
.sb-nav-section {
  padding: 0.5rem 0.5rem 0.2rem;
}
.sb-nav-group-label {
  padding: 0.65rem 0.8rem 0.15rem;
  font-family: 'EB Garamond', serif;
  font-size: 0.58rem;
  font-weight: 600;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: var(--text-mute);
  user-select: none;
}
/* Nav item wrapper — carries active/inactive class */
.sb-nav-item > div > button,
.sb-nav-active > div > button {
  width: 100% !important;
  text-align: left !important;
  justify-content: flex-start !important;
  border: none !important;
  border-left: 2px solid transparent !important;
  border-radius: 0 var(--r-sm) var(--r-sm) 0 !important;
  background: transparent !important;
  color: var(--text-nav) !important;
  font-family: 'EB Garamond', serif !important;
  font-size: 0.97rem !important;
  letter-spacing: 0.01em !important;
  line-height: 1.25 !important;
  min-height: unset !important;
  padding: 0.44rem 0.85rem !important;
  box-shadow: none !important;
  transition: background var(--t-fast), color var(--t-fast),
              border-left-color var(--t-fast) !important;
}
.sb-nav-item > div > button:hover {
  background: var(--gold-dim) !important;
  color: var(--text-body) !important;
  border-left-color: rgba(200,146,42,0.30) !important;
}
.sb-nav-active > div > button {
  background: rgba(200,146,42,0.08) !important;
  color: var(--text-nav-act) !important;
  border-left-color: var(--gold) !important;
}
.sb-nav-active > div > button:hover {
  background: rgba(200,146,42,0.12) !important;
}

/* ── Zone 3: Utilities (bottom) ── */
.sb-util-section {
  padding: 0.4rem 0.8rem 0.6rem;
}
.sb-util-label {
  display: block;
  font-family: 'EB Garamond', serif;
  font-size: 0.58rem;
  font-weight: 600;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--text-mute);
  margin-bottom: 0.3rem;
}
.sb-date {
  font-family: 'EB Garamond', serif;
  font-size: 0.7rem;
  color: var(--text-mute);
  text-align: center;
  font-style: italic;
  line-height: 1.8;
  padding: 0.5rem 0.8rem 0.9rem;
}

/* Override ALL Streamlit sidebar button styles */
[data-testid="stSidebar"] .stButton > button {
  background: transparent !important;
  border: none !important;
  border-left: 2px solid transparent !important;
  border-radius: 0 var(--r-sm) var(--r-sm) 0 !important;
  color: var(--text-nav) !important;
  font-family: 'EB Garamond', serif !important;
  font-size: 0.97rem !important;
  text-align: left !important;
  justify-content: flex-start !important;
  width: 100% !important;
  min-height: unset !important;
  padding: 0.44rem 0.85rem !important;
  line-height: 1.25 !important;
  box-shadow: none !important;
  transition: background var(--t-fast), color var(--t-fast),
              border-left-color var(--t-fast) !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: var(--gold-dim) !important;
  color: var(--text-body) !important;
  border-left-color: rgba(200,146,42,0.30) !important;
  transform: none !important;
}
[data-testid="stSidebar"] .stButton > button:active { transform: none !important; }

/* Sidebar selects, toggles */
[data-testid="stSidebar"] .stSelectbox > div > div {
  background: var(--bg-card) !important;
  border: 1px solid var(--gold-border) !important;
  border-radius: var(--r-sm) !important;
  color: var(--text-body) !important;
  font-family: 'EB Garamond', serif !important;
  font-size: 0.9rem !important;
}
[data-testid="stSidebar"] .stSelectbox label {
  font-family: 'EB Garamond', serif !important;
  font-size: 0.58rem !important;
  letter-spacing: 0.2em !important;
  text-transform: uppercase !important;
  color: var(--text-mute) !important;
}
[data-testid="stSidebar"] hr {
  border: none !important;
  border-top: 1px solid var(--gold-border) !important;
  margin: 0.35rem 0.8rem !important;
  opacity: 1 !important;
}
[data-testid="stSidebar"] .stToggle label {
  font-family: 'EB Garamond', serif !important;
  font-size: 0.88rem !important;
  color: var(--text-sec) !important;
}

/* ═══════════════════════════════════════════════════════════
   4. TYPOGRAPHY
   ═══════════════════════════════════════════════════════════ */
.page-hd { margin-bottom: var(--sp-xl); }
.page-hd-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(1.55rem, 4vw, 1.95rem);
  font-weight: 600;
  color: var(--text-prim);
  line-height: 1.1;
  letter-spacing: -0.015em;
  margin: 0;
}
.page-hd-sub {
  font-family: 'EB Garamond', serif;
  font-size: clamp(0.95rem, 2.5vw, 1.05rem);
  color: var(--text-mute);
  font-style: italic;
  margin-top: 0.35rem;
  line-height: 1.5;
}
.date-ribbon {
  display: inline-flex;
  align-items: center;
  padding: 0.26rem 0.85rem;
  background: var(--gold-dim);
  border: 1px solid var(--gold-hi);
  border-radius: var(--r-pill);
  margin-bottom: var(--sp-md);
}
.date-ribbon span {
  font-family: 'EB Garamond', serif;
  font-size: 0.76rem;
  font-weight: 500;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--gold);
}

/* ═══════════════════════════════════════════════════════════
   5. SCRIPTURE BLOCK
   ═══════════════════════════════════════════════════════════ */
.scripture-wrap {
  position: relative;
  padding: clamp(1.5rem, 4vw, 2.4rem) clamp(1.3rem, 4vw, 2.5rem) clamp(1.4rem, 3vw, 2rem);
  margin: var(--sp-sm) 0 var(--sp-xl);
  border-radius: var(--r-lg);
  background:
    linear-gradient(150deg, rgba(200,146,42,0.05) 0%, transparent 50%),
    var(--bg-card);
  border: 1px solid var(--gold-border);
  box-shadow: var(--sh-scrip);
  overflow: hidden;
  animation: rise 0.5s cubic-bezier(0.22,1,0.36,1) both;
}
.scripture-wrap::before {
  content: '\201C';
  position: absolute;
  top: -1.8rem; left: 0.8rem;
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(5rem, 11vw, 9rem);
  line-height: 1;
  color: rgba(200,146,42,0.07);
  pointer-events: none;
  user-select: none;
}
.scripture-wrap::after {
  content: '';
  position: absolute;
  bottom: 0; left: 14%; right: 14%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(200,146,42,0.38), transparent);
}
.scripture-meta {
  display: flex; flex-wrap: wrap;
  align-items: center;
  gap: var(--sp-sm);
  margin-bottom: var(--sp-md);
}
.scripture-ref {
  font-family: 'EB Garamond', serif;
  font-size: 0.74rem;
  font-weight: 500;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--gold);
}
.scripture-badge {
  font-family: 'EB Garamond', serif;
  font-size: 0.64rem;
  font-weight: 500;
  letter-spacing: 0.1em;
  color: var(--gold);
  background: var(--gold-dim);
  border: 1px solid var(--gold-hi);
  border-radius: var(--r-xs);
  padding: 0.06rem 0.42rem;
}
.scripture-text {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(1.22rem, 3.2vw, 1.52rem);
  font-style: italic;
  font-weight: 400;
  line-height: 1.84;
  color: var(--text-prim);
  letter-spacing: 0.01em;
}
.scripture-trust {
  margin-top: var(--sp-md);
  font-family: 'EB Garamond', serif;
  font-size: 0.64rem;
  color: var(--text-mute);
  font-style: italic;
  letter-spacing: 0.08em;
}

/* ═══════════════════════════════════════════════════════════
   6. CONTENT CARDS
   ═══════════════════════════════════════════════════════════ */
.card {
  background: var(--bg-card);
  border: 1px solid var(--gold-border);
  border-radius: var(--r-md);
  padding: var(--sp-lg) clamp(0.9rem, 2.5vw, 1.55rem);
  margin-bottom: var(--sp-sm);
  transition: border-color var(--t-fast), background var(--t-fast);
  animation: rise 0.38s cubic-bezier(0.22,1,0.36,1) both;
}
.card:hover {
  border-color: var(--gold-hi);
  background: var(--bg-card-h);
}
.card-label {
  font-family: 'EB Garamond', serif;
  font-size: 0.62rem;
  font-weight: 600;
  letter-spacing: 0.25em;
  text-transform: uppercase;
  color: var(--gold);
  opacity: 0.9;
  margin-bottom: 0.55rem;
  display: block;
}
.card-body {
  font-family: 'EB Garamond', serif;
  font-size: clamp(1rem, 2.4vw, 1.1rem);
  line-height: 1.78;
  color: var(--text-body);
}
.card-prayer {
  background: rgba(34,40,80,0.48);
  border-color: rgba(80,100,210,0.18);
}
.card-prayer .card-label { color: #8892d0; opacity: 1; }
.card-prayer .card-body  { color: var(--text-prayer); font-style: italic; }
.card-memory {
  background: linear-gradient(135deg, rgba(200,146,42,0.08) 0%, rgba(20,14,8,0.45) 100%);
  border-color: rgba(200,146,42,0.26);
  text-align: center;
  padding: var(--sp-xl);
}
.card-memory .card-label { text-align: center; margin-bottom: var(--sp-sm); }
.card-memory .card-body {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(1.08rem, 2.8vw, 1.3rem);
  font-weight: 600;
  font-style: italic;
  color: var(--text-prim);
}

/* ── API quota notice ── */
.api-notice {
  display: flex;
  align-items: flex-start;
  gap: 0.9rem;
  background: rgba(200,146,42,0.07);
  border: 1px solid rgba(200,146,42,0.22);
  border-radius: var(--r-md);
  padding: var(--sp-md) var(--sp-lg);
  margin-bottom: var(--sp-lg);
  animation: fadeIn 0.4s ease both;
}
.api-notice-icon { font-size: 1rem; color: var(--gold); flex-shrink: 0; opacity: 0.7; margin-top: 0.1rem; }
.api-notice-body {
  font-family: 'EB Garamond', serif;
  font-size: 0.94rem;
  line-height: 1.6;
  color: var(--text-sec);
}
.api-notice-body strong { color: var(--gold-lt); font-weight: 600; display: block; margin-bottom: 0.2rem; }

.fallback-note {
  background: rgba(110,80,10,0.18);
  border: 1px solid rgba(200,148,0,0.25);
  border-radius: var(--r-sm);
  padding: var(--sp-sm) var(--sp-md);
  font-family: 'EB Garamond', serif;
  font-size: 0.88rem;
  color: #c8a050;
  margin-bottom: var(--sp-md);
}

/* ── Sermon points ── */
.sermon-point {
  border-left: 2px solid var(--gold);
  border-radius: 0 var(--r-sm) var(--r-sm) 0;
  padding: var(--sp-md) var(--sp-lg);
  margin-bottom: var(--sp-sm);
  background: var(--bg-card);
  transition: background var(--t-fast);
}
.sermon-point:hover { background: var(--bg-card-h); }
.sermon-point-num   { font-size: 0.62rem; letter-spacing: 0.22em; text-transform: uppercase; color: var(--gold); margin-bottom: var(--sp-2xs); }
.sermon-point-title { font-family: 'Cormorant Garamond', serif; font-size: 1.08rem; font-weight: 600; color: var(--text-prim); margin-bottom: var(--sp-xs); }
.sermon-illus       { font-size: 0.9rem; color: var(--text-mute); font-style: italic; margin-top: var(--sp-xs); }

/* ── Metrics ── */
.metric-box { background: var(--bg-card); border: 1px solid var(--gold-border); border-radius: var(--r-md); padding: var(--sp-lg) var(--sp-md); text-align: center; }
.metric-num { display: block; font-family: 'Cormorant Garamond', serif; font-size: clamp(1.8rem,4vw,2.4rem); font-weight: 700; color: var(--text-prim); line-height: 1; }
.metric-lbl { display: block; font-family: 'EB Garamond', serif; font-size: 0.65rem; letter-spacing: 0.16em; text-transform: uppercase; color: var(--text-mute); margin-top: 0.35rem; }

/* ── Empty states ── */
.empty-state { text-align: center; padding: var(--sp-2xl) 0; opacity: 0.45; }
.empty-state-icon { display: block; font-size: 2rem; color: var(--gold); margin-bottom: var(--sp-sm); animation: ember 4s ease-in-out infinite alternate; }
.empty-state-text { font-family: 'EB Garamond', serif; font-size: 0.95rem; font-style: italic; color: var(--text-mute); line-height: 1.65; white-space: pre-line; }

/* ── Export box ── */
.export-box {
  background: var(--bg-raised);
  border: 1px solid var(--gold-border);
  border-radius: var(--r-md);
  padding: var(--sp-md) clamp(0.85rem, 2.5vw, 1.3rem);
  font-family: 'EB Garamond', serif;
  font-size: 0.93rem;
  line-height: 1.65;
  color: var(--text-body);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 260px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: var(--gold-border) transparent;
}
.export-box::-webkit-scrollbar { width: 3px; }
.export-box::-webkit-scrollbar-thumb { background: var(--gold-border); border-radius: 2px; }
.char-track { height: 2px; background: var(--gold-border); border-radius: 1px; margin-top: 5px; }
.char-fill  { height: 100%; border-radius: 1px; background: var(--gold); transition: width 0.3s; }

/* ── Divider ── */
.vdivide { display: flex; align-items: center; gap: var(--sp-md); margin: var(--sp-xl) 0 var(--sp-lg); }
.vdivide-line { flex: 1; height: 1px; background: var(--gold-hi); opacity: 0.45; }
.vdivide-sym  { font-size: 0.62rem; letter-spacing: 0.38em; color: var(--gold); opacity: 0.55; user-select: none; }

/* ── Church Settings mode ── */
.settings-section {
  background: var(--bg-card);
  border: 1px solid var(--gold-border);
  border-radius: var(--r-md);
  padding: var(--sp-lg) var(--sp-xl);
  margin-bottom: var(--sp-lg);
}
.settings-section-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-prim);
  margin-bottom: var(--sp-md);
  padding-bottom: var(--sp-sm);
  border-bottom: 1px solid var(--gold-border);
}
.theme-preview {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.3rem 0.7rem;
  border-radius: var(--r-sm);
  border: 1px solid var(--gold-border);
  background: var(--gold-dim);
  font-family: 'EB Garamond', serif;
  font-size: 0.82rem;
  color: var(--text-sec);
  cursor: default;
}
.theme-swatch {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* ═══════════════════════════════════════════════════════════
   7. STREAMLIT WIDGET OVERRIDES — no white components
   ═══════════════════════════════════════════════════════════ */

/* Main content buttons */
.main .stButton > button {
  font-family: 'EB Garamond', serif;
  font-size: 1rem;
  letter-spacing: 0.04em;
  border-radius: var(--r-sm);
  min-height: 2.35rem;
  line-height: 1;
  transition: all var(--t-fast);
}
.main .stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #422200 0%, #6e4008 100%);
  border: 1px solid var(--gold);
  color: var(--text-prim) !important;
}
.main .stButton > button[kind="primary"]:hover {
  background: linear-gradient(135deg, #4e2a00 0%, #7e4c0e 100%);
  box-shadow: 0 3px 14px rgba(200,146,42,0.22);
  transform: translateY(-1px);
}
.main .stButton > button[kind="primary"]:active { transform: none; box-shadow: none; }
.main .stButton > button:not([kind="primary"]) {
  background: transparent;
  border: 1px solid var(--gold-border);
  color: var(--text-sec) !important;
}
.main .stButton > button:not([kind="primary"]):hover {
  border-color: var(--gold-hi);
  background: var(--gold-dim);
}

/* Text inputs */
.stTextInput > div > div > input {
  background: var(--bg-input) !important;
  border: 1px solid var(--gold-border) !important;
  border-radius: var(--r-sm) !important;
  color: var(--text-body) !important;
  font-family: 'EB Garamond', serif !important;
  font-size: 1rem !important;
  padding: 0.5rem 0.85rem !important;
  transition: border-color var(--t-fast), box-shadow var(--t-fast);
}
.stTextInput > div > div > input:focus {
  border-color: var(--gold) !important;
  box-shadow: 0 0 0 2px rgba(200,146,42,0.10) !important;
  outline: none !important;
}
.stTextInput > div > div > input::placeholder { color: var(--text-mute) !important; }
.stTextInput label { font-family: 'EB Garamond', serif !important; color: var(--text-mute) !important; font-size: 0.82rem !important; }

/* Selectbox */
.stSelectbox > div > div {
  background: var(--bg-input) !important;
  border: 1px solid var(--gold-border) !important;
  border-radius: var(--r-sm) !important;
  color: var(--text-body) !important;
  font-family: 'EB Garamond', serif !important;
  font-size: 0.98rem !important;
}
.stSelectbox label { font-family: 'EB Garamond', serif !important; color: var(--text-mute) !important; font-size: 0.82rem !important; }

/* File uploader */
[data-testid="stFileUploaderDropzone"] {
  background: var(--bg-input) !important;
  border: 1px dashed var(--gold-border) !important;
  border-radius: var(--r-sm) !important;
}
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzone"] p {
  color: var(--text-mute) !important;
  font-family: 'EB Garamond', serif !important;
}

/* Dropdowns/popovers — eliminate white panels */
[data-baseweb="popover"] {
  background: var(--bg-dropdown) !important;
  border: 1px solid var(--gold-border) !important;
  border-radius: var(--r-sm) !important;
  box-shadow: 0 8px 28px rgba(0,0,0,0.45) !important;
}
[data-baseweb="menu"] {
  background: var(--bg-dropdown) !important;
  border-radius: var(--r-sm) !important;
}
[data-baseweb="menu"] ul { background: var(--bg-dropdown) !important; padding: var(--sp-xs) !important; }
[data-baseweb="menu-item"] {
  background: transparent !important;
  color: var(--text-body) !important;
  font-family: 'EB Garamond', serif !important;
  font-size: 0.96rem !important;
  border-radius: var(--r-xs) !important;
  padding: 0.42rem 0.7rem !important;
  transition: background var(--t-fast) !important;
}
[data-baseweb="menu-item"]:hover,
[data-baseweb="menu-item"][aria-selected="true"] {
  background: var(--bg-dropdown-h) !important;
  color: var(--text-prim) !important;
}
[data-baseweb="select"] span,
[data-baseweb="select"] [data-testid="stMarkdownContainer"] p { color: var(--text-body) !important; font-family: 'EB Garamond', serif !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  background: transparent;
  gap: 0;
  border-bottom: 1px solid var(--gold-border);
  padding: 0;
}
.stTabs [data-baseweb="tab"] {
  background: transparent;
  font-family: 'EB Garamond', serif;
  font-size: 0.9rem;
  color: var(--text-mute) !important;
  padding: 0.52rem 1rem;
  border-radius: 0;
  border-bottom: 2px solid transparent;
  transition: color var(--t-fast), border-color var(--t-fast);
}
.stTabs [aria-selected="true"] { color: var(--gold) !important; border-bottom-color: var(--gold); background: transparent; }
.stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) { color: var(--text-sec) !important; }
.stTabs [data-baseweb="tab-panel"] { padding: var(--sp-md) 0 !important; }

/* Expanders */
[data-testid="stExpander"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--gold-border) !important;
  border-radius: var(--r-md) !important;
  margin-bottom: var(--sp-sm) !important;
}
[data-testid="stExpander"] summary { font-family: 'EB Garamond', serif !important; font-size: 0.96rem !important; color: var(--text-body) !important; padding: 0.75rem 1rem !important; }
[data-testid="stExpander"] summary:hover { color: var(--text-prim) !important; }

/* Toggles */
.stToggle label { font-family: 'EB Garamond', serif !important; font-size: 0.9rem !important; color: var(--text-sec) !important; }

/* Text area */
.stTextArea textarea {
  background: var(--bg-input) !important;
  border: 1px solid var(--gold-border) !important;
  border-radius: var(--r-sm) !important;
  color: var(--text-body) !important;
  font-family: 'EB Garamond', serif !important;
  font-size: 0.96rem !important;
}

/* System messages */
.stCaption { font-family: 'EB Garamond', serif !important; font-size: 0.8rem !important; color: var(--text-mute) !important; }
.stToast   { background: var(--bg-card) !important; border: 1px solid var(--gold-border) !important; color: var(--text-body) !important; font-family: 'EB Garamond', serif !important; }
.stException, .stError { background: rgba(160,40,40,0.12) !important; border: 1px solid rgba(200,60,60,0.25) !important; border-radius: var(--r-sm) !important; color: #e8a0a0 !important; font-family: 'EB Garamond', serif !important; }
.stSuccess  { background: rgba(40,100,60,0.12) !important; border: 1px solid rgba(60,160,80,0.22) !important; border-radius: var(--r-sm) !important; font-family: 'EB Garamond', serif !important; }
.stWarning  { background: rgba(160,120,20,0.12) !important; border: 1px solid rgba(200,160,30,0.22) !important; border-radius: var(--r-sm) !important; font-family: 'EB Garamond', serif !important; }
.stSpinner > div { border-color: var(--gold) transparent transparent !important; }
.stVegaLiteChart { animation: fadeIn 0.4s ease both; }

/* ═══════════════════════════════════════════════════════════
   8. STREAMLIT CHROME — preserve mobile sidebar toggle
   ═══════════════════════════════════════════════════════════ */
[data-testid="stHeader"] { background: transparent !important; border-bottom: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] { display: flex !important; visibility: visible !important; }
button[aria-label="Open sidebar"],
button[aria-label="Close sidebar"] {
  display: flex !important; visibility: visible !important;
  color: var(--gold) !important;
  background: rgba(200,146,42,0.08) !important;
  border-radius: var(--r-sm) !important;
}
[data-testid="stDecoration"] { display: none !important; }
.stDeployButton { display: none !important; }
footer { display: none !important; }
#MainMenu { display: none !important; }

/* ═══════════════════════════════════════════════════════════
   9. ANIMATIONS
   ═══════════════════════════════════════════════════════════ */
@keyframes rise { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:translateY(0); } }
@keyframes ember {
  from { text-shadow: 0 0 7px rgba(200,146,42,0.22), 0 0 16px rgba(200,146,42,0.07); }
  to   { text-shadow: 0 0 16px rgba(200,146,42,0.52), 0 0 34px rgba(200,146,42,0.16), 0 0 52px rgba(200,146,42,0.04); }
}
@keyframes fadeIn { from { opacity:0; } to { opacity:1; } }

/* ═══════════════════════════════════════════════════════════
   10. RESPONSIVE
   ═══════════════════════════════════════════════════════════ */
@media (max-width: 768px) {
  .main .block-container { padding: var(--sp-md) var(--sp-sm) 5rem; }
  .scripture-wrap { padding: var(--sp-lg) var(--sp-md); margin-bottom: var(--sp-lg); }
  .card { padding: var(--sp-md); }
  .card-memory { padding: var(--sp-lg) var(--sp-md); }
  .settings-section { padding: var(--sp-md); }
}
@media (max-width: 480px) {
  .scripture-text { font-size: 1.2rem; line-height: 1.78; }
  .page-hd-title { font-size: 1.5rem; }
}
</style>
""", unsafe_allow_html=True)


# ── Inject theme accent override immediately after base CSS ──
_identity_now = get_identity()
st.markdown(get_accent_css(_identity_now.get("accent_theme", "Gold Ember")), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  SHARED UI COMPONENTS
# ══════════════════════════════════════════════════════════════

def _divider(symbol: str = "✦  ✦  ✦") -> None:
    st.markdown(
        f'<div class="vdivide">'
        f'<div class="vdivide-line"></div>'
        f'<div class="vdivide-sym">{symbol}</div>'
        f'<div class="vdivide-line"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _header(title: str, subtitle: str = "") -> None:
    sub_html = f'<p class="page-hd-sub">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f'<div class="page-hd">'
        f'<h1 class="page-hd-title">{title}</h1>'
        f'{sub_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _empty(icon: str, message: str) -> None:
    st.markdown(
        f'<div class="empty-state">'
        f'<span class="empty-state-icon">{icon}</span>'
        f'<span class="empty-state-text">{message}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _quota_notice() -> None:
    """Render an elegant quota-exceeded notice instead of a red error wall."""
    st.markdown(
        '<div class="api-notice">'
        '<span class="api-notice-icon">✦</span>'
        '<div class="api-notice-body">'
        '<strong>Using an offline reflection</strong>'
        'The AI reached its usage limit for this moment. A thoughtful fallback '
        'has been prepared — your devotional is still complete. '
        'Try again in a few minutes if you prefer a freshly generated reflection.'
        '</div></div>',
        unsafe_allow_html=True,
    )


def render_scripture(d: dict) -> None:
    """
    Render the scripture centrepiece block.
    Reads canonical key 'text'. Defensive .get() on everything.
    """
    ref    = d.get("reference", "")
    verse  = d.get("text", "")          # canonical key
    trans  = d.get("translation_id", "KJV").upper()
    label  = d.get("journey_theme") or d.get("topic") or ""

    if d.get("_fallback"):
        st.markdown(
            '<div class="fallback-note">'
            '⚠ Bible API unavailable — displaying a cached fallback verse.'
            '</div>',
            unsafe_allow_html=True,
        )

    badges = f'<span class="scripture-badge">{trans}</span>'
    if label and label != "General":
        badges += f' <span class="scripture-badge">{label}</span>'

    st.markdown(
        f'<div class="scripture-wrap">'
        f'  <div class="scripture-meta">'
        f'    <span class="scripture-ref">{ref}</span>'
        f'    {badges}'
        f'  </div>'
        f'  <div class="scripture-text">{verse}</div>'
        f'  <div class="scripture-trust">✦ Scripture from bible-api.com — not AI generated</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_devotional_body(d: dict, key_suffix: str = "") -> None:
    """
    Render devotional content cards.
    All dict access uses .get() — no KeyErrors possible.
    Shows elegant quota notice when AI used its fallback.
    """
    if d.get("_quota_error"):
        _quota_notice()
    col1, col2 = st.columns(2, gap="large")

    with col1:
        if d.get("explanation"):
            st.markdown(
                f'<div class="card">'
                f'<div class="card-label">Explanation</div>'
                f'<div class="card-body">{d["explanation"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        if d.get("application"):
            st.markdown(
                f'<div class="card">'
                f'<div class="card-label">Apply Today</div>'
                f'<div class="card-body">{d["application"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with col2:
        if d.get("reflection"):
            st.markdown(
                f'<div class="card">'
                f'<div class="card-label">Reflect</div>'
                f'<div class="card-body">{d["reflection"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        if d.get("prayer"):
            st.markdown(
                f'<div class="card card-prayer">'
                f'<div class="card-label">Prayer</div>'
                f'<div class="card-body">{d["prayer"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    if d.get("memory"):
        st.markdown(
            f'<div class="card card-memory">'
            f'<div class="card-label">Hold This Close</div>'
            f'<div class="card-body">"{d["memory"]}"</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Save / Unsave button — below cards, low visual weight
    ref   = d.get("reference", "")
    saved = is_favorite(ref)
    fc, _ = st.columns([1, 6])
    with fc:
        btn_label = "★ Saved" if saved else "☆ Save"
        if st.button(btn_label, key=f"fav_{key_suffix}_{ref}"):
            if saved:
                remove_favorite(ref)
                st.toast("Removed from saved.")
            else:
                save_favorite(d)
                st.toast(f"Saved — {ref}")
            # No st.rerun() — toast is sufficient feedback


def render_social_export(d: dict) -> None:
    """Export tabs for social media. No AI calls — pure formatting."""
    _divider("Share")
    t1, t2, t3, t4 = st.tabs(["Instagram", "WhatsApp", "Twitter", "Full Text"])

    with t1:
        txt = format_instagram(d)
        st.markdown(f'<div class="export-box">{txt}</div>', unsafe_allow_html=True)
        pct = min(len(txt) / 2200, 1)
        st.markdown(
            f'<div class="char-track"><div class="char-fill" style="width:{pct*100:.1f}%"></div></div>',
            unsafe_allow_html=True,
        )
        st.caption(f"{len(txt):,} / 2,200 characters")
        st.download_button("Download", txt, "instagram.txt", "text/plain", use_container_width=True)

    with t2:
        txt = format_whatsapp(d)
        st.markdown(f'<div class="export-box">{txt}</div>', unsafe_allow_html=True)
        st.download_button("Download", txt, "whatsapp.txt", "text/plain", use_container_width=True)

    with t3:
        txt  = format_twitter(d)
        over = len(txt) > 280
        clr  = "#d05050" if over else "#5a9060"
        st.markdown(f'<div class="export-box">{txt}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<span style="font-size:0.78rem;color:{clr};font-family:\'EB Garamond\',serif;">'
            f'{len(txt)} / 280 characters</span>',
            unsafe_allow_html=True,
        )
        st.download_button("Download", txt, "tweet.txt", "text/plain", use_container_width=True)

    with t4:
        full = format_full(d)
        st.text_area("", full, height=240, label_visibility="collapsed")
        st.download_button("Download .txt", full, "devotional.txt", "text/plain", use_container_width=True)


# ─────────────────────────────────────────────────────────────
# CORE GENERATION FUNCTION
# Guards against duplicate calls on Streamlit reruns.
# Enforces a 15-second cooldown between generations.
# ─────────────────────────────────────────────────────────────
_COOLDOWN_SEC = 15


def _can_generate() -> bool:
    """True if enough time has passed since last generation."""
    return (time.time() - st.session_state.get("last_gen_time", 0.0)) >= _COOLDOWN_SEC


def _cooldown_remaining() -> int:
    elapsed = time.time() - st.session_state.get("last_gen_time", 0.0)
    return max(0, int(_COOLDOWN_SEC - elapsed))


def _generate(
    verse: dict,
    topic: str,
    journey_theme: str = None,
    include_prayer: bool = True,
    include_memory: bool = True,
) -> dict:
    """
    Generate a devotional. Guards:
    - Session-state dedup: if st.session_state.generating is True, return existing
    - Cooldown: minimum 15 s between Gemini calls
    - Returns existing devotional rather than re-calling if already matching
    """
    # Guard 1: already mid-generation (Streamlit rerun during spinner)
    if st.session_state.get("generating"):
        existing = st.session_state.get("devotional")
        if existing:
            return existing

    # Guard 2: cooldown
    if not _can_generate():
        secs = _cooldown_remaining()
        st.warning(f"Please wait {secs}s before generating again.")
        existing = st.session_state.get("devotional")
        if existing:
            return existing
        return get_offline_devotional()

    st.session_state.generating = True
    st.session_state.last_gen_time = time.time()

    try:
        with st.spinner(""):
            d = generate_devotional(
                reference      = verse.get("reference", ""),
                verse_text     = verse.get("text", ""),
                topic          = topic,
                journey_theme  = journey_theme,
                include_prayer = include_prayer,
                include_memory = include_memory,
            )
            d["translation_id"] = verse.get("translation_id", "KJV")
            d["_fallback"]      = verse.get("_fallback", False)
            st.session_state.devotional = d
            save_devotional(d)
    finally:
        st.session_state.generating = False

    return st.session_state.devotional


# ══════════════════════════════════════════════════════════════
#  SIDEBAR — 3-zone architecture
#  Zone 1: App brand + church identity
#  Zone 2: Navigation rail (grouped, button-based)
#  Zone 3: Utilities (translation, toggles, date)
# ══════════════════════════════════════════════════════════════

_NAV_GROUPS = [
    (None, [   # no group label for primary item
        ("today",   "☀  Today's Word"),
    ]),
    ("Devotionals", [
        ("topic",   "📖  By Topic"),
        ("journey", "🗺  7-Day Journey"),
        ("search",  "🔍  Search"),
    ]),
    ("Tools", [
        ("sermon",  "🎙  Sermon"),
        ("study",   "📚  Study"),
        ("prayer",  "🙏  Prayer"),
    ]),
    ("Library", [
        ("saved",     "⭐  Saved"),
        ("analytics", "📊  Analytics"),
        ("history",   "📁  History"),
        ("settings",  "⚙  Church Settings"),
    ]),
]

with st.sidebar:
    identity = get_identity()
    church_name     = (identity.get("church_name") or "").strip()[:32]
    church_subtitle = (identity.get("church_subtitle") or "").strip()[:45]
    logo_bytes      = identity.get("logo_bytes")
    streak          = get_streak()

    # ── Zone 1: App brand ──────────────────────────────────────
    st.markdown(
        '<div class="sb-app-brand">'
        '  <span class="sb-app-symbol">✦  ✦  ✦</span>'
        '  <span class="sb-app-name">The Word</span>'
        '  <span class="sb-app-tagline">Daily Devotional</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Zone 1b: Church identity ───────────────────────────────
    if church_name:
        logo_html = ""
        if logo_bytes:
            import base64
            b64 = base64.b64encode(logo_bytes).decode()
            logo_html = f'<img src="data:image/png;base64,{b64}" class="sb-church-logo" alt="Church logo">'
        streak_html = (
            f'<span class="sb-streak">🔥 {streak} days</span>' if streak > 0 else ""
        )
        subtitle_html = (
            f'<span class="sb-church-subtitle">{church_subtitle}</span>'
            if church_subtitle else ""
        )
        st.markdown(
            f'<div class="sb-church-block">'
            f'  {logo_html}'
            f'  <span class="sb-church-name">{church_name}</span>'
            f'  {subtitle_html}'
            f'  {streak_html}'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        if streak > 0:
            st.markdown(
                f'<div style="text-align:center;padding:0.4rem 0 0.6rem;">'
                f'<span class="sb-streak">🔥 {streak} days</span></div>',
                unsafe_allow_html=True,
            )

    # ── Zone 2: Navigation ──────────────────────────────────────
    current = st.session_state.get("mode", "today")
    st.markdown('<div class="sb-nav-section">', unsafe_allow_html=True)
    for group_label, items in _NAV_GROUPS:
        if group_label:
            st.markdown(
                f'<div class="sb-nav-group-label">{group_label}</div>',
                unsafe_allow_html=True,
            )
        for key, label in items:
            css_cls = "sb-nav-active" if current == key else "sb-nav-item"
            st.markdown(f'<div class="{css_cls}">', unsafe_allow_html=True)
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state.mode = key
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Zone 3: Utilities ───────────────────────────────────────
    st.divider()
    st.markdown('<div class="sb-util-section">', unsafe_allow_html=True)
    st.markdown('<span class="sb-util-label">Translation</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    translation = st.selectbox(
        "Translation",
        ["kjv", "web", "bbe"],
        label_visibility="collapsed",
        format_func=lambda x: {
            "kjv": "King James (KJV)",
            "web": "World English (WEB)",
            "bbe": "Basic English (BBE)",
        }[x],
    )

    tc, mc = st.columns(2)
    with tc: include_prayer = st.toggle("Prayer", value=True)
    with mc: include_memory = st.toggle("Memory", value=True)

    st.markdown(
        f'<div class="sb-date">'
        f'{datetime.now().strftime("%A")}<br>{datetime.now().strftime("%B %d, %Y")}'
        f'</div>',
        unsafe_allow_html=True,
    )

# Resolve active mode
mode = st.session_state.get("mode", "today")


# ══════════════════════════════════════════════════════════════
#  ☀  TODAY'S WORD
#  Emotional centrepiece. Auto-loads if cached. One CTA if not.
# ══════════════════════════════════════════════════════════════
if mode == "today":
    st.markdown(
        f'<div class="date-ribbon"><span>{datetime.now().strftime("%A, %B %d, %Y")}</span></div>',
        unsafe_allow_html=True,
    )
    _header(
        "Today's Word",
        "One devotional for the whole congregation — the same for everyone today.",
    )

    cached = get_cached_daily()

    if cached and cached.get("explanation"):
        # ── Full devotional in cache → render directly, no spinner ──
        render_scripture(cached)
        render_devotional_body(cached, key_suffix="today")
        render_social_export(cached)

    elif cached and not cached.get("explanation"):
        # ── Verse cached but no devotional yet ──
        render_scripture(cached)
        if st.button("Open Today's Devotional", type="primary", use_container_width=True):
            d = _generate(
                cached, cached.get("topic", "General"),
                include_prayer=include_prayer, include_memory=include_memory,
            )
            cache_daily(d)
            render_devotional_body(d, key_suffix="today_gen")
            render_social_export(d)

    else:
        # ── Nothing cached today ──
        _empty("✦", "Today's word is waiting for you.")
        if st.button("Receive Today's Word", type="primary", use_container_width=True):
            try:
                with st.spinner(""):
                    verse, topic = get_daily_verse(translation)
                d = _generate(
                    verse, topic,
                    include_prayer=include_prayer, include_memory=include_memory,
                )
                cache_daily(d)
                render_scripture(d)
                render_devotional_body(d, key_suffix="today_fresh")
                render_social_export(d)
            except Exception as e:
                st.error(f"Unable to load today's word: {e}")


# ══════════════════════════════════════════════════════════════
#  📖  BY TOPIC
# ══════════════════════════════════════════════════════════════
elif mode == "topic":
    _header("By Topic", "Choose a theme. Receive a verse that speaks to it.")

    TOPIC_ICONS = {
        "Faith": "🙏", "Anxiety": "☁", "Purpose": "🎯", "Strength": "⚡",
        "Hope": "🌅", "Love": "❤", "Wisdom": "🦉", "Forgiveness": "🕊",
        "Gratitude": "🌻", "Peace": "☮", "Courage": "🦁", "Healing": "💚",
    }

    # 4-column topic grid
    grid = st.columns(4)
    for i, t in enumerate(ALL_TOPICS):
        with grid[i % 4]:
            active = st.session_state.sel_topic == t
            if st.button(
                f"{TOPIC_ICONS.get(t, '·')} {t}",
                key=f"tp_{t}",
                type="primary" if active else "secondary",
                use_container_width=True,
            ):
                st.session_state.sel_topic = t
                # Clear stale devotional from a different topic
                if (st.session_state.devotional or {}).get("topic") != t:
                    st.session_state.devotional = None

    st.markdown("<br>", unsafe_allow_html=True)
    sel = st.session_state.sel_topic

    if st.button(f"Open a {sel} Devotional", type="primary", use_container_width=True):
        try:
            with st.spinner(""):
                verse = get_verse_for_topic(sel, translation)
            _generate(verse, sel, include_prayer=include_prayer, include_memory=include_memory)
        except Exception as e:
            st.error(f"Could not load verse: {e}")

    d = st.session_state.get("devotional")
    if d and d.get("topic") == sel:
        render_scripture(d)
        render_devotional_body(d, key_suffix="topic")
        render_social_export(d)


# ══════════════════════════════════════════════════════════════
#  🗺  JOURNEY
# ══════════════════════════════════════════════════════════════
elif mode == "journey":
    _header("7-Day Journey", "A guided week of scripture on one theme.")

    jt   = st.selectbox("", JOURNEY_TOPICS,
                        format_func=lambda x: f"7 Days of {x}",
                        label_visibility="collapsed")
    plan = JOURNEYS[jt]

    st.markdown("<br>", unsafe_allow_html=True)

    # Day strip
    day_cols = st.columns(7)
    sel_day  = st.session_state.get("journey_day", 1)
    for entry in plan:
        with day_cols[entry["day"] - 1]:
            active = sel_day == entry["day"]
            if st.button(
                f"{'◆' if active else '◇'} {entry['day']}",
                key=f"jd_{jt}_{entry['day']}",
                help=f"Day {entry['day']}: {entry['theme']} — {entry['ref']}",
                type="primary" if active else "secondary",
                use_container_width=True,
            ):
                st.session_state.journey_day = entry["day"]

    sel_day = st.session_state.get("journey_day", 1)
    entry   = plan[sel_day - 1]

    st.markdown(
        f'<div class="card" style="margin:var(--sp-md) 0;">'
        f'<div class="card-label">Day {sel_day} of 7</div>'
        f'<div class="card-body" style="font-family:\'Cormorant Garamond\',serif;'
        f'font-size:1.18rem;color:var(--text-prim);">{entry["theme"]}</div>'
        f'<div style="font-size:0.88rem;color:var(--text-mute);margin-top:var(--sp-xs);">'
        f'{entry["ref"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if st.button(f"Open Day {sel_day} Devotional", type="primary", use_container_width=True):
        try:
            with st.spinner(""):
                verse = get_journey_verse(jt, sel_day, translation)
            _generate(verse, jt, journey_theme=entry["theme"],
                      include_prayer=include_prayer, include_memory=include_memory)
        except Exception as e:
            st.error(f"Could not load verse: {e}")

    d = st.session_state.get("devotional")
    if d and d.get("topic") == jt:
        render_scripture(d)
        render_devotional_body(d, key_suffix=f"j{sel_day}")
        render_social_export(d)


# ══════════════════════════════════════════════════════════════
#  🔍  SEARCH
# ══════════════════════════════════════════════════════════════
elif mode == "search":
    _header("Search a Verse", "Enter any Bible reference to build a devotional from it.")

    ref_col, btn_col = st.columns([4, 1])
    with ref_col:
        custom = st.text_input(
            "",
            placeholder="John 3:16  ·  Psalm 23:1  ·  Romans 8:28",
            label_visibility="collapsed",
        )
    with btn_col:
        go = st.button("Open", type="primary", use_container_width=True)

    st.markdown(
        '<div style="margin:var(--sp-xs) 0 var(--sp-md);font-size:0.72rem;'
        'color:var(--text-mute);letter-spacing:0.12em;text-transform:uppercase;'
        'font-family:\'EB Garamond\',serif;">Quick picks</div>',
        unsafe_allow_html=True,
    )
    _picks = ["Psalm 23:1", "John 3:16", "Romans 8:28", "Isaiah 40:31", "Jeremiah 29:11", "Proverbs 3:5-6"]
    pcols  = st.columns(len(_picks))
    for i, p in enumerate(_picks):
        with pcols[i]:
            if st.button(p, key=f"pick_{i}", use_container_width=True):
                custom = p
                go     = True

    if go and custom:
        if not validate_ref(custom):
            st.error("Please enter a valid reference — e.g. John 3:16 or Psalm 23:1")
        else:
            try:
                with st.spinner(""):
                    verse = fetch_verse(custom.strip(), translation)
                _generate(verse, None, include_prayer=include_prayer, include_memory=include_memory)
            except Exception as e:
                st.error(f"Could not fetch '{custom}': {e}")

    d = st.session_state.get("devotional")
    if d:
        render_scripture(d)
        render_devotional_body(d, key_suffix="search")
        render_social_export(d)


# ══════════════════════════════════════════════════════════════
#  🎙  SERMON
# ══════════════════════════════════════════════════════════════
elif mode == "sermon":
    _header("Sermon Mode", "A full outline from any verse — for pastors, youth leaders, and study groups.")

    sc1, sc2 = st.columns([3, 1])
    with sc1:
        sref = st.text_input(
            "",
            placeholder="Romans 8:28  ·  Psalm 23  ·  John 15:5",
            label_visibility="collapsed",
        )
    with sc2:
        aud = st.selectbox(
            "",
            ["congregation", "youth", "small_group"],
            format_func=lambda x: {
                "congregation": "Sunday Service",
                "youth":        "Youth Group",
                "small_group":  "Small Group",
            }[x],
            label_visibility="collapsed",
        )

    if st.button("Generate Sermon Outline", type="primary", use_container_width=True):
        if not sref or not validate_ref(sref):
            st.error("Enter a valid reference first.")
        else:
            try:
                with st.spinner(""):
                    verse = fetch_verse(sref.strip(), translation)
                with st.spinner(""):
                    s = generate_sermon(verse.get("reference",""), verse.get("text", ""), aud)
                    s["translation_id"] = verse.get("translation_id", "KJV")
                    s["text"] = verse.get("text", "")
                    st.session_state.sermon = s
            except Exception as e:
                st.error(f"Error: {e}")

    s = st.session_state.get("sermon")
    if s:
        render_scripture({
            "reference":      s.get("reference", ""),
            "text":           s.get("text", ""),
            "translation_id": s.get("translation_id", "KJV"),
        })

        st.markdown(
            f'<div class="card card-memory" style="margin-bottom:var(--sp-md);">'
            f'<div class="card-label">Sermon Title</div>'
            f'<div class="card-body">{s.get("title","")}</div>'
            f'</div>'
            f'<div class="card"><div class="card-label">Big Idea</div>'
            f'<div class="card-body">{s.get("big_idea","")}</div></div>'
            f'<div class="card"><div class="card-label">Introduction</div>'
            f'<div class="card-body">{s.get("introduction","")}</div></div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div style="margin:var(--sp-md) 0 var(--sp-sm);font-size:0.66rem;'
            'letter-spacing:0.22em;text-transform:uppercase;color:var(--gold);'
            'font-family:\'EB Garamond\',serif;">Points</div>',
            unsafe_allow_html=True,
        )
        for i, pt in enumerate(s.get("points", []), 1):
            st.markdown(
                f'<div class="sermon-point">'
                f'<div class="sermon-point-num">Point {i}</div>'
                f'<div class="sermon-point-title">{pt.get("point","")}</div>'
                f'<div class="card-body">{pt.get("explanation","")}</div>'
                f'<div class="sermon-illus">{pt.get("illustration","")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        ca, cb = st.columns(2)
        with ca:
            st.markdown(
                f'<div class="card"><div class="card-label">Conclusion</div>'
                f'<div class="card-body">{s.get("conclusion","")}</div></div>',
                unsafe_allow_html=True,
            )
        with cb:
            st.markdown(
                f'<div class="card card-prayer"><div class="card-label">Closing Prayer</div>'
                f'<div class="card-body">{s.get("closing_prayer","")}</div></div>',
                unsafe_allow_html=True,
            )

        dqs = s.get("discussion_questions", [])
        if dqs:
            _divider("Discussion")
            for i, q in enumerate(dqs, 1):
                st.markdown(
                    f'<div class="card" style="padding:var(--sp-sm) var(--sp-md);">'
                    f'<div class="card-body">'
                    f'<span style="color:var(--gold);">Q{i}.</span> {q}'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

        outline = "\n\n".join(filter(None, [
            s.get("title", ""),
            f"Big Idea: {s.get('big_idea','')}",
            f"Introduction:\n{s.get('introduction','')}",
            "\n".join([
                f"Point {i+1}: {p.get('point','')}\n{p.get('explanation','')}"
                for i, p in enumerate(s.get("points", []))
            ]),
            f"Conclusion:\n{s.get('conclusion','')}",
            f"Closing Prayer:\n{s.get('closing_prayer','')}",
        ]))
        st.download_button(
            "Download Outline", outline, "sermon.txt", "text/plain",
            use_container_width=True,
        )


# ══════════════════════════════════════════════════════════════
#  📚  STUDY
# ══════════════════════════════════════════════════════════════
elif mode == "study":
    _header("Bible Study", "Context, key words, and discussion prompts for any passage.")

    study_ref = st.text_input(
        "",
        placeholder="John 15:1-8  ·  Psalm 1  ·  Proverbs 3:5-6",
        label_visibility="collapsed",
    )

    if st.button("Generate Study Notes", type="primary", use_container_width=True):
        if not study_ref or not validate_ref(study_ref):
            st.error("Enter a valid reference.")
        else:
            try:
                with st.spinner(""):
                    verse = fetch_verse(study_ref.strip(), translation)
                with st.spinner(""):
                    ns = generate_study(verse.get("reference",""), verse.get("text", ""))
                    ns["translation_id"] = verse.get("translation_id", "KJV")
                    ns["text"] = verse.get("text", "")
                    st.session_state.study = ns
            except Exception as e:
                st.error(f"Error: {e}")

    ns = st.session_state.get("study")
    if ns:
        render_scripture({
            "reference":      ns.get("reference", ""),
            "text":           ns.get("text", ""),
            "translation_id": ns.get("translation_id", "KJV"),
        })

        st.markdown(
            f'<div class="card"><div class="card-label">Context</div>'
            f'<div class="card-body">{ns.get("context","")}</div></div>'
            f'<div class="card"><div class="card-label">Summary</div>'
            f'<div class="card-body">{ns.get("summary","")}</div></div>',
            unsafe_allow_html=True,
        )

        kw = ns.get("key_words", [])
        if kw:
            _divider("Key Words")
            for item in kw:
                st.markdown(
                    f'<div class="card" style="padding:var(--sp-sm) var(--sp-md);">'
                    f'<span style="color:var(--gold-lt);font-weight:500;">{item.get("word","")}</span>'
                    f'<span style="color:var(--text-mute);"> — </span>'
                    f'<span class="card-body">{item.get("meaning","")}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        ca, cb = st.columns(2)
        with ca:
            for lesson in ns.get("life_lessons", []):
                st.markdown(
                    f'<div class="card" style="padding:var(--sp-sm) var(--sp-md);">'
                    f'<div class="card-body">✦ {lesson}</div></div>',
                    unsafe_allow_html=True,
                )
        with cb:
            for i, prompt in enumerate(ns.get("discussion_prompts", []), 1):
                st.markdown(
                    f'<div class="card" style="padding:var(--sp-sm) var(--sp-md);">'
                    f'<div class="card-body">'
                    f'<span style="color:var(--gold);">Q{i}.</span> {prompt}'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

        if ns.get("youth_angle"):
            st.markdown(
                f'<div class="card" style="border-left:2px solid #508050;margin-top:var(--sp-sm);">'
                f'<div class="card-label" style="color:#5a9060;">Youth Connection</div>'
                f'<div class="card-body">{ns["youth_angle"]}</div></div>',
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════
#  🙏  PRAYER
# ══════════════════════════════════════════════════════════════
elif mode == "prayer":
    _header("Prayer Generator", "Scripture-grounded prayers — personal, congregational, or intercessory.")

    pc1, pc2 = st.columns([3, 1])
    with pc1:
        pref = st.text_input(
            "",
            placeholder="Philippians 4:6-7  ·  Psalm 23:1  ·  John 14:27",
            label_visibility="collapsed",
        )
    with pc2:
        ptype = st.selectbox(
            "",
            ["personal", "congregation", "intercessory"],
            format_func=lambda x: {
                "personal":     "Personal",
                "congregation": "Congregation",
                "intercessory": "Intercessory",
            }[x],
            label_visibility="collapsed",
        )

    _prayer_picks = ["Psalm 23:1", "John 14:27", "Philippians 4:6-7", "Isaiah 41:10", "Romans 8:28"]
    ppcols = st.columns(len(_prayer_picks))
    for i, p in enumerate(_prayer_picks):
        with ppcols[i]:
            if st.button(p, key=f"pp_{i}", use_container_width=True):
                pref = p

    if st.button("Write This Prayer", type="primary", use_container_width=True):
        if not pref or not validate_ref(pref):
            st.error("Enter a valid reference.")
        else:
            try:
                with st.spinner(""):
                    verse = fetch_verse(pref.strip(), translation)
                with st.spinner(""):
                    pr = generate_prayer(verse.get("reference",""), verse.get("text", ""), ptype)
                    pr["translation_id"] = verse.get("translation_id", "KJV")
                    pr["text"]           = verse.get("text", "")
                    st.session_state.prayer_result = pr
            except Exception as e:
                st.error(f"Error: {e}")

    pr = st.session_state.get("prayer_result")
    if pr:
        render_scripture({
            "reference":      pr.get("reference", ""),
            "text":           pr.get("text", ""),
            "translation_id": pr.get("translation_id", "KJV"),
        })

        full_prayer = "\n\n".join(filter(None, [
            pr.get("title", ""), pr.get("opening", ""),
            pr.get("body", ""), pr.get("declaration", ""), pr.get("closing", ""),
        ]))

        st.markdown(
            f'<div class="card card-prayer" style="padding:var(--sp-xl) clamp(1.2rem,4vw,2.2rem);">'
            f'<div class="card-label">{pr.get("title","Prayer")}</div>'
            f'<div class="card-body" style="font-size:1.14rem;line-height:1.88;">'
            f'<em>{pr.get("opening","")}</em><br><br>'
            f'{pr.get("body","")}<br><br>'
            f'<strong style="color:var(--text-prim);font-style:normal;">'
            f'{pr.get("declaration","")}</strong><br><br>'
            f'<em>{pr.get("closing","")}</em>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        st.download_button(
            "Download Prayer", full_prayer, "prayer.txt", "text/plain",
            use_container_width=True,
        )


# ══════════════════════════════════════════════════════════════
#  ⭐  SAVED
# ══════════════════════════════════════════════════════════════
elif mode == "saved":
    _header("Saved Verses", "Devotionals and verses you've kept.")

    favs = load_favorites()
    if not favs:
        _empty("☆", "Nothing saved yet.\nGenerate a devotional and tap Save to keep it here.")
    else:
        st.caption(f"{len(favs)} saved")
        for fav in reversed(favs):
            ref   = fav.get("reference", "?")
            topic = fav.get("topic", "")
            saved = fav.get("saved_at", "")
            label = f"📖 {ref}  ·  {topic}  ·  {saved}"
            with st.expander(label):
                if fav.get("text"):
                    st.markdown(f"*\"{fav['text'][:200]}\"*")
                if fav.get("explanation"):
                    st.markdown(f"**Explanation:** {fav['explanation']}")
                if fav.get("memory"):
                    st.markdown(f"**Remember:** *{fav['memory']}*")
                if st.button("Remove", key=f"rm_{ref}"):
                    remove_favorite(ref)
                    st.toast(f"Removed {ref}")


# ══════════════════════════════════════════════════════════════
#  📊  ANALYTICS
# ══════════════════════════════════════════════════════════════
elif mode == "analytics":
    _header("Analytics")

    counts  = topic_counts()
    history = load_history()
    favs    = load_favorites()

    m1, m2, m3, m4 = st.columns(4)
    for col, val, lbl in [
        (m1, str(len(history)), "Devotionals"),
        (m2, str(len(counts)),  "Topics"),
        (m3, str(len(favs)),    "Saved"),
        (m4, f"🔥 {get_streak()}", "Day Streak"),
    ]:
        with col:
            st.markdown(
                f'<div class="metric-box">'
                f'<span class="metric-num">{val}</span>'
                f'<span class="metric-lbl">{lbl}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    if counts:
        st.markdown("<br>", unsafe_allow_html=True)
        st.bar_chart(counts, use_container_width=True, color="#c8922a")
    else:
        st.markdown("<br>", unsafe_allow_html=True)
        _empty("✦", "Generate some devotionals first to see usage patterns here.")

    st.markdown("<br>", unsafe_allow_html=True)
    dl_col, clr_col = st.columns(2)
    with dl_col:
        b = history_csv_bytes()
        if b:
            st.download_button(
                "Export History CSV", b, "history.csv", "text/csv",
                use_container_width=True,
            )
    with clr_col:
        if st.button("Clear History", use_container_width=True):
            clear_history()
            st.success("History cleared.")


# ══════════════════════════════════════════════════════════════
#  📁  HISTORY
# ══════════════════════════════════════════════════════════════
elif mode == "history":
    _header("History", "Your last 30 devotionals.")

    history = load_history()
    if not history:
        _empty("✦", "No history yet.\nGenerate your first devotional to begin.")
    else:
        st.caption(f"{len(history)} total · showing last 30")
        for row in list(reversed(history))[:30]:
            ref   = row.get("reference", "?")
            topic = row.get("topic", "")
            dt    = row.get("date", "")
            with st.expander(f"{ref}  ·  {topic}  ·  {dt}"):
                # Reads 'text' — canonical key, same as storage writes
                if row.get("text"):
                    st.markdown(
                        f"*\"{row['text'][:180]}\"* ({row.get('translation','KJV')})"
                    )
                if row.get("explanation"):
                    st.markdown(f"**Explanation:** {row['explanation']}")
                if row.get("reflection"):
                    st.markdown(f"**Reflect:** {row['reflection']}")
                if row.get("memory"):
                    st.markdown(f"**Remember:** *{row['memory']}*")

        b = history_csv_bytes()
        if b:
            st.download_button(
                "Download CSV", b, "history.csv", "text/csv",
                use_container_width=True,
            )


# ══════════════════════════════════════════════════════════════
#  ⚙  CHURCH SETTINGS
#  Controlled branding personalisation — no arbitrary overrides.
# ══════════════════════════════════════════════════════════════
elif mode == "settings":
    _header("Church Settings", "Personalise the app identity for your congregation.")

    import base64
    identity = get_identity()

    # ── Church Name ────────────────────────────────────────────
    st.markdown(
        '<div class="settings-section">'
        '<div class="settings-section-title">Church Identity</div>',
        unsafe_allow_html=True,
    )

    church_name_input = st.text_input(
        "Church name",
        value=st.session_state.get("church_name", ""),
        max_chars=32,
        placeholder="e.g. Redeemed House Assembly",
        help="Displayed in the sidebar beneath the app name. Max 32 characters.",
    )

    church_subtitle_input = st.text_input(
        "Tagline / subtitle",
        value=st.session_state.get("church_subtitle", ""),
        max_chars=45,
        placeholder="e.g. Walking in Light & Truth",
        help="Optional short line below the church name. Max 45 characters.",
    )

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Logo Upload ────────────────────────────────────────────
    st.markdown(
        '<div class="settings-section">'
        '<div class="settings-section-title">Church Logo</div>',
        unsafe_allow_html=True,
    )

    logo_file = st.file_uploader(
        "Upload logo",
        type=["png", "jpg", "jpeg", "webp"],
        help="Optional. Displayed as a small circular emblem in the sidebar.",
        label_visibility="collapsed",
    )

    current_logo = st.session_state.get("logo_bytes")
    if logo_file is not None:
        new_bytes = logo_file.read()
        if len(new_bytes) <= 500_000:   # 500 KB max
            st.session_state.logo_bytes = new_bytes
            b64 = base64.b64encode(new_bytes).decode()
            st.markdown(
                f'<div style="display:flex;justify-content:center;margin:var(--sp-md) 0;">'
                f'<img src="data:image/png;base64,{b64}" '
                f'style="width:64px;height:64px;border-radius:50%;object-fit:cover;'
                f'border:1px solid var(--gold-border);" alt="Preview"></div>',
                unsafe_allow_html=True,
            )
        else:
            st.warning("Image is too large. Please use a file under 500 KB.")
    elif current_logo:
        b64 = base64.b64encode(current_logo).decode()
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:var(--sp-md);margin:var(--sp-sm) 0;">'
            f'<img src="data:image/png;base64,{b64}" '
            f'style="width:48px;height:48px;border-radius:50%;object-fit:cover;'
            f'border:1px solid var(--gold-border);" alt="Current logo">'
            f'<span style="font-family:\'EB Garamond\',serif;font-size:0.88rem;'
            f'color:var(--text-mute);font-style:italic;">Current logo</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        rc, _ = st.columns([1, 4])
        with rc:
            if st.button("Remove logo"):
                st.session_state.logo_bytes = None

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Accent Theme ───────────────────────────────────────────
    st.markdown(
        '<div class="settings-section">'
        '<div class="settings-section-title">Accent Theme</div>',
        unsafe_allow_html=True,
    )

    current_theme = st.session_state.get("accent_theme", "Gold Ember")
    _SWATCH_COLORS = {
        "Gold Ember":        "#c8922a",
        "Royal Indigo":      "#7c6fc0",
        "Ivory Dawn":        "#b8956a",
        "Crimson Covenant":  "#b05060",
        "Olive Sanctuary":   "#7a9e6a",
    }

    # Render theme cards as a 5-column button grid
    theme_cols = st.columns(5)
    for i, (tname, tcolor) in enumerate(_SWATCH_COLORS.items()):
        with theme_cols[i]:
            active = current_theme == tname
            st.markdown(
                f'<div style="text-align:center;margin-bottom:var(--sp-xs);">'
                f'<div style="width:28px;height:28px;border-radius:50%;'
                f'background:{tcolor};margin:0 auto var(--sp-xs);'
                f'border:2px solid {"#fff" if active else "transparent"};'
                f'box-shadow:{"0 0 0 2px " + tcolor if active else "none"};"></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button(
                tname,
                key=f"theme_{tname}",
                type="primary" if active else "secondary",
                use_container_width=True,
            ):
                st.session_state.accent_theme = tname
                save_identity()
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Save ───────────────────────────────────────────────────
    if st.button("Save Church Identity", type="primary", use_container_width=True):
        st.session_state.church_name     = church_name_input.strip()[:32]
        st.session_state.church_subtitle = church_subtitle_input.strip()[:45]
        save_identity()
        st.success("Church identity saved.")
        st.rerun()

    # ── Reset ──────────────────────────────────────────────────
    _divider()
    rc2, _ = st.columns([1, 3])
    with rc2:
        if st.button("Reset to defaults"):
            st.session_state.church_name     = "The Word"
            st.session_state.church_subtitle = "Daily Devotional"
            st.session_state.accent_theme    = "Gold Ember"
            st.session_state.logo_bytes      = None
            save_identity()
            st.rerun()