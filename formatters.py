"""
utils/formatters.py
Social media and export formatting. Zero AI calls.
"""

import csv, io, json
from datetime import datetime

INSTAGRAM_LIMIT = 2200
WHATSAPP_LIMIT = 700
TWITTER_LIMIT = 280

def _c(t: str) -> str:
    return t.strip().replace("\n", " ")

def _hashtags(topic: str) -> str:
    base = ["#DailyDevotional", "#BibleVerse", "#ChurchLife", "#Faith", "#WordOfGod"]
    if topic and topic != "General":
        tag = f"#{topic.replace(' ', '')}"
        if tag not in base:
            base.insert(0, tag)
    return " ".join(base[:6])

def format_instagram(d: dict) -> str:
    lines = [
        f"📖 {d['reference']}",
        f'"{_c(d["verse_text"])}"',
        "",
        f"✨ {_c(d.get('explanation',''))}",
        "",
        f"🤔 Reflect: {_c(d.get('reflection_question',''))}",
        "",
        f"👣 Apply: {_c(d.get('application',''))}",
    ]
    if d.get("memory_summary"):
        lines += ["", f"💡 Remember: {_c(d['memory_summary'])}"]
    if d.get("prayer_prompt"):
        lines += ["", f"🙏 {_c(d['prayer_prompt'])}"]
    lines += ["", _hashtags(d.get("topic", ""))]
    return "\n".join(lines)[:INSTAGRAM_LIMIT]

def format_whatsapp(d: dict) -> str:
    v = _c(d["verse_text"])
    lines = [
        f"📖 *{d['reference']}*",
        f"_{v[:200]}{'...' if len(v)>200 else ''}_",
        "",
        _c(d.get("explanation", "")),
        "",
        f"👉 {_c(d.get('application',''))}",
    ]
    return "\n".join(lines)[:WHATSAPP_LIMIT]

def format_twitter(d: dict) -> str:
    topic = d.get("topic", "")
    tag = f"#{topic.replace(' ','')}" if topic and topic != "General" else "#DailyDevotional"
    msg = _c(d.get("memory_summary") or d.get("application") or d.get("explanation", ""))
    base = f"📖 {d['reference']} | {msg} {tag} #Bible"
    if len(base) <= TWITTER_LIMIT:
        return base
    overhead = len(f"📖 {d['reference']} |  {tag} #Bible") + 4
    return f"📖 {d['reference']} | {msg[:TWITTER_LIMIT - overhead]}... {tag} #Bible"

def format_full_text(d: dict) -> str:
    lines = [
        "=" * 44,
        f"Daily Devotional — {d.get('topic','General')}",
        f"Scripture: {d['reference']} ({d.get('translation_id','KJV')})",
        "=" * 44,
        "",
        f'"{d["verse_text"]}"',
        "",
        "── EXPLANATION ──",
        d.get("explanation", ""),
        "",
        "── REFLECTION ──",
        d.get("reflection_question", ""),
        "",
        "── APPLICATION ──",
        d.get("application", ""),
    ]
    if d.get("memory_summary"):
        lines += ["", "── MEMORY VERSE ──", d["memory_summary"]]
    if d.get("prayer_prompt"):
        lines += ["", "── PRAYER ──", d["prayer_prompt"]]
    lines += ["", f"Generated: {datetime.now().strftime('%B %d, %Y')}"]
    return "\n".join(lines)

CSV_FIELDS = ["date","topic","reference","translation","verse_text","explanation",
              "reflection_question","application","memory_summary","prayer_prompt"]

def to_row(d: dict) -> dict:
    return {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "topic": d.get("topic",""), "reference": d.get("reference",""),
        "translation": d.get("translation_id","KJV"), "verse_text": d.get("verse_text",""),
        "explanation": d.get("explanation",""), "reflection_question": d.get("reflection_question",""),
        "application": d.get("application",""), "memory_summary": d.get("memory_summary",""),
        "prayer_prompt": d.get("prayer_prompt",""),
    }

def devotionals_to_csv(devotionals: list[dict]) -> str:
    if not devotionals:
        return ""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_FIELDS)
    w.writeheader()
    for d in devotionals:
        w.writerow(to_row(d))
    return buf.getvalue()
