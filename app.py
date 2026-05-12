"""
app.py — The Word  |  Church Devotional Platform
A sacred reading space. Calm. Intentional. Immersive.

Run:  streamlit run app.py
Env:  GEMINI_API_KEY  (in .env or Streamlit secrets)
"""

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
    "devotional":    None,            # active devotional dict
    "sermon":        None,            # active sermon dict
    "prayer_result": None,            # active prayer dict
    "study":         None,            # active study dict
    "journey_day":   1,               # journey day selector
    "sel_topic":     ALL_TOPICS[0],   # topic selector
    "mode":          "today",         # active nav section key
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ══════════════════════════════════════════════════════════════
#  DESIGN SYSTEM — Cathedral Minimalism v2
#  Warm charcoal (not pure black), layered surfaces, gold glow.
#  Fully themed Streamlit widgets. Button-based sidebar nav.
# ══════════════════════════════════════════════════════════════
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;0,700;1,300;1,400;1,600&family=EB+Garamond:ital,wght@0,400;0,500;1,400;1,500&display=swap" rel="stylesheet">

<style>
/* ═══════════════════════════════════════════════════════════
   1. DESIGN TOKENS
   Warm charcoal palette — cathedral minimalism, not AMOLED black.
   ═══════════════════════════════════════════════════════════ */
:root {
  /* ── Surface stack: 5 clearly-separable warm charcoal tones ── */
  --bg:          #17130f;   /* page background — warm near-black    */
  --bg-raised:   #1e1912;   /* sidebar, slightly lifted             */
  --bg-card:     #252018;   /* card surface — visible on background  */
  --bg-card-h:   #2d2820;   /* card hover                           */
  --bg-input:    #1e1912;   /* inputs, selects                      */
  --bg-dropdown: #26201a;   /* dropdown/popover panels              */
  --bg-dropdown-h:#302820;  /* dropdown item hover                  */

  /* ── Gold system ── */
  --gold:        #c8922a;
  --gold-lt:     #daa84a;
  --gold-dim:    rgba(200, 146, 42, 0.09);
  --gold-glow:   rgba(200, 146, 42, 0.05);
  --gold-border: rgba(200, 146, 42, 0.18);
  --gold-hi:     rgba(200, 146, 42, 0.30);

  /* ── Typography scale ── */
  --text-prim:   #ede2cc;   /* headings, scripture — warm cream     */
  --text-body:   #c8b896;   /* body copy — readable warm            */
  --text-sec:    #9a8464;   /* secondary — sidebar nav labels       */
  --text-mute:   #5e4e36;   /* metadata, footnotes                  */
  --text-prayer: #b8c4ec;   /* prayer card text                     */

  /* ── Spacing ── */
  --sp-2xs: 0.2rem;
  --sp-xs:  0.35rem;
  --sp-sm:  0.6rem;
  --sp-md:  1rem;
  --sp-lg:  1.5rem;
  --sp-xl:  2rem;
  --sp-2xl: 3rem;

  /* ── Shape ── */
  --r-xs:   4px;
  --r-sm:   6px;
  --r-md:   10px;
  --r-lg:   14px;
  --r-pill: 9999px;

  /* ── Motion ── */
  --t-fast: 0.14s ease;
  --t-med:  0.24s ease;

  /* ── Shadows ── */
  --sh-card:  0 2px 16px rgba(0,0,0,0.30);
  --sh-scrip: 0 6px 36px rgba(0,0,0,0.42);
}

/* ═══════════════════════════════════════════════════════════
   2. BASE RESET + BODY
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

/* App background — subtle warm radial glow top-left */
.stApp {
  background:
    radial-gradient(ellipse 90% 50% at 8% 0%, rgba(200,146,42,0.04) 0%, transparent 60%),
    radial-gradient(ellipse 60% 40% at 92% 100%, rgba(38,44,90,0.05) 0%, transparent 60%),
    var(--bg);
  min-height: 100vh;
}

/* Main content area — centred, comfortable reading width */
.main .block-container {
  max-width: 880px;
  padding: var(--sp-xl) var(--sp-lg) 6rem;
  margin: 0 auto;
}

