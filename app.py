"""
app.py — Church Devotional Platform v3
Modes: Today's Word · Topic · Journey · Sermon · Study · Prayer · Favorites · Analytics
Run: streamlit run app.py
"""

import streamlit as st
from datetime import datetime, date

from verse_service import (
    fetch_verse, get_verse_for_topic, get_random_verse,
    get_daily_verse, get_journey_verse, get_all_topics,
    validate_reference, TOPIC_JOURNEYS, JOURNEY_TOPICS,
)
from devotional_engine import (
    generate_devotional, generate_sermon_outline,
    generate_prayer, generate_study_notes,
)
from formatters import (
    format_instagram, format_whatsapp, format_twitter, format_full_text,
)
from storage import (
    save_devotional, load_history, get_history_csv_bytes,
    load_favorites, save_favorite, remove_favorite, is_favorite,
    get_cached_daily, cache_daily, get_topic_analytics, get_streak,
    clear_history,
)

# ──────────────────────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="The Word — Daily Devotional",
    page_icon="✝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────
# Session state
# ──────────────────────────────────────────────────────────────
for k, v in [
    ("devotional", None), ("sermon", None), ("prayer", None),
    ("study", None), ("reading_mode", False),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ──────────────────────────────────────────────────────────────
# Aesthetic: Warm Sanctuary — deep indigo night + gold candlelight
# Fonts: Cormorant Garamond (display) + EB Garamond (body)
# ──────────────────────────────────────────────────────────────
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,700;1,400;1,500&family=EB+Garamond:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet">

<style>
:root {
  --ink:        #f4ead7;
  --cream:      #1a1208;
  --cream-2:    #24170a;
  --gold:       #c8922a;
  --gold-lt:    #e8c56d;

  --night:      #070402;
  --night-2:    #100904;
  --night-3:    #1a1208;
  --night-4:    #2b1d0d;

  --border:     rgba(200,146,42,0.18);
  --shadow:     rgba(0,0,0,0.45);
}
html, body, [class*="css"] {
  font-family: 'EB Garamond', Georgia, serif;
  color: var(--ink);
}
.stApp {
  background:
    radial-gradient(circle at top left,
      rgba(212,175,55,0.10) 0%,
      transparent 35%),

    radial-gradient(circle at bottom right,
      rgba(255,140,0,0.08) 0%,
      transparent 35%),

    linear-gradient(
      180deg,
      #050302 0%,
      #0b0703 25%,
      #120b05 60%,
      #070402 100%
    );

  color: var(--ink);
}
.main .block-container { max-width: 920px; padding: 1.8rem 1.4rem 5rem; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: linear-gradient(175deg, var(--night) 0%, var(--night-2) 40%, var(--night-3) 100%);
  border-right: 1px solid var(--night-4);
}
[data-testid="stSidebar"] * { color: #e8d8b8 !important; }
[data-testid="stSidebar"] hr { border-color: var(--night-4) !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stRadio label { font-size: 0.95rem; }

/* ── Sidebar brand ── */
.sidebar-brand {
  text-align: center;
  padding: 1.2rem 0 0.8rem;
}
.sidebar-cross {
  font-size: 2.8rem;
  color: var(--gold);
  display: block;
  animation: glow 3s ease-in-out infinite alternate;
}
@keyframes glow {
  from { text-shadow: 0 0 8px rgba(200,146,42,0.3); }
  to   { text-shadow: 0 0 24px rgba(200,146,42,0.7), 0 0 48px rgba(200,146,42,0.2); }
}
.sidebar-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.3rem;
  font-weight: 700;
  color: #f0ddb8 !important;
  margin: 0.4rem 0 0.1rem;
  letter-spacing: 0.04em;
}
.sidebar-sub {
  font-size: 0.75rem;
  color: #907050 !important;
  font-style: italic;
}

/* ── Streak badge ── */
.streak-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: rgba(200,146,42,0.15);
  border: 1px solid rgba(200,146,42,0.3);
  border-radius: 20px;
  padding: 0.25rem 0.7rem;
  font-size: 0.82rem;
  color: var(--gold-lt) !important;
  margin: 0.5rem auto;
}

/* ── Page header ── */
.page-header { margin-bottom: 1.4rem; }
.page-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 2rem;
  font-weight: 700;
  color: #f5e8cc;
  line-height: 1.15;
  margin: 0;
}
.page-sub {
  font-family: 'EB Garamond', serif;
  font-size: 1rem;
  color: #8a6640;
  font-style: italic;
  margin-top: 0.2rem;
}

/* ── Daily banner ── */
.daily-banner {
  background: linear-gradient(135deg, var(--night) 0%, var(--night-3) 100%);
  border: 1px solid var(--night-4);
  border-radius: 14px;
  padding: 0.7rem 1.4rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.8rem;
}
.daily-date {
  font-family: 'Cormorant Garamond', serif;
  font-size: 0.82rem;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--gold);
}
.daily-label {
  font-size: 0.78rem;
  color: #705030;
  font-style: italic;
}

