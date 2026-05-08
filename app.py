"""
app.py — Church Devotional Platform
Powered by Google Gemini 1.5 Flash + bible-api.com

Run: streamlit run app.py
"""

import streamlit as st
from datetime import datetime

from verse_service import (
    fetch_verse,
    get_verse_for_topic,
    get_random_verse,
    get_all_topics,
)
from devotional_engine import generate_devotional
from formatters import (
    format_instagram,
    format_whatsapp,
    format_twitter,
    format_full_text,
)
from storage import (
    save_devotional,
    load_history,
    get_topic_analytics,
    get_history_csv_bytes,
)

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Daily Devotional",
    page_icon="✝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────
if "devotional" not in st.session_state:
    st.session_state.devotional = None
if "generating" not in st.session_state:
    st.session_state.generating = False

# ─────────────────────────────────────────────
# Custom CSS — Warm Sanctuary aesthetic
# Inspired by candlelight, stained glass, old parchment
# Font: Playfair Display (display) + Crimson Text (body)
# ─────────────────────────────────────────────
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">

<style>
  /* ── Global ── */
  html, body, [class*="css"] {
    font-family: 'Crimson Text', Georgia, serif;
    color: #2a1f14;
  }
  .main .block-container {
    max-width: 900px;
    padding: 2rem 1.5rem 4rem;
    background: transparent;
  }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1c1008 0%, #2d1a0a 50%, #1c1008 100%);
    border-right: 1px solid #5a3a1a;
  }
  [data-testid="stSidebar"] * { color: #f0ddb8 !important; }
  [data-testid="stSidebar"] .stRadio label { font-family: 'Crimson Text', serif; font-size: 1.05rem; }
  [data-testid="stSidebar"] hr { border-color: #5a3a1a !important; }

/* ── App background ── */
.stApp {
  background:
    radial-gradient(circle at top left, rgba(212, 175, 55, 0.10), transparent 40%),
    radial-gradient(circle at bottom right, rgba(255, 140, 0, 0.08), transparent 40%),
    #0f1117;

  color: #f5f5f5;
}
  /* ── Page title ── */
  .page-title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 2.2rem;
    font-weight: 700;
    color: #3d1f00;
    letter-spacing: -0.01em;
    margin-bottom: 0.2rem;
    line-height: 1.2;
  }
  .page-subtitle {
    font-family: 'Crimson Text', serif;
    font-size: 1.05rem;
    color: #8a6640;
    font-style: italic;
    margin-bottom: 1.5rem;
  }

  /* ── Scripture card ── */
  .scripture-card {
    background: linear-gradient(135deg, #1e0f00 0%, #2d1a06 60%, #1e0f00 100%);
    border: 1px solid #7a5020;
    border-radius: 12px;
    padding: 2rem 2.4rem;
    margin: 1.2rem 0 1.8rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(0,0,0,0.18), inset 0 1px 0 rgba(255,200,80,0.15);
  }
  .scripture-card::before {
    content: '\u201C';
    position: absolute;
    top: -0.3rem;
    left: 1.2rem;
    font-family: 'Playfair Display', serif;
    font-size: 8rem;
    color: rgba(180, 130, 40, 0.12);
    line-height: 1;
    pointer-events: none;
  }
  .scripture-ref {
    font-family: 'Crimson Text', serif;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    color: #c8922a;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .scripture-ref .dot { color: #5a3a1a; }
  .scripture-text {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.35rem;
    font-style: italic;
    line-height: 1.75;
    color: #f5e8cc;
  }
  .topic-pill {
    display: inline-block;
    background: rgba(180, 130, 40, 0.2);
    border: 1px solid rgba(180, 130, 40, 0.4);
    color: #e0b060 !important;
    border-radius: 20px;
    padding: 0.15rem 0.8rem;
    font-family: 'Crimson Text', serif;
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-top: 1rem;
    display: inline-block;
  }

  /* ── Content cards ── */
  .content-card {
    background: #fff9f2;
    border: 1px solid #e8d5b8;
    border-radius: 10px;
    padding: 1.4rem 1.6rem;
    margin: 0.7rem 0;
    box-shadow: 0 2px 8px rgba(100, 60, 10, 0.06);
    transition: box-shadow 0.2s ease;
  }
  .content-card:hover { box-shadow: 0 4px 16px rgba(100, 60, 10, 0.1); }
  .card-label {
    font-family: 'Crimson Text', serif;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #a07040;
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }
  .card-body {
    font-family: 'Crimson Text', serif;
    font-size: 1.08rem;
    line-height: 1.7;
    color: #2a1f14;
  }

  /* ── Prayer card ── */
  .prayer-card {
    background: linear-gradient(135deg, #f0f4ff 0%, #e8eeff 100%);
    border: 1px solid #c8d0f0;
    border-radius: 10px;
    padding: 1.4rem 1.6rem;
    margin: 0.7rem 0;
    font-style: italic;
  }
  .prayer-card .card-label { color: #4a5a90; }
  .prayer-card .card-body { color: #2a3060; }

  /* ── Memory verse ── */
  .memory-card {
    background: linear-gradient(135deg, #fffbee 0%, #fff8dc 100%);
    border: 1px solid #e8c84a;
    border-radius: 10px;
    padding: 1.2rem 1.6rem;
    margin: 0.7rem 0;
    text-align: center;
  }
  .memory-card .card-label { color: #8a6a00; justify-content: center; }
  .memory-card .card-body {
    font-family: 'Playfair Display', serif;
    font-size: 1.15rem;
    font-weight: 600;
    color: #5a3e00;
  }

  /* ── Social export box ── */
  .export-box {
    background: #1a1a2a;
    color: #e0e0f0;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    font-family: 'Crimson Text', serif;
    font-size: 0.95rem;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
    border: 1px solid #2a2a4a;
    max-height: 300px;
    overflow-y: auto;
  }
  .char-count {
    font-size: 0.78rem;
    color: #8a8aaa;
    text-align: right;
    margin-top: 0.3rem;
    font-family: monospace;
  }

  /* ── Section divider ── */
  .section-divider {
    border: none;
    border-top: 1px solid #e0c8a0;
    margin: 1.8rem 0 1.4rem;
  }

  /* ── Fallback warning ── */
  .fallback-notice {
    background: #fff8e8;
    border: 1px solid #f0c040;
    border-radius: 8px;
    padding: 0.7rem 1rem;
    font-size: 0.9rem;
    color: #7a5a00;
    margin-bottom: 1rem;
  }

  /* ── Analytics ── */
  .metric-card {
    background: #fff9f2;
    border: 1px solid #e8d5b8;
    border-radius: 10px;
    padding: 1.2rem;
    text-align: center;
  }
  .metric-value {
    font-family: 'Playfair Display', serif;
    font-size: 2.5rem;
    font-weight: 700;
    color: #3d1f00;
    line-height: 1;
    margin-bottom: 0.3rem;
  }
  .metric-label {
    font-size: 0.82rem;
    color: #8a6640;
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }

  /* ── Hide Streamlit chrome ── */
  #MainMenu, footer, header { visibility: hidden; }
  .stDeployButton { display: none; }
  [data-testid="stDecoration"] { display: none; }

  /* ── Button overrides ── */
  .stButton > button {
    font-family: 'Crimson Text', serif;
    font-size: 1rem;
    letter-spacing: 0.03em;
    border-radius: 8px;
    transition: all 0.2s ease;
  }
  .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7a4010 0%, #a05820 100%);
    border: 1px solid #c07030;
    color: #fff8ee;
  }
  .stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #8a5020 0%, #b06830 100%);
    box-shadow: 0 4px 12px rgba(120, 60, 10, 0.3);
  }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0 0.5rem;">
      <div style="font-size:2.5rem;">✝</div>
      <div style="font-family:'Playfair Display',serif; font-size:1.2rem; font-weight:700; color:#f0ddb8; margin-top:0.3rem;">Daily Devotional</div>
      <div style="font-size:0.82rem; color:#a07840; margin-top:0.2rem; font-style:italic;">Powered by Gemini</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    mode = st.radio(
        "Navigate",
        ["✨ Random Devotional", "📖 Topic Devotional", "🔍 Search Verse", "📊 Analytics", "📁 History"],
        label_visibility="collapsed",
    )

    st.divider()

    translation = st.selectbox(
        "Translation",
        ["kjv", "web", "bbe"],
        format_func=lambda x: {"kjv": "KJV — King James", "web": "WEB — World English", "bbe": "BBE — Basic English"}[x],
    )

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        include_prayer = st.toggle("Prayer", value=True, help="Include a prayer prompt")
    with col_b:
        include_memory = st.toggle("Memory", value=True, help="Include memory verse summary")

    st.divider()
    st.markdown(f"""
    <div style="font-size:0.78rem; color:#705030; text-align:center; font-style:italic;">
      {datetime.now().strftime("%A")}<br>
      {datetime.now().strftime("%B %d, %Y")}
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _run_generation(verse: dict, topic: str):
    """Fetch devotional from Gemini and cache in session state."""
    with st.spinner("✍️ Crafting your devotional..."):
        d = generate_devotional(
            verse_reference=verse["reference"],
            verse_text=verse["text"],
            topic=topic,
            include_prayer=include_prayer,
            include_memory_summary=include_memory,
        )
        d["translation_id"] = verse.get("translation_id", translation.upper())
        st.session_state.devotional = d
        save_devotional(d)


def render_devotional(d: dict):
    """Render the full devotional UI."""

    # ── Is fallback verse? ──
    if d.get("_is_fallback"):
        st.markdown("""
        <div class="fallback-notice">
          ⚠️ Bible API was unreachable. Showing a cached verse instead.
        </div>
        """, unsafe_allow_html=True)

    # ── Scripture card ──
    ref = d.get("reference", "")
    verse = d.get("verse_text", "")
    translation_id = d.get("translation_id", "KJV").upper()
    topic = d.get("topic", "General")

    st.markdown(f"""
    <div class="scripture-card">
      <div class="scripture-ref">
        📖 {ref}
        <span class="dot">·</span>
        {translation_id}
      </div>
      <div class="scripture-text">{verse}</div>
      <div class="topic-pill">{topic}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Devotional content ──
    col1, col2 = st.columns(2, gap="medium")

    with col1:
        if d.get("explanation"):
            st.markdown(f"""
            <div class="content-card">
              <div class="card-label">💡 Explanation</div>
              <div class="card-body">{d['explanation']}</div>
            </div>""", unsafe_allow_html=True)
        if d.get("application"):
            st.markdown(f"""
            <div class="content-card">
              <div class="card-label">👣 Apply Today</div>
              <div class="card-body">{d['application']}</div>
            </div>""", unsafe_allow_html=True)

    with col2:
        if d.get("reflection_question"):
            st.markdown(f"""
            <div class="content-card">
              <div class="card-label">🤔 Reflect</div>
              <div class="card-body">{d['reflection_question']}</div>
            </div>""", unsafe_allow_html=True)
        if d.get("prayer_prompt"):
            st.markdown(f"""
            <div class="prayer-card content-card">
              <div class="card-label">🙏 Prayer</div>
              <div class="card-body">{d['prayer_prompt']}</div>
            </div>""", unsafe_allow_html=True)

    if d.get("memory_summary"):
        st.markdown(f"""
        <div class="memory-card">
          <div class="card-label">💛 Memory Verse</div>
          <div class="card-body">"{d['memory_summary']}"</div>
        </div>""", unsafe_allow_html=True)

    # ── Social export ──
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family:'Playfair Display',serif; font-size:1.15rem; font-weight:700; color:#3d1f00; margin-bottom:0.8rem;">
      📤 Share This Devotional
    </div>""", unsafe_allow_html=True)

    tab_ig, tab_wa, tab_tw, tab_txt = st.tabs(["📷 Instagram", "💬 WhatsApp", "🐦 Twitter / X", "📄 Full Text"])

    with tab_ig:
        ig = format_instagram(d)
        st.markdown(f'<div class="export-box">{ig}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="char-count">{len(ig)} / 2,200 characters</div>', unsafe_allow_html=True)
        st.download_button("⬇️ Download Caption", ig, file_name="instagram.txt", mime="text/plain", use_container_width=True)

    with tab_wa:
        wa = format_whatsapp(d)
        st.markdown(f'<div class="export-box">{wa}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="char-count">{len(wa)} / 700 characters</div>', unsafe_allow_html=True)
        st.download_button("⬇️ Download Text", wa, file_name="whatsapp.txt", mime="text/plain", use_container_width=True)

    with tab_tw:
        tw = format_twitter(d)
        over = len(tw) > 280
        color = "#e05050" if over else "#50a050"
        st.markdown(f'<div class="export-box">{tw}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="char-count" style="color:{color}">{len(tw)} / 280 characters</div>', unsafe_allow_html=True)
        st.download_button("⬇️ Download Tweet", tw, file_name="tweet.txt", mime="text/plain", use_container_width=True)

    with tab_txt:
        full = format_full_text(d)
        st.text_area("", full, height=280, label_visibility="collapsed")
        st.download_button("⬇️ Download .txt", full, file_name="devotional.txt", mime="text/plain", use_container_width=True)


# ─────────────────────────────────────────────
# Mode: Random Devotional
# ─────────────────────────────────────────────
if mode == "✨ Random Devotional":
    st.markdown('<div class="page-title">✨ Random Devotional</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">A verse chosen for you, for today.</div>', unsafe_allow_html=True)

    if st.button("🎲 Generate Random Devotional", type="primary", use_container_width=True):
        try:
            with st.spinner("📖 Selecting a verse..."):
                verse, topic = get_random_verse(translation)
            _run_generation(verse, topic)
        except Exception as e:
            st.error(f"❌ Could not fetch verse: {e}")

    if st.session_state.devotional:
        render_devotional(st.session_state.devotional)


# ─────────────────────────────────────────────
# Mode: Topic Devotional
# ─────────────────────────────────────────────
elif mode == "📖 Topic Devotional":
    st.markdown('<div class="page-title">📖 Topic Devotional</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Choose a theme and receive a scripture that speaks to it.</div>', unsafe_allow_html=True)

    topics = get_all_topics()

    # Topic grid selector
    cols = st.columns(4)
    TOPIC_ICONS = {
        "Faith": "🙏", "Anxiety": "😮‍💨", "Purpose": "🎯", "Strength": "💪",
        "Hope": "🌅", "Love": "❤️", "Wisdom": "🦉", "Forgiveness": "🕊️",
        "Gratitude": "🌻", "Peace": "☮️", "Courage": "🦁", "Healing": "💚",
    }

    if "selected_topic" not in st.session_state:
        st.session_state.selected_topic = topics[0]

    for i, topic in enumerate(topics):
        with cols[i % 4]:
            icon = TOPIC_ICONS.get(topic, "📌")
            active = st.session_state.selected_topic == topic
            if st.button(
                f"{icon} {topic}",
                key=f"topic_{topic}",
                type="primary" if active else "secondary",
                use_container_width=True,
            ):
                st.session_state.selected_topic = topic

    st.markdown("<br>", unsafe_allow_html=True)
    selected = st.session_state.selected_topic

    if st.button(f"📖 Generate Devotional on '{selected}'", type="primary", use_container_width=True):
        try:
            with st.spinner(f"📖 Finding a verse on {selected}..."):
                verse = get_verse_for_topic(selected, translation)
            _run_generation(verse, selected)
        except Exception as e:
            st.error(f"❌ Error: {e}")

    if st.session_state.devotional and st.session_state.devotional.get("topic") == selected:
        render_devotional(st.session_state.devotional)


# ─────────────────────────────────────────────
# Mode: Search Verse
# ─────────────────────────────────────────────
elif mode == "🔍 Search Verse":
    st.markdown('<div class="page-title">🔍 Search a Verse</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Enter any Bible reference to build a devotional from it.</div>', unsafe_allow_html=True)

    col_ref, col_btn = st.columns([4, 1])
    with col_ref:
        custom_ref = st.text_input(
            "Reference",
            placeholder="e.g.  John 3:16   ·   Psalm 23:1   ·   Romans 8:28",
            label_visibility="collapsed",
        )
    with col_btn:
        search_btn = st.button("🔍 Search", type="primary", use_container_width=True)

    # Suggestion chips
    suggestions = ["Psalm 23:1", "John 3:16", "Romans 8:28", "Isaiah 40:31", "Jeremiah 29:11"]
    st.markdown("**Quick picks:**")
    s_cols = st.columns(len(suggestions))
    for i, s in enumerate(suggestions):
        with s_cols[i]:
            if st.button(s, key=f"sug_{s}", use_container_width=True):
                custom_ref = s
                search_btn = True

    if search_btn and custom_ref:
        try:
            with st.spinner(f"📖 Fetching {custom_ref}..."):
                verse = fetch_verse(custom_ref.strip(), translation)
            _run_generation(verse, topic=None)
        except Exception as e:
            st.error(f"❌ Could not fetch '{custom_ref}'. Check the reference format (e.g. 'John 3:16').\n\n_Error: {e}_")

    if st.session_state.devotional:
        render_devotional(st.session_state.devotional)


# ─────────────────────────────────────────────
# Mode: Analytics
# ─────────────────────────────────────────────
elif mode == "📊 Analytics":
    st.markdown('<div class="page-title">📊 Usage Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Insight into how your congregation uses the platform.</div>', unsafe_allow_html=True)

    analytics = get_topic_analytics()
    history = load_history()
    total = len(history)
    top_topic = max(analytics, key=analytics.get) if analytics else "—"
    unique_refs = len({r.get("reference") for r in history}) if history else 0

    m1, m2, m3 = st.columns(3)
    for col, val, label in [
        (m1, str(total), "Devotionals Generated"),
        (m2, str(len(analytics)), "Topics Explored"),
        (m3, top_topic, "Most Popular Topic"),
    ]:
        with col:
            st.markdown(f"""
            <div class="metric-card">
              <div class="metric-value">{val}</div>
              <div class="metric-label">{label}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if analytics:
        st.markdown("**Topic Frequency**")
        st.bar_chart(analytics, use_container_width=True, color="#a05820")
    else:
        st.info("Generate some devotionals first to see analytics here.")

    if history:
        st.markdown("<br>", unsafe_allow_html=True)
        csv_bytes = get_history_csv_bytes()
        st.download_button(
            "⬇️ Export Full History (CSV)",
            csv_bytes,
            file_name="devotional_history.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ─────────────────────────────────────────────
# Mode: History
# ─────────────────────────────────────────────
elif mode == "📁 History":
    st.markdown('<div class="page-title">📁 Devotional History</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Your last 25 generated devotionals.</div>', unsafe_allow_html=True)

    history = load_history()

    if not history:
        st.info("No devotionals saved yet. Generate some first!")
    else:
        st.caption(f"{len(history)} total · showing last 25")
        for row in list(reversed(history))[:25]:
            label = f"📖 {row.get('reference', '?')}  ·  {row.get('topic', '?')}  ·  {row.get('date', '')}"
            with st.expander(label):
                st.markdown(f"**Verse:** _{row.get('verse_text', '')}_")
                if row.get("explanation"):
                    st.markdown(f"**Explanation:** {row['explanation']}")
                if row.get("reflection_question"):
                    st.markdown(f"**Reflection:** {row['reflection_question']}")
                if row.get("application"):
                    st.markdown(f"**Application:** {row['application']}")
                if row.get("memory_summary"):
                    st.markdown(f"**Memory:** _{row['memory_summary']}_")

        st.markdown("<br>", unsafe_allow_html=True)
        csv_bytes = get_history_csv_bytes()
        st.download_button(
            "⬇️ Download All as CSV",
            csv_bytes,
            file_name="devotional_history.csv",
            mime="text/csv",
            use_container_width=True,
        )