/* ═══════════════════════════════════════════════════════════
   3. SIDEBAR — warm charcoal, slightly deeper than main content
   ═══════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
  background-color: var(--bg-raised);
  background-image:
    linear-gradient(180deg,
      rgba(200,146,42,0.025) 0%,
      transparent 40%
    );
  border-right: 1px solid var(--gold-border);
}

/* Remove default Streamlit sidebar padding so our nav fills edge-to-edge */
[data-testid="stSidebar"] > div:first-child {
  padding: 0 !important;
}

/* ── Brand block ── */
.sidebar-brand {
  padding: 1.4rem 1.2rem 1rem;
  text-align: center;
  border-bottom: 1px solid var(--gold-border);
  margin-bottom: 0.5rem;
}
.sidebar-symbol {
  display: block;
  font-size: 1.4rem;
  color: var(--gold);
  letter-spacing: 0.55em;
  animation: ember 5s ease-in-out infinite alternate;
}
.sidebar-name {
  display: block;
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.35rem;
  font-weight: 600;
  color: var(--text-prim);
  letter-spacing: 0.04em;
  margin-top: 0.45rem;
  line-height: 1;
}
.sidebar-tagline {
  display: block;
  font-family: 'EB Garamond', serif;
  font-size: 0.66rem;
  color: var(--text-mute);
  letter-spacing: 0.16em;
  text-transform: uppercase;
  margin-top: 0.35rem;
}
.sidebar-streak {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  margin-top: 0.6rem;
  padding: 0.18rem 0.7rem;
  background: var(--gold-dim);
  border: 1px solid var(--gold-hi);
  border-radius: var(--r-pill);
  font-family: 'EB Garamond', serif;
  font-size: 0.75rem;
  color: var(--gold-lt);
}

/* ── Nav section group labels ── */
.nav-group {
  padding: 0.9rem 1rem 0.2rem;
  font-family: 'EB Garamond', serif;
  font-size: 0.6rem;
  font-weight: 600;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--text-mute);
}

/* ── Nav items — button-based, styled as premium rail items ── */
/* Outer wrapper div that carries active class */
.nav-item > div > button,
.nav-active > div > button {
  width: 100% !important;
  text-align: left !important;
  justify-content: flex-start !important;
  border-radius: var(--r-sm) !important;
  border: none !important;
  padding: 0.48rem 1rem !important;
  font-family: 'EB Garamond', serif !important;
  font-size: 0.96rem !important;
  letter-spacing: 0.01em !important;
  line-height: 1.3 !important;
  min-height: unset !important;
  transition: background var(--t-fast), color var(--t-fast), border-left-color var(--t-fast) !important;
  border-left: 2px solid transparent !important;
  background: transparent !important;
  color: var(--text-sec) !important;
  box-shadow: none !important;
}
.nav-item > div > button:hover {
  background: var(--gold-dim) !important;
  color: var(--text-body) !important;
  border-left-color: rgba(200,146,42,0.35) !important;
}
.nav-active > div > button {
  background: rgba(200,146,42,0.10) !important;
  color: var(--gold-lt) !important;
  border-left-color: var(--gold) !important;
}
.nav-active > div > button:hover {
  background: rgba(200,146,42,0.14) !important;
}

/* Nav container padding */
.nav-section {
  padding: 0 0.6rem 0.4rem;
}

/* Sidebar settings area */
.sidebar-settings {
  padding: 0.6rem 1rem 0.4rem;
}
.sidebar-settings-label {
  font-family: 'EB Garamond', serif;
  font-size: 0.62rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--text-mute);
  margin-bottom: 0.3rem;
  display: block;
}
.sidebar-date {
  font-family: 'EB Garamond', serif;
  font-size: 0.72rem;
  color: var(--text-mute);
  text-align: center;
  font-style: italic;
  line-height: 1.8;
  padding: 0.6rem 1rem 1rem;
}

/* ─── Override Streamlit's sidebar button styles so they don't fight ours ─── */
[data-testid="stSidebar"] .stButton > button {
  background: transparent !important;
  border: none !important;
  border-left: 2px solid transparent !important;
  border-radius: var(--r-sm) !important;
  color: var(--text-sec) !important;
  font-family: 'EB Garamond', serif !important;
  font-size: 0.96rem !important;
  text-align: left !important;
  justify-content: flex-start !important;
  width: 100% !important;
  min-height: unset !important;
  padding: 0.48rem 1rem !important;
  line-height: 1.3 !important;
  letter-spacing: 0.01em !important;
  box-shadow: none !important;
  transition: background var(--t-fast), color var(--t-fast), border-left-color var(--t-fast) !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: var(--gold-dim) !important;
  color: var(--text-body) !important;
  border-left-color: rgba(200,146,42,0.35) !important;
  transform: none !important;
}
[data-testid="stSidebar"] .stButton > button:active {
  transform: none !important;
}