/* ── Scripture card ── */
.scripture-card {
  background: linear-gradient(145deg, #0e0800 0%, #1e1006 55%, #140c04 100%);
  border: 1px solid rgba(180,120,30,0.35);
  border-radius: 14px;
  padding: 2rem 2.4rem;
  margin: 1rem 0 1.6rem;
  position: relative;
  overflow: hidden;
  box-shadow: 0 12px 40px rgba(0,0,0,0.22), inset 0 1px 0 rgba(255,200,80,0.12);
  animation: fadeUp 0.5s ease both;
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
.scripture-card::before {
  content: '\u201C';
  position: absolute;
  top: -1.5rem;
  left: 1rem;
  font-family: 'Cormorant Garamond', serif;
  font-size: 10rem;
  color: rgba(200,146,42,0.08);
  line-height: 1;
  pointer-events: none;
  user-select: none;
}
.scripture-card::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--gold), transparent);
  opacity: 0.4;
}
.scripture-meta {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 0.9rem;
  flex-wrap: wrap;
}
.scripture-ref {
  font-family: 'EB Garamond', serif;
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--gold);
}
.scripture-trans {
  font-size: 0.72rem;
  color: #604020;
  border: 1px solid rgba(200,146,42,0.25);
  border-radius: 4px;
  padding: 0.05rem 0.4rem;
  font-family: monospace;
  color: #c8922a !important;
}
.topic-pill {
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #e8c56d !important;
  background: rgba(200,146,42,0.15);
  border: 1px solid rgba(200,146,42,0.3);
  border-radius: 20px;
  padding: 0.1rem 0.6rem;
}
.scripture-text {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.42rem;
  font-style: italic;
  line-height: 1.78;
  color: #f5e8cc;
}
.trust-note {
  font-size: 0.7rem;
  color: #504030;
  margin-top: 0.9rem;
  font-style: italic;
}

