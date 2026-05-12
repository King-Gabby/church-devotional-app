"""
utils/formatters.py
Social and export formatting. Uses canonical key "text". Zero AI calls.
"""
from datetime import datetime

IG_MAX = 2200; WA_MAX = 700; TW_MAX = 280

def _c(t: str) -> str:
    return (t or "").strip().replace("\n", " ")

def _tags(topic: str) -> str:
    base = ["#DailyDevotional", "#BibleVerse", "#ChurchLife", "#Faith", "#WordOfGod"]
    if topic and topic != "General":
        tag = f"#{topic.replace(' ','')}"
        if tag not in base:
            base.insert(0, tag)
    return " ".join(base[:6])

def format_instagram(d: dict) -> str:
    lines = [
        f"📖 {d.get('reference','')}",
        f'"{_c(d.get("text",""))}"',
        "",
        f"✨ {_c(d.get('explanation',''))}",
        "",
        f"🤔 Reflect: {_c(d.get('reflection',''))}",
        "",
        f"👣 Apply: {_c(d.get('application',''))}",
    ]
    if d.get("memory"):
        lines += ["", f"💡 Remember: {_c(d['memory'])}"]
    if d.get("prayer"):
        lines += ["", f"🙏 {_c(d['prayer'])}"]
    lines += ["", _tags(d.get("topic",""))]
    return "\n".join(lines)[:IG_MAX]

def format_whatsapp(d: dict) -> str:
    v = _c(d.get("text",""))
    lines = [
        f"📖 *{d.get('reference','')}*",
        f"_{v[:200]}{'...' if len(v)>200 else ''}_",
        "",
        _c(d.get("explanation","")),
        "",
        f"👉 {_c(d.get('application',''))}",
    ]
    return "\n".join(lines)[:WA_MAX]

def format_twitter(d: dict) -> str:
    topic = d.get("topic","")
    tag   = f"#{topic.replace(' ','')}" if topic and topic != "General" else "#DailyDevotional"
    ref   = d.get("reference","")
    msg   = _c(d.get("memory") or d.get("application") or d.get("explanation",""))
    base  = f"📖 {ref} | {msg} {tag} #Bible"
    if len(base) <= TW_MAX:
        return base
    budget = TW_MAX - len(f"📖 {ref} |  {tag} #Bible") - 4
    return f"📖 {ref} | {msg[:budget]}... {tag} #Bible"

def format_full(d: dict) -> str:
    lines = [
        "=" * 44,
        f"Daily Devotional — {d.get('topic','General')}",
        f"Scripture: {d.get('reference','')} ({d.get('translation_id','KJV')})",
        "=" * 44, "",
        f'"{d.get("text","")}"', "",
        "── EXPLANATION ──", d.get("explanation",""), "",
        "── REFLECTION ──",   d.get("reflection",""), "",
        "── APPLICATION ──",  d.get("application",""),
    ]
    if d.get("memory"):
        lines += ["", "── MEMORY ──", d["memory"]]
    if d.get("prayer"):
        lines += ["", "── PRAYER ──", d["prayer"]]
    lines += ["", f"Generated: {datetime.now().strftime('%B %d, %Y')}"]
    return "\n".join(lines)