/* Sidebar selectbox */
[data-testid="stSidebar"] .stSelectbox > div > div {
  background: var(--bg-card) !important;
  border: 1px solid var(--gold-border) !important;
  border-radius: var(--r-sm) !important;
  color: var(--text-body) !important;
  font-family: 'EB Garamond', serif !important;
  font-size: 0.92rem !important;
}
[data-testid="stSidebar"] .stSelectbox label {
  font-family: 'EB Garamond', serif !important;
  font-size: 0.62rem !important;
  letter-spacing: 0.15em !important;
  text-transform: uppercase !important;
  color: var(--text-mute) !important;
}
[data-testid="stSidebar"] hr {
  border: none !important;
  border-top: 1px solid var(--gold-border) !important;
  margin: 0.4rem 1rem !important;
  opacity: 1 !important;
}
[data-testid="stSidebar"] .stToggle label {
  font-family: 'EB Garamond', serif !important;
  font-size: 0.9rem !important;
  color: var(--text-sec) !important;
}

/* ═══════════════════════════════════════════════════════════
   4. TYPOGRAPHY SYSTEM
   Hierarchical scale using clamp() for fluid responsiveness.
   ═══════════════════════════════════════════════════════════ */

/* Page titles */
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

/* Date ribbon */
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
   5. SCRIPTURE BLOCK — emotional centrepiece
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
/* Decorative opening quote */
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
/* Bottom shimmer */
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
   6. CONTENT CARDS — clearly visible on warm-charcoal background
   ═══════════════════════════════════════════════════════════ */
.card {
  background: var(--bg-card);
  border: 1px solid var(--gold-border);
  border-radius: var(--r-md);
  padding: var(--sp-lg) clamp(0.9rem, 2.5vw, 1.55rem);
  margin-bottom: var(--sp-sm);
  transition: border-color var(--t-fast), background var(--t-fast), box-shadow var(--t-fast);
  animation: rise 0.38s cubic-bezier(0.22,1,0.36,1) both;
}
.card:hover {
  border-color: var(--gold-hi);
  background: var(--bg-card-h);
  box-shadow: 0 3px 16px rgba(200,146,42,0.06);
}
.card-label {
  font-family: 'EB Garamond', serif;
  font-size: 0.62rem;
  font-weight: 600;
  letter-spacing: 0.25em;
  text-transform: uppercase;
  color: var(--gold);
  opacity: 0.85;
  margin-bottom: 0.55rem;
  display: block;
}
.card-body {
  font-family: 'EB Garamond', serif;
  font-size: clamp(1rem, 2.4vw, 1.1rem);
  line-height: 1.78;
  color: var(--text-body);
}

/* Prayer variant — indigo tint for visual distinction */
.card-prayer {
  background: rgba(34, 40, 80, 0.50);
  border-color: rgba(80, 100, 210, 0.18);
}
.card-prayer .card-label { color: #8892d0; opacity: 1; }
.card-prayer .card-body  { color: var(--text-prayer); font-style: italic; }

/* Memory verse — gold tint, centred */
.card-memory {
  background: linear-gradient(
    135deg, rgba(200,146,42,0.08) 0%, rgba(20,14,8,0.45) 100%
  );
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

/* ── API quota / error notice — elegant, not alarming ── */
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
.api-notice-icon {
  font-size: 1rem;
  color: var(--gold);
  flex-shrink: 0;
  margin-top: 0.1rem;
  opacity: 0.7;
}
.api-notice-body {
  font-family: 'EB Garamond', serif;
  font-size: 0.94rem;
  line-height: 1.6;
  color: var(--text-sec);
}
.api-notice-body strong {
  color: var(--gold-lt);
  font-weight: 600;
  display: block;
  margin-bottom: 0.2rem;
}

/* ── Fallback verse notice ── */
.fallback-note {
  background: rgba(110, 80, 10, 0.18);
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
.sermon-point-num {
  font-family: 'EB Garamond', serif;
  font-size: 0.62rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--gold);
  margin-bottom: var(--sp-2xs);
}
.sermon-point-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.08rem;
  font-weight: 600;
  color: var(--text-prim);
  margin-bottom: var(--sp-xs);
}
.sermon-illus {
  font-size: 0.9rem;
  color: var(--text-mute);
  font-style: italic;
  margin-top: var(--sp-xs);
}

/* ── Analytics metrics ── */
.metric-box {
  background: var(--bg-card);
  border: 1px solid var(--gold-border);
  border-radius: var(--r-md);
  padding: var(--sp-lg) var(--sp-md);
  text-align: center;
}
.metric-num {
  display: block;
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(1.8rem, 4vw, 2.4rem);
  font-weight: 700;
  color: var(--text-prim);
  line-height: 1;
}
.metric-lbl {
  display: block;
  font-family: 'EB Garamond', serif;
  font-size: 0.65rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--text-mute);
  margin-top: 0.35rem;
}