/* ── Content cards ── */
.card {
  background: var(--cream);
  border: 1px solid rgba(180,140,80,0.2);
  border-radius: 10px;
  padding: 1.3rem 1.5rem;
  margin: 0.6rem 0;
  box-shadow: 0 2px 10px rgba(100,60,10,0.05);
  transition: box-shadow 0.2s, transform 0.2s;
  animation: fadeUp 0.4s ease both;
}
.card:hover { box-shadow: 0 5px 20px rgba(100,60,10,0.1); transform: translateY(-1px); }
.card-label {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #9a6a20;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}
.card-body {
  font-family: 'EB Garamond', serif;
  font-size: 1.1rem;
  line-height: 1.72;
  color: var(--ink);
}

.prayer-card {
  background: linear-gradient(135deg, #f0f3ff 0%, #e8ecff 100%);
  border-color: rgba(100,120,220,0.2);
}
.prayer-card .card-label { color: #3a4a9a; }
.prayer-card .card-body  { color: #1a2060; font-style: italic; }

.memory-card {
  background: linear-gradient(135deg, #fffbee 0%, #fff6d0 100%);
  border: 1px solid rgba(200,180,40,0.35);
  text-align: center;
}
.memory-card .card-label { color: #7a5a00; justify-content: center; }
.memory-card .card-body {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.22rem;
  font-weight: 600;
  color: #4a3400;
}

/* ── Sermon cards ── */
.sermon-point {
  background: var(--cream);
  border-left: 3px solid var(--gold);
  border-radius: 0 8px 8px 0;
  padding: 1rem 1.4rem;
  margin: 0.6rem 0;
}
.sermon-point-num {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--gold);
  margin-bottom: 0.3rem;
}
.sermon-point-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--ink);
  margin-bottom: 0.4rem;
}

/* ── Journey progress ── */
.journey-day {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 0.6rem 0.8rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  margin: 0.2rem 0;
}
.journey-day:hover { background: rgba(200,146,42,0.06); }
.journey-day.active { background: rgba(200,146,42,0.12); border: 1px solid rgba(200,146,42,0.25); }
.day-circle {
  width: 32px; height: 32px;
  border-radius: 50%;
  border: 2px solid rgba(200,146,42,0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Cormorant Garamond', serif;
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--gold);
  flex-shrink: 0;
}
.day-circle.done {
  background: var(--gold);
  color: white;
  border-color: var(--gold);
}

/* ── Social export ── */
.export-box {
  background: #14100a;
  color: #ddd0b8;
  border: 1px solid #2a2010;
  border-radius: 8px;
  padding: 1rem 1.2rem;
  font-family: 'EB Garamond', serif;
  font-size: 0.96rem;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 280px;
  overflow-y: auto;
}
.char-bar { height: 3px; border-radius: 2px; margin-top: 6px; background: rgba(200,146,42,0.15); }
.char-fill { height: 100%; border-radius: 2px; background: var(--gold); transition: width 0.3s; }

/* ── Analytics metrics ── */
.metric-box {
  background: var(--cream);
  border: 1px solid rgba(180,140,80,0.2);
  border-radius: 10px;
  padding: 1.1rem;
  text-align: center;
}
.metric-num {
  font-family: 'Cormorant Garamond', serif;
  font-size: 2.6rem;
  font-weight: 700;
  color: #2a1600;
  line-height: 1;
}
.metric-lbl {
  font-size: 0.74rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #8a6640;
  margin-top: 0.3rem;
}

/* ── Fallback warning ── */
.fallback-note {
  background: #fff8e0;
  border: 1px solid #e0b840;
  border-radius: 8px;
  padding: 0.6rem 1rem;
  font-size: 0.88rem;
  color: #7a5800;
  margin-bottom: 1rem;
}

/* ── Reading mode overlay ── */
.reading-mode .sidebar-content,
.reading-mode [data-testid="stSidebar"] { display: none !important; }

/* ── Divider ── */
.fancy-divider {
  text-align: center;
  margin: 1.8rem 0 1.4rem;
  color: rgba(180,140,60,0.4);
  font-size: 0.9rem;
  letter-spacing: 0.3em;
}

/* ── Buttons ── */
.stButton > button {
  font-family: 'EB Garamond', serif;
  font-size: 1rem;
  letter-spacing: 0.02em;
  border-radius: 8px;
  transition: all 0.2s;
}
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #6a3808 0%, #9a5818 100%);
  border: 1px solid #c07830;
  color: #fff8ee !important;
}
.stButton > button[kind="primary"]:hover {
  background: linear-gradient(135deg, #7a4810 0%, #aa6828 100%);
  box-shadow: 0 4px 14px rgba(120,60,10,0.35);
  transform: translateY(-1px);
}

/* ── Hide chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
[data-testid="stDecoration"] { display: none; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    streak = get_streak()
    st.markdown(f"""
    <div class="sidebar-brand">
      <span class="sidebar-cross">✝</span>
      <div class="sidebar-title">The Word</div>
      <div class="sidebar-sub">Daily Devotional Platform</div>
      {"<div class='streak-badge'>🔥 " + str(streak) + "-day streak</div>" if streak > 0 else ""}
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    NAV_OPTIONS = [
        "☀️  Today's Word",
        "📖  Topic Devotional",
        "🗺️  7-Day Journey",
        "🎙️  Sermon Mode",
        "📚  Bible Study",
        "🙏  Prayer Generator",
        "🔍  Search Verse",
        "⭐  Favorites",
        "📊  Analytics",
        "📁  History",
    ]
    mode = st.radio("Navigate", NAV_OPTIONS, label_visibility="collapsed")

    st.divider()

    translation = st.selectbox(
        "Translation",
        ["kjv", "web", "bbe"],
        format_func=lambda x: {"kjv": "KJV — King James", "web": "WEB — World English", "bbe": "BBE — Basic English"}[x],
    )

    st.divider()

    c1, c2 = st.columns(2)
    with c1: include_prayer = st.toggle("Prayer", value=True)
    with c2: include_memory = st.toggle("Memory", value=True)

    st.divider()
    st.markdown(f"""
    <div style="font-size:0.76rem;color:#604030;text-align:center;font-style:italic;line-height:1.6;">
      {datetime.now().strftime("%A")}<br>
      {datetime.now().strftime("%B %d, %Y")}
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# Reusable renderers
# ──────────────────────────────────────────────────────────────

def render_scripture(d: dict, show_trust: bool = True):
    ref = d.get("reference","")
    verse = d.get("verse_text","")
    trans = d.get("translation_id", translation.upper())
    topic = d.get("topic","")
    journey_theme = d.get("journey_theme","")

    if d.get("_is_fallback"):
        st.markdown('<div class="fallback-note">⚠️ Bible API unreachable — showing a cached fallback verse.</div>', unsafe_allow_html=True)

    pill = f'<span class="topic-pill">{journey_theme or topic}</span>' if (topic or journey_theme) else ""
    st.markdown(f"""
    <div class="scripture-card">
      <div class="scripture-meta">
        <span class="scripture-ref">📖 {ref}</span>
        <span class="scripture-trans">{trans}</span>
        {pill}
      </div>
      <div class="scripture-text">{verse}</div>
      {"<div class='trust-note'>✓ Scripture sourced from bible-api.com — not AI-generated</div>" if show_trust else ""}
    </div>
    """, unsafe_allow_html=True)


def render_devotional_cards(d: dict, key_prefix: str = ""):
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        if d.get("explanation"):
            st.markdown(f'<div class="card"><div class="card-label">💡 Explanation</div><div class="card-body">{d["explanation"]}</div></div>', unsafe_allow_html=True)
        if d.get("application"):
            st.markdown(f'<div class="card"><div class="card-label">👣 Apply Today</div><div class="card-body">{d["application"]}</div></div>', unsafe_allow_html=True)
    with col2:
        if d.get("reflection_question"):
            st.markdown(f'<div class="card"><div class="card-label">🤔 Reflection</div><div class="card-body">{d["reflection_question"]}</div></div>', unsafe_allow_html=True)
        if d.get("prayer_prompt"):
            st.markdown(f'<div class="prayer-card card"><div class="card-label">🙏 Prayer</div><div class="card-body">{d["prayer_prompt"]}</div></div>', unsafe_allow_html=True)

    if d.get("memory_summary"):
        st.markdown(f'<div class="memory-card card"><div class="card-label">💛 Memory Verse</div><div class="card-body">"{d["memory_summary"]}"</div></div>', unsafe_allow_html=True)

    # Favorite button
    ref = d.get("reference","")
    fav = is_favorite(ref)
    fav_col, _ = st.columns([1, 4])
    with fav_col:
        if st.button("★ Saved" if fav else "☆ Save", key=f"{key_prefix}_fav_{ref}"):
            if fav:
                remove_favorite(ref)
                st.toast(f"Removed from favorites.")
            else:
                save_favorite(d)
                st.toast(f"⭐ {ref} saved to favorites!")
            st.rerun()


def render_social_export(d: dict):
    st.markdown('<div class="fancy-divider">✦ &nbsp; Share This Devotional &nbsp; ✦</div>', unsafe_allow_html=True)
    t1, t2, t3, t4 = st.tabs(["📷 Instagram", "💬 WhatsApp", "🐦 Twitter / X", "📄 Full Text"])
    with t1:
        ig = format_instagram(d)
        st.markdown(f'<div class="export-box">{ig}</div>', unsafe_allow_html=True)
        pct = min(len(ig)/2200, 1)
        st.markdown(f'<div class="char-bar"><div class="char-fill" style="width:{pct*100:.1f}%"></div></div>', unsafe_allow_html=True)
        st.caption(f"{len(ig)} / 2,200")
        st.download_button("⬇️ Download", ig, "instagram.txt", "text/plain", use_container_width=True)
    with t2:
        wa = format_whatsapp(d)
        st.markdown(f'<div class="export-box">{wa}</div>', unsafe_allow_html=True)
        st.download_button("⬇️ Download", wa, "whatsapp.txt", "text/plain", use_container_width=True)
    with t3:
        tw = format_twitter(d)
        over = len(tw) > 280
        st.markdown(f'<div class="export-box">{tw}</div>', unsafe_allow_html=True)
        st.markdown(f'<span style="font-size:0.8rem;color:{"#e04040" if over else "#60a060"}">{len(tw)}/280</span>', unsafe_allow_html=True)
        st.download_button("⬇️ Download", tw, "tweet.txt", "text/plain", use_container_width=True)
    with t4:
        full = format_full_text(d)
        st.text_area("", full, height=260, label_visibility="collapsed")
        st.download_button("⬇️ Download .txt", full, "devotional.txt", "text/plain", use_container_width=True)


def _gen_devotional(verse: dict, topic: str, journey_theme: str = None):
    with st.spinner("✍️ Crafting your devotional..."):
        d = generate_devotional(
            verse_reference=verse["reference"],
            verse_text=verse["text"],
            topic=topic,
            include_prayer=include_prayer,
            include_memory=include_memory,
            journey_theme=journey_theme,
        )
        d["translation_id"] = verse.get("translation_id", translation.upper())
        d["_is_fallback"] = verse.get("_is_fallback", False)
        st.session_state.devotional = d
        save_devotional(d)


# ══════════════════════════════════════════════════════════════
# MODE: Today's Word
# ══════════════════════════════════════════════════════════════
if mode == "☀️  Today's Word":
    st.markdown(f"""
    <div class="page-header">
      <div class="daily-banner">
        <span style="font-size:1.4rem;">☀️</span>
        <div>
          <div class="daily-date">{datetime.now().strftime("%A, %B %d, %Y")}</div>
          <div class="daily-label">Today's devotional is the same for everyone — come back tomorrow for a new word.</div>
        </div>
      </div>
      <div class="page-title">Today's Word</div>
    </div>
    """, unsafe_allow_html=True)

    # Load from cache or generate fresh
    cached = get_cached_daily()
    if cached:
        d = cached
        # Show cached without regenerating
        render_scripture(d)
        if not d.get("explanation"):
            # Verse cached but no devotional yet — generate
            verse = {"reference": d["reference"], "text": d["verse_text"], "translation_id": d.get("translation_id", "KJV")}
            _gen_devotional(verse, d.get("topic","General"))
            d = st.session_state.devotional
        render_devotional_cards(d, key_prefix="today")
        render_social_export(d)
    else:
        if st.button("☀️ Load Today's Devotional", type="primary", use_container_width=True):
            try:
                with st.spinner("📖 Selecting today's verse..."):
                    verse, topic = get_daily_verse(translation)
                cache_daily(verse, topic)
                _gen_devotional(verse, topic)
            except Exception as e:
                st.error(f"❌ {e}")

        if st.session_state.devotional:
            d = st.session_state.devotional
            render_scripture(d)
            render_devotional_cards(d, key_prefix="today")
            render_social_export(d)


# ══════════════════════════════════════════════════════════════
# MODE: Topic Devotional
# ══════════════════════════════════════════════════════════════
elif mode == "📖  Topic Devotional":
    st.markdown('<div class="page-header"><div class="page-title">📖 Topic Devotional</div><div class="page-sub">Choose a theme. Receive a scripture that speaks to it.</div></div>', unsafe_allow_html=True)

    ICONS = {"Faith":"🙏","Anxiety":"😮‍💨","Purpose":"🎯","Strength":"💪","Hope":"🌅","Love":"❤️",
             "Wisdom":"🦉","Forgiveness":"🕊️","Gratitude":"🌻","Peace":"☮️","Courage":"🦁","Healing":"💚"}

    if "sel_topic" not in st.session_state:
        st.session_state.sel_topic = get_all_topics()[0]

    cols = st.columns(4)
    for i, t in enumerate(get_all_topics()):
        with cols[i % 4]:
            active = st.session_state.sel_topic == t
            if st.button(f"{ICONS.get(t,'📌')} {t}", key=f"tp_{t}",
                         type="primary" if active else "secondary", use_container_width=True):
                st.session_state.sel_topic = t

    st.markdown("<br>", unsafe_allow_html=True)
    sel = st.session_state.sel_topic

    if st.button(f"Generate Devotional on '{sel}'", type="primary", use_container_width=True):
        try:
            with st.spinner(f"📖 Finding verse on {sel}..."):
                verse = get_verse_for_topic(sel, translation)
            _gen_devotional(verse, sel)
        except Exception as e:
            st.error(f"❌ {e}")

    if st.session_state.devotional and st.session_state.devotional.get("topic") == sel:
        d = st.session_state.devotional
        render_scripture(d)
        render_devotional_cards(d, key_prefix="topic")
        render_social_export(d)


# ══════════════════════════════════════════════════════════════
# MODE: 7-Day Journey
# ══════════════════════════════════════════════════════════════
elif mode == "🗺️  7-Day Journey":
    st.markdown('<div class="page-header"><div class="page-title">🗺️ 7-Day Journey</div><div class="page-sub">A guided week of scripture on one theme.</div></div>', unsafe_allow_html=True)

    journey_topic = st.selectbox("Choose your journey", JOURNEY_TOPICS, format_func=lambda x: f"7 Days of {x}")
    plan = TOPIC_JOURNEYS[journey_topic]

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Your Journey Plan**")

    # Day selector as visual cards
    sel_day = st.session_state.get("journey_day", 1)
    day_cols = st.columns(7)
    for entry in plan:
        with day_cols[entry["day"] - 1]:
            active = sel_day == entry["day"]
            if st.button(
                f"Day {entry['day']}\n{entry['theme'][:8]}",
                key=f"jd_{entry['day']}",
                type="primary" if active else "secondary",
                use_container_width=True,
                help=f"{entry['theme']} — {entry['ref']}",
            ):
                st.session_state.journey_day = entry["day"]
                st.rerun()

    sel_day = st.session_state.get("journey_day", 1)
    entry = plan[sel_day - 1]

    st.markdown(f"""
    <div class="card" style="margin-top:1rem;">
      <div class="card-label">🗓️ Day {sel_day} — {entry['theme']}</div>
      <div class="card-body" style="font-size:0.95rem;color:#8a6640;">{entry['ref']}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button(f"📖 Generate Day {sel_day} Devotional", type="primary", use_container_width=True):
        try:
            with st.spinner(f"📖 Fetching {entry['ref']}..."):
                verse = get_journey_verse(journey_topic, sel_day, translation)
            _gen_devotional(verse, journey_topic, journey_theme=entry["theme"])
        except Exception as e:
            st.error(f"❌ {e}")

    if st.session_state.devotional:
        d = st.session_state.devotional
        if d.get("topic") == journey_topic:
            render_scripture(d)
            render_devotional_cards(d, key_prefix=f"j{sel_day}")
            render_social_export(d)


# ══════════════════════════════════════════════════════════════
# MODE: Sermon Mode
# ══════════════════════════════════════════════════════════════
elif mode == "🎙️  Sermon Mode":
    st.markdown('<div class="page-header"><div class="page-title">🎙️ Sermon Mode</div><div class="page-sub">Generate a full sermon outline from any verse — for pastors, youth leaders, and study coordinators.</div></div>', unsafe_allow_html=True)

    sc1, sc2 = st.columns([3, 1])
    with sc1:
        sermon_ref = st.text_input("Verse reference", placeholder="e.g.  Romans 8:28  ·  Psalm 23  ·  John 15:5", label_visibility="collapsed")
    with sc2:
        audience = st.selectbox("Audience", ["congregation","youth","small_group"],
            format_func=lambda x: {"congregation":"Sunday Service","youth":"Youth Group","small_group":"Small Group"}[x],
            label_visibility="collapsed")

    if st.button("🎙️ Generate Sermon Outline", type="primary", use_container_width=True):
        if not sermon_ref:
            st.warning("Enter a verse reference first.")
        elif not validate_reference(sermon_ref):
            st.error("Invalid reference format. Try: 'Romans 8:28' or 'Psalm 23:1'")
        else:
            try:
                with st.spinner("📖 Fetching verse..."):
                    verse = fetch_verse(sermon_ref.strip(), translation)
                with st.spinner("✍️ Building sermon outline..."):
                    s = generate_sermon_outline(verse["reference"], verse["text"], audience)
                    s["translation_id"] = verse.get("translation_id", translation.upper())
                    s["verse_text"] = verse["text"]
                    st.session_state.sermon = s
            except Exception as e:
                st.error(f"❌ {e}")

    s = st.session_state.sermon
    if s:
        render_scripture({"reference": s["reference"], "verse_text": s["verse_text"],
                          "translation_id": s.get("translation_id","KJV")})

        st.markdown(f"""
        <div class="card">
          <div class="card-label">🎯 Big Idea</div>
          <div class="card-body" style="font-size:1.18rem;font-weight:600;font-family:'Cormorant Garamond',serif;">{s.get('title','')}</div>
          <div class="card-body" style="margin-top:0.5rem;color:#5a3a10;">{s.get('big_idea','')}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="card"><div class="card-label">🎤 Introduction</div><div class="card-body">{s.get("introduction","")}</div></div>', unsafe_allow_html=True)

        st.markdown("**Sermon Points**")
        for i, pt in enumerate(s.get("points", []), 1):
            st.markdown(f"""
            <div class="sermon-point">
              <div class="sermon-point-num">Point {i}</div>
              <div class="sermon-point-title">{pt.get('point','')}</div>
              <div class="card-body">{pt.get('explanation','')}</div>
              <div style="font-size:0.9rem;color:#7a5a30;margin-top:0.4rem;font-style:italic;">💡 {pt.get('illustration','')}</div>
            </div>
            """, unsafe_allow_html=True)

        themes = s.get("key_themes", [])
        if themes:
            pills = " ".join([f'<span class="topic-pill" style="margin:0.1rem;">{t}</span>' for t in themes])
            st.markdown(f"<div style='margin:0.8rem 0;'>{pills}</div>", unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f'<div class="card"><div class="card-label">🏁 Conclusion</div><div class="card-body">{s.get("conclusion","")}</div></div>', unsafe_allow_html=True)
        with col_b:
            st.markdown(f'<div class="prayer-card card"><div class="card-label">🙏 Closing Prayer</div><div class="card-body">{s.get("prayer_close","")}</div></div>', unsafe_allow_html=True)

        dq = s.get("discussion_questions", [])
        if dq:
            st.markdown("**Discussion Questions**")
            for i, q in enumerate(dq, 1):
                st.markdown(f'<div class="card" style="padding:0.8rem 1.2rem;"><div class="card-body"><span style="color:var(--gold);font-weight:600;">Q{i}.</span> {q}</div></div>', unsafe_allow_html=True)

        full_sermon = f"SERMON OUTLINE\n{'='*44}\n{s.get('title','')}\n{s['reference']}\n\nBIG IDEA: {s.get('big_idea','')}\n\nINTRODUCTION:\n{s.get('introduction','')}\n\n"
        for i, pt in enumerate(s.get("points",[]),1):
            full_sermon += f"POINT {i}: {pt.get('point','')}\n{pt.get('explanation','')}\nIllustration: {pt.get('illustration','')}\n\n"
        full_sermon += f"CONCLUSION:\n{s.get('conclusion','')}\n\nCLOSING PRAYER:\n{s.get('prayer_close','')}\n"
        st.download_button("⬇️ Download Sermon Outline", full_sermon, "sermon_outline.txt", "text/plain", use_container_width=True)


# ══════════════════════════════════════════════════════════════
# MODE: Bible Study
# ══════════════════════════════════════════════════════════════
elif mode == "📚  Bible Study":
    st.markdown('<div class="page-header"><div class="page-title">📚 Bible Study Mode</div><div class="page-sub">Context, key words, cross-references and discussion prompts.</div></div>', unsafe_allow_html=True)

    study_ref = st.text_input("Enter a verse or passage", placeholder="e.g.  John 15:1-8  ·  Psalm 1  ·  Proverbs 3:5-6", label_visibility="collapsed")

    if st.button("📚 Generate Study Notes", type="primary", use_container_width=True):
        if not study_ref or not validate_reference(study_ref):
            st.error("Enter a valid Bible reference.")
        else:
            try:
                with st.spinner("📖 Fetching passage..."):
                    verse = fetch_verse(study_ref.strip(), translation)
                with st.spinner("🔍 Generating study notes..."):
                    notes = generate_study_notes(verse["reference"], verse["text"])
                    notes["translation_id"] = verse.get("translation_id", translation.upper())
                    notes["verse_text"] = verse["text"]
                    st.session_state.study = notes
            except Exception as e:
                st.error(f"❌ {e}")

    ns = st.session_state.study
    if ns:
        render_scripture({"reference": ns["reference"], "verse_text": ns["verse_text"],
                          "translation_id": ns.get("translation_id","KJV")})

        st.markdown(f'<div class="card"><div class="card-label">📜 Context</div><div class="card-body">{ns.get("context","")}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="card"><div class="card-label">📝 Summary</div><div class="card-body">{ns.get("summary","")}</div></div>', unsafe_allow_html=True)

        kw = ns.get("key_words", [])
        if kw:
            st.markdown("**Key Words**")
            for item in kw:
                st.markdown(f'<div class="card" style="padding:0.7rem 1.2rem;"><span style="color:var(--gold);font-weight:600;">{item.get("word","")}</span> — <span class="card-body">{item.get("meaning","")}</span></div>', unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            ll = ns.get("life_lessons", [])
            if ll:
                st.markdown("**Life Lessons**")
                for l in ll:
                    st.markdown(f'<div class="card" style="padding:0.7rem 1.2rem;"><div class="card-body">✦ {l}</div></div>', unsafe_allow_html=True)
        with col_b:
            dp = ns.get("discussion_prompts", [])
            if dp:
                st.markdown("**Discussion Prompts**")
                for i, p in enumerate(dp, 1):
                    st.markdown(f'<div class="card" style="padding:0.7rem 1.2rem;"><div class="card-body"><span style="color:var(--gold);">Q{i}.</span> {p}</div></div>', unsafe_allow_html=True)

        ya = ns.get("youth_angle","")
        if ya:
            st.markdown(f'<div class="card" style="border-top:3px solid #60a060;"><div class="card-label" style="color:#2a7a2a;">⚡ Youth Connection</div><div class="card-body">{ya}</div></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# MODE: Prayer Generator
# ══════════════════════════════════════════════════════════════
elif mode == "🙏  Prayer Generator":
    st.markdown('<div class="page-header"><div class="page-title">🙏 Prayer Generator</div><div class="page-sub">Generate scripture-grounded prayers for personal use, congregation, or intercession.</div></div>', unsafe_allow_html=True)

    pc1, pc2 = st.columns([3, 1])
    with pc1:
        prayer_ref = st.text_input("Verse reference", placeholder="e.g.  Philippians 4:6-7  ·  Psalm 23:1", label_visibility="collapsed")
    with pc2:
        prayer_type = st.selectbox("Type", ["personal","congregation","intercessory"],
            format_func=lambda x: {"personal":"Personal","congregation":"Congregation","intercessory":"Intercessory"}[x],
            label_visibility="collapsed")

    # Quick verse picks
    st.markdown("**Quick verse picks:**")
    quick_cols = st.columns(5)
    quick_picks = ["Psalm 23:1","John 14:27","Philippians 4:6-7","Isaiah 41:10","Romans 8:28"]
    for i, qp in enumerate(quick_picks):
        with quick_cols[i]:
            if st.button(qp, key=f"qp_{i}", use_container_width=True):
                prayer_ref = qp

    if st.button("🙏 Generate Prayer", type="primary", use_container_width=True):
        if not prayer_ref or not validate_reference(prayer_ref):
            st.error("Enter a valid Bible reference.")
        else:
            try:
                with st.spinner("📖 Fetching verse..."):
                    verse = fetch_verse(prayer_ref.strip(), translation)
                with st.spinner("🙏 Writing your prayer..."):
                    p = generate_prayer(verse["reference"], verse["text"], prayer_type)
                    p["translation_id"] = verse.get("translation_id", translation.upper())
                    p["verse_text"] = verse["text"]
                    st.session_state.prayer = p
            except Exception as e:
                st.error(f"❌ {e}")

    pr = st.session_state.prayer
    if pr:
        render_scripture({"reference": pr["reference"], "verse_text": pr["verse_text"],
                          "translation_id": pr.get("translation_id","KJV")})

        full_prayer = "\n\n".join([
            pr.get("title",""),
            pr.get("opening",""),
            pr.get("body",""),
            pr.get("declaration",""),
            pr.get("closing",""),
        ])

        st.markdown(f"""
        <div class="prayer-card card">
          <div class="card-label">🙏 {pr.get("title","Prayer")}</div>
          <div class="card-body" style="font-size:1.15rem;line-height:1.85;">
            <em>{pr.get("opening","")}</em><br><br>
            {pr.get("body","")}<br><br>
            <strong>{pr.get("declaration","")}</strong><br><br>
            <em>{pr.get("closing","")}</em>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.download_button("⬇️ Download Prayer", full_prayer, "prayer.txt", "text/plain", use_container_width=True)


# ══════════════════════════════════════════════════════════════
# MODE: Search Verse
# ══════════════════════════════════════════════════════════════
elif mode == "🔍  Search Verse":
    st.markdown('<div class="page-header"><div class="page-title">🔍 Search a Verse</div><div class="page-sub">Enter any Bible reference to build a devotional from it.</div></div>', unsafe_allow_html=True)

    sr_col, btn_col = st.columns([4, 1])
    with sr_col:
        custom_ref = st.text_input("Reference", placeholder="John 3:16  ·  Psalm 23:1  ·  Romans 8:28", label_visibility="collapsed")
    with btn_col:
        search_btn = st.button("🔍 Search", type="primary", use_container_width=True)

    suggestions = ["Psalm 23:1","John 3:16","Romans 8:28","Isaiah 40:31","Jeremiah 29:11","Proverbs 3:5-6"]
    s_cols = st.columns(len(suggestions))
    for i, s in enumerate(suggestions):
        with s_cols[i]:
            if st.button(s, key=f"sg_{i}", use_container_width=True):
                custom_ref = s
                search_btn = True

    if search_btn and custom_ref:
        if not validate_reference(custom_ref):
            st.error("Invalid format. Try 'John 3:16' or 'Psalm 23:1'")
        else:
            try:
                with st.spinner(f"📖 Fetching {custom_ref}..."):
                    verse = fetch_verse(custom_ref.strip(), translation)
                _gen_devotional(verse, topic=None)
            except Exception as e:
                st.error(f"❌ Could not fetch '{custom_ref}': {e}")

    if st.session_state.devotional:
        d = st.session_state.devotional
        render_scripture(d)
        render_devotional_cards(d, key_prefix="search")
        render_social_export(d)


# ══════════════════════════════════════════════════════════════
# MODE: Favorites
# ══════════════════════════════════════════════════════════════
elif mode == "⭐  Favorites":
    st.markdown('<div class="page-header"><div class="page-title">⭐ Saved Favorites</div><div class="page-sub">Verses and devotionals you\'ve bookmarked.</div></div>', unsafe_allow_html=True)

    favs = load_favorites()
    if not favs:
        st.info("No favorites yet. Generate a devotional and tap ☆ Save to bookmark it.")
    else:
        st.caption(f"{len(favs)} saved")
        for fav in reversed(favs):
            with st.expander(f"📖 {fav.get('reference','?')}  ·  {fav.get('topic','?')}  ·  {fav.get('saved_at','')}"):
                st.markdown(f"**Verse:** _{fav.get('verse_text','')}_ ")
                if fav.get("explanation"):
                    st.markdown(f"**Explanation:** {fav['explanation']}")
                if fav.get("reflection_question"):
                    st.markdown(f"**Reflection:** {fav['reflection_question']}")
                if fav.get("memory_summary"):
                    st.markdown(f"**Memory:** _{fav['memory_summary']}_")
                if st.button(f"🗑️ Remove", key=f"unfav_{fav.get('reference','')}"):
                    remove_favorite(fav.get("reference",""))
                    st.rerun()


# ══════════════════════════════════════════════════════════════
# MODE: Analytics
# ══════════════════════════════════════════════════════════════
elif mode == "📊  Analytics":
    st.markdown('<div class="page-header"><div class="page-title">📊 Analytics</div><div class="page-sub">Platform usage at a glance.</div></div>', unsafe_allow_html=True)

    analytics = get_topic_analytics()
    history = load_history()
    favs = load_favorites()
    streak = get_streak()

    m1, m2, m3, m4 = st.columns(4)
    for col, val, lbl in [
        (m1, str(len(history)), "Devotionals"),
        (m2, str(len(analytics)), "Topics Used"),
        (m3, str(len(favs)), "Favorites"),
        (m4, f"🔥 {streak}", "Day Streak"),
    ]:
        with col:
            st.markdown(f'<div class="metric-box"><div class="metric-num">{val}</div><div class="metric-lbl">{lbl}</div></div>', unsafe_allow_html=True)

    if analytics:
        st.markdown("<br>**Topic Frequency**")
        st.bar_chart(analytics, use_container_width=True, color="#c8922a")
    else:
        st.info("Generate some devotionals first.")

    st.markdown("<br>", unsafe_allow_html=True)
    col_dl, col_clr = st.columns(2)
    with col_dl:
        csv_bytes = get_history_csv_bytes()
        if csv_bytes:
            st.download_button("⬇️ Export History CSV", csv_bytes, "history.csv", "text/csv", use_container_width=True)
    with col_clr:
        if st.button("🗑️ Clear All History", use_container_width=True):
            clear_history()
            st.success("History cleared.")
            st.rerun()


# ══════════════════════════════════════════════════════════════
# MODE: History
# ══════════════════════════════════════════════════════════════
elif mode == "📁  History":
    st.markdown('<div class="page-header"><div class="page-title">📁 History</div><div class="page-sub">Your last 30 generated devotionals.</div></div>', unsafe_allow_html=True)

    history = load_history()
    if not history:
        st.info("No history yet. Generate your first devotional!")
    else:
        st.caption(f"{len(history)} total · showing last 30")
        for row in list(reversed(history))[:30]:
            with st.expander(f"📖 {row.get('reference','?')}  ·  {row.get('topic','?')}  ·  {row.get('date','')}"):
                st.markdown(f"**Verse:** _{row.get('verse_text','')}_ ({row.get('translation','KJV')})")
                if row.get("explanation"):
                    st.markdown(f"**Explanation:** {row['explanation']}")
                if row.get("reflection_question"):
                    st.markdown(f"**Reflection:** {row['reflection_question']}")
                if row.get("application"):
                    st.markdown(f"**Apply:** {row['application']}")
                if row.get("memory_summary"):
                    st.markdown(f"**Memory:** _{row['memory_summary']}_")
        csv_bytes = get_history_csv_bytes()
        st.download_button("⬇️ Download All (CSV)", csv_bytes, "devotional_history.csv", "text/csv", use_container_width=True)