/* ── Empty states ── */
.empty-state {
  text-align: center;
  padding: var(--sp-2xl) 0;
  opacity: 0.45;
}
.empty-state-icon {
  display: block;
  font-size: 2rem;
  color: var(--gold);
  margin-bottom: var(--sp-sm);
  animation: ember 4s ease-in-out infinite alternate;
}
.empty-state-text {
  font-family: 'EB Garamond', serif;
  font-size: 0.95rem;
  font-style: italic;
  color: var(--text-mute);
  line-height: 1.65;
  white-space: pre-line;
}

/* ── Social export ── */
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

/* ── Divider ornament ── */
.vdivide {
  display: flex; align-items: center;
  gap: var(--sp-md);
  margin: var(--sp-xl) 0 var(--sp-lg);
}
.vdivide-line { flex: 1; height: 1px; background: var(--gold-hi); opacity: 0.45; }
.vdivide-sym  { font-size: 0.62rem; letter-spacing: 0.38em; color: var(--gold); opacity: 0.55; user-select: none; }

/* ═══════════════════════════════════════════════════════════
   7. STREAMLIT WIDGET OVERRIDES
   Fully themed — no white components. Scoped selectors only.
   ═══════════════════════════════════════════════════════════ */

/* ── Buttons — main content area ── */
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
.main .stButton > button[kind="primary"]:active {
  transform: none; box-shadow: none;
}
.main .stButton > button:not([kind="primary"]) {
  background: transparent;
  border: 1px solid var(--gold-border);
  color: var(--text-sec) !important;
}
.main .stButton > button:not([kind="primary"]):hover {
  border-color: var(--gold-hi);
  background: var(--gold-glow);
}

/* ── Text inputs ── */
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
.stTextInput label {
  font-family: 'EB Garamond', serif !important;
  color: var(--text-mute) !important;
  font-size: 0.82rem !important;
}

/* ── Selectbox — the field ── */
.stSelectbox > div > div {
  background: var(--bg-input) !important;
  border: 1px solid var(--gold-border) !important;
  border-radius: var(--r-sm) !important;
  color: var(--text-body) !important;
  font-family: 'EB Garamond', serif !important;
  font-size: 0.98rem !important;
}
.stSelectbox label {
  font-family: 'EB Garamond', serif !important;
  color: var(--text-mute) !important;
  font-size: 0.82rem !important;
}

/* ── Dropdown popover — kills the white panel ── */
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
[data-baseweb="menu"] ul {
  background: var(--bg-dropdown) !important;
  padding: var(--sp-xs) !important;
}
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
/* The select value display text */
[data-baseweb="select"] [data-testid="stMarkdownContainer"] p,
[data-baseweb="select"] span {
  color: var(--text-body) !important;
  font-family: 'EB Garamond', serif !important;
}

/* ── Tabs ── */
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
.stTabs [aria-selected="true"] {
  color: var(--gold) !important;
  border-bottom-color: var(--gold);
  background: transparent;
}
.stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
  color: var(--text-sec) !important;
  background: transparent;
}
.stTabs [data-baseweb="tab-panel"] {
  padding: var(--sp-md) 0 !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--gold-border) !important;
  border-radius: var(--r-md) !important;
  margin-bottom: var(--sp-sm) !important;
}
[data-testid="stExpander"] summary {
  font-family: 'EB Garamond', serif !important;
  font-size: 0.96rem !important;
  color: var(--text-body) !important;
  padding: 0.75rem 1rem !important;
}
[data-testid="stExpander"] summary:hover { color: var(--text-prim) !important; }

/* ── Toggles ── */
.stToggle label {
  font-family: 'EB Garamond', serif !important;
  font-size: 0.9rem !important;
  color: var(--text-sec) !important;
}

/* ── Text area ── */
.stTextArea textarea {
  background: var(--bg-input) !important;
  border: 1px solid var(--gold-border) !important;
  border-radius: var(--r-sm) !important;
  color: var(--text-body) !important;
  font-family: 'EB Garamond', serif !important;
  font-size: 0.96rem !important;
}

/* ── Captions ── */
.stCaption {
  font-family: 'EB Garamond', serif !important;
  font-size: 0.8rem !important;
  color: var(--text-mute) !important;
}

/* ── Toast notifications ── */
.stToast {
  background: var(--bg-card) !important;
  border: 1px solid var(--gold-border) !important;
  color: var(--text-body) !important;
  font-family: 'EB Garamond', serif !important;
}

/* ── Streamlit default error/warning — override the red wall ── */
.stException, .stError {
  background: rgba(160, 40, 40, 0.12) !important;
  border: 1px solid rgba(200, 60, 60, 0.25) !important;
  border-radius: var(--r-sm) !important;
  color: #e8a0a0 !important;
  font-family: 'EB Garamond', serif !important;
}
.stSuccess {
  background: rgba(40,100,60,0.12) !important;
  border: 1px solid rgba(60,160,80,0.22) !important;
  border-radius: var(--r-sm) !important;
  font-family: 'EB Garamond', serif !important;
}
.stWarning {
  background: rgba(160,120,20,0.12) !important;
  border: 1px solid rgba(200,160,30,0.22) !important;
  border-radius: var(--r-sm) !important;
  font-family: 'EB Garamond', serif !important;
}

/* ── Spinner ── */
.stSpinner > div {
  border-color: var(--gold) transparent transparent !important;
}

/* ── Bar chart tinting ── */
.stVegaLiteChart { animation: fadeIn 0.4s ease both; }

/* ═══════════════════════════════════════════════════════════
   8. STREAMLIT CHROME — preserve mobile sidebar toggle
   ═══════════════════════════════════════════════════════════ */

/*
  DO NOT hide the header entirely — it contains the mobile
  hamburger menu. Instead, make it transparent.
*/
[data-testid="stHeader"] {
  background: transparent !important;
  border-bottom: none !important;
}
/* Hide toolbar (share/deploy buttons) but keep sidebar toggle */
[data-testid="stToolbar"] { display: none !important; }

/* Ensure sidebar collapse/expand button is always visible */
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {
  display: flex !important;
  visibility: visible !important;
}
button[aria-label="Open sidebar"],
button[aria-label="Close sidebar"] {
  display: flex !important;
  visibility: visible !important;
  color: var(--gold) !important;
  background: rgba(200,146,42,0.08) !important;
  border-radius: var(--r-sm) !important;
}

/* Hide decorative chrome */
[data-testid="stDecoration"] { display: none !important; }
.stDeployButton              { display: none !important; }
footer                       { display: none !important; }
#MainMenu                    { display: none !important; }

/* ═══════════════════════════════════════════════════════════
   9. ANIMATIONS
   ═══════════════════════════════════════════════════════════ */
@keyframes rise {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes ember {
  from { text-shadow: 0 0 7px  rgba(200,146,42,0.22), 0 0 16px rgba(200,146,42,0.07); }
  to   { text-shadow: 0 0 16px rgba(200,146,42,0.52), 0 0 34px rgba(200,146,42,0.16), 0 0 52px rgba(200,146,42,0.04); }
}
@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}

/* ═══════════════════════════════════════════════════════════
   10. RESPONSIVE
   ═══════════════════════════════════════════════════════════ */
@media (max-width: 768px) {
  .main .block-container {
    padding: var(--sp-md) var(--sp-sm) 5rem;
  }
  .scripture-wrap {
    padding: var(--sp-lg) var(--sp-md) var(--sp-md);
    margin-bottom: var(--sp-lg);
  }
  .card { padding: var(--sp-md); }
  .card-memory { padding: var(--sp-lg) var(--sp-md); }
  .vdivide { margin: var(--sp-lg) 0 var(--sp-md); }
}

@media (max-width: 480px) {
  .scripture-text {
    font-size: 1.2rem;
    line-height: 1.78;
  }
  .page-hd-title { font-size: 1.5rem; }
  .page-hd-sub   { font-size: 0.95rem; }
  .card-body     { font-size: 1rem; }
}
</style>
""", unsafe_allow_html=True)


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
        'Try again in a few minutes if youd prefer a freshly generated reflection.'
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
# Single entry point — no duplicated logic across modes.
# Returns the devotional dict and writes to session state.
# Does NOT call st.rerun() — the caller decides if needed.
# ─────────────────────────────────────────────────────────────
def _generate(
    verse: dict,
    topic: str,
    journey_theme: str = None,
    include_prayer: bool = True,
    include_memory: bool = True,
) -> dict:
    """
    Generate a devotional from a verse dict.
    Reads verse['text'] (canonical key).
    Writes result to st.session_state.devotional.
    Returns the generated dict.
    """
    with st.spinner(""):
        d = generate_devotional(
            reference      = verse.get("reference", ""),
            verse_text     = verse.get("text", ""),      # canonical
            topic          = topic,
            journey_theme  = journey_theme,
            include_prayer = include_prayer,
            include_memory = include_memory,
        )
        d["translation_id"] = verse.get("translation_id", "KJV")
        d["_fallback"]      = verse.get("_fallback", False)
        st.session_state.devotional = d
        save_devotional(d)
    return d


# ══════════════════════════════════════════════════════════════
#  SIDEBAR — Button-rail navigation, no radio circles
# ══════════════════════════════════════════════════════════════

# Nav definition: (key, label) — key stored in session_state.mode
_NAV_GROUPS = [
    ("Daily", [
        ("today",   "☀  Today's Word"),
    ]),
    ("Devotionals", [
        ("topic",   "📖  By Topic"),
        ("journey", "🗺  7-Day Journey"),
        ("search",  "🔍  Search a Verse"),
    ]),
    ("Tools", [
        ("sermon",  "🎙  Sermon Mode"),
        ("study",   "📚  Bible Study"),
        ("prayer",  "🙏  Prayer"),
    ]),
    ("Library", [
        ("saved",     "⭐  Saved"),
        ("analytics", "📊  Analytics"),
        ("history",   "📁  History"),
    ]),
]

with st.sidebar:
    # ── Brand ──
    streak = get_streak()
    streak_html = (
        f'<div class="sidebar-streak">🔥 {streak}-day streak</div>'
        if streak > 0 else ""
    )
    st.markdown(
        f'<div class="sidebar-brand">'
        f'  <span class="sidebar-symbol">✦  ✦  ✦</span>'
        f'  <span class="sidebar-name">The Word</span>'
        f'  <span class="sidebar-tagline">Daily Devotional</span>'
        f'  {streak_html}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Navigation rail ──
    # Each group renders a small uppercase label then button items.
    # Active item gets a gold left-border via CSS class on the container div.
    current = st.session_state.get("mode", "today")
    for group_label, items in _NAV_GROUPS:
        st.markdown(
            f'<div class="nav-group">{group_label}</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="nav-section">', unsafe_allow_html=True)
        for key, label in items:
            active_class = "nav-active" if current == key else "nav-item"
            st.markdown(f'<div class="{active_class}">', unsafe_allow_html=True)
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state.mode = key
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # ── Settings ──
    st.markdown('<div class="sidebar-settings">', unsafe_allow_html=True)
    st.markdown('<span class="sidebar-settings-label">Translation</span>', unsafe_allow_html=True)
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

    st.divider()

    tc, mc = st.columns(2)
    with tc: include_prayer = st.toggle("Prayer", value=True)
    with mc: include_memory = st.toggle("Memory", value=True)

    st.divider()
    st.markdown(
        f'<div class="sidebar-date">'
        f'{datetime.now().strftime("%A")}<br>{datetime.now().strftime("%B %d, %Y")}'
        f'</div>',
        unsafe_allow_html=True,
    )

# Resolve active mode from session state
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