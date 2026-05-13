"""
services/devotional_engine.py
AI generation — devotional, sermon, prayer, study.
Canonical schema: all verse dicts use key "text" (never "verse_text").

Quota strategy:
  - Slim prompts (~100 tokens input vs previous ~300)
  - max_tokens=350 enforced in gemini_client
  - QUOTA_EXCEEDED sentinel → returns offline fallback via utils.fallbacks
  - Parse failure → inline safe defaults, never raises to UI
"""
import json
import re
from typing import Optional

from gemini_client import generate_with_gemini, QUOTA_EXCEEDED
from fallbacks import get_offline_devotional


# ── Shared voice — stripped to essential constraints only ────
# Previous prompt was ~300 tokens. This is ~80 tokens.
_VOICE = (
    "You are a calm, pastoral devotional writer for a church platform. "
    "Rules: NEVER invent Bible verses (always provided). No clichés. No filler. "
    "Family-safe. Return ONLY valid JSON, no markdown fences."
)


def _parse(raw: str) -> Optional[dict]:
    cleaned = re.sub(r"^```(?:json)?\s*|```\s*$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict) and len(parsed) == 1:
            inner = next(iter(parsed.values()))
            if isinstance(inner, dict):
                return inner
        return parsed
    except Exception:
        return None


def _s(d: dict, key: str, fallback: str = "") -> str:
    return str(d.get(key) or fallback).strip()


# ─────────────────────────────────────────────────────────────
# DEVOTIONAL  — lean prompt, ~110 input tokens
# ─────────────────────────────────────────────────────────────

def generate_devotional(
    reference: str,
    verse_text: str,
    topic: Optional[str] = None,
    journey_theme: Optional[str] = None,
    include_prayer: bool = True,
    include_memory: bool = True,
) -> dict:
    context = " ".join(filter(None, [
        f"Theme: {journey_theme}." if journey_theme else "",
        f"Topic: {topic}." if (topic and not journey_theme) else "",
    ]))

    prompt = (
        f"{_VOICE}\n\n"
        f"{context}\n"
        f'Verse: {reference} — "{verse_text}"\n\n'
        "Write a devotional. Return JSON with exactly these keys:\n"
        '{"explanation":"2-3 sentences unpacking this verse in plain language. Do not restate it.",'
        '"reflection":"One specific personal question — honest and answerable.",'
        '"application":"One concrete action for today — not vague.",'
        '"memory":"10-12 words capturing the verse\'s core truth.",'
        '"prayer":"2-3 sentences. First person. Honest before reverent."}'
    )

    raw = generate_with_gemini(prompt)

    if raw == QUOTA_EXCEEDED:
        return get_offline_devotional()

    parsed = _parse(raw) or {}

    result = {
        "reference":   reference,
        "text":        verse_text,
        "topic":       topic or "General",
        "explanation": _s(parsed, "explanation", f"Sit with {reference} today."),
        "reflection":  _s(parsed, "reflection",  "What does this verse resist in you today?"),
        "application": _s(parsed, "application", "Carry one word from this verse through the day."),
        "memory":      _s(parsed, "memory",      f"The promise of {reference} is alive today."),
        "prayer":      _s(parsed, "prayer",      f"Lord, let {reference} do its work in me. Amen."),
    }
    if not include_memory: result.pop("memory", None)
    if not include_prayer: result.pop("prayer", None)
    return result


# ─────────────────────────────────────────────────────────────
# SERMON  — ~140 input tokens
# ─────────────────────────────────────────────────────────────

_AUD = {
    "congregation": "Sunday congregation — mixed ages. Warm but direct.",
    "youth":        "Teenagers (14-24). Concrete, honest, skip jargon.",
    "small_group":  "Mid-week group (6-15). Conversational. Leave space.",
}


def generate_sermon(reference: str, verse_text: str, audience: str = "congregation") -> dict:
    prompt = (
        f"{_VOICE}\n\n"
        f"Audience: {_AUD.get(audience, _AUD['congregation'])}\n"
        f'Scripture: {reference} — "{verse_text}"\n\n'
        "Sermon outline JSON with exactly:\n"
        '{"title":"honest title","big_idea":"one sentence",'
        '"introduction":"2-3 sentences opening a real tension",'
        '"points":[{"point":"title","explanation":"2-3 sentences","illustration":"1-2 sentences"},{"point":"","explanation":"","illustration":""},{"point":"","explanation":"","illustration":""}],'
        '"conclusion":"2-3 sentences",'
        '"discussion_questions":["Q1","Q2","Q3"],'
        '"closing_prayer":"2-3 sentences"}'
    )

    raw = generate_with_gemini(prompt, max_tokens=500)   # sermon needs more room

    if raw == QUOTA_EXCEEDED:
        return {
            "title": f"A Word from {reference}",
            "big_idea": "God meets us where we actually are.",
            "introduction": "Most of us arrived here carrying something. This text has something to say about that.",
            "points": [
                {"point": "What the text says", "explanation": verse_text[:140], "illustration": "One sentence changed how you saw an entire situation."},
                {"point": "What it means now", "explanation": "The original hearers faced something specific. The human need is the same.", "illustration": "Their world and ours are closer than they look."},
                {"point": "What we do with it", "explanation": "Faith without response stays inside the building.", "illustration": "A decision deferred is still a decision."},
            ],
            "conclusion": "You don't have to resolve everything today. Take one step.",
            "discussion_questions": ["What surprised you?", "Where do you see yourself?", "What will you change?"],
            "closing_prayer": "Lord, do with this what only You can. Amen.",
            "_quota_error": True,
        }

    parsed = _parse(raw) or {}
    parsed.update({"reference": reference, "text": verse_text, "audience": audience})
    return parsed


# ─────────────────────────────────────────────────────────────
# PRAYER  — ~100 input tokens
# ─────────────────────────────────────────────────────────────

_PCTX = {
    "personal":     "First person singular. Honest. Praying alone.",
    "congregation": "First person plural. Suitable to read aloud Sunday.",
    "intercessory": "On behalf of others — families, community, people in pain.",
}


def generate_prayer(reference: str, verse_text: str, prayer_type: str = "personal") -> dict:
    prompt = (
        f"{_VOICE}\n\n"
        f"Prayer type: {_PCTX.get(prayer_type, _PCTX['personal'])}\n"
        f'Verse: {reference} — "{verse_text}"\n\n'
        "Prayer JSON with exactly:\n"
        '{"title":"short honest title","opening":"one sentence addressing God",'
        '"body":"3-4 sentences from this verse specifically. Name real feelings.",'
        '"declaration":"one sentence of faith from what this verse promises",'
        '"closing":"one sentence. simple."}'
    )

    raw = generate_with_gemini(prompt)

    if raw == QUOTA_EXCEEDED:
        return {
            "title": f"Praying Through {reference}",
            "opening": "Lord —",
            "body": "I'm bringing this verse and my honest self before You. Not the version of me that has it together — the one who needs what this text promises. Meet me in the gap.",
            "declaration": f"What You promised in {reference} is still true today.",
            "closing": "In Jesus' name. Amen.",
            "_quota_error": True,
        }

    parsed = _parse(raw) or {}
    parsed.update({"reference": reference, "text": verse_text, "prayer_type": prayer_type})
    return parsed


# ─────────────────────────────────────────────────────────────
# STUDY  — ~120 input tokens
# ─────────────────────────────────────────────────────────────

def generate_study(reference: str, verse_text: str) -> dict:
    prompt = (
        f"{_VOICE}\n\n"
        f'Verse: {reference} — "{verse_text}"\n\n'
        "Study notes JSON with exactly:\n"
        '{"context":"2-3 sentences. Only background that changes how the verse lands.",'
        '"summary":"2-3 sentences. Plain English. No jargon.",'
        '"key_words":[{"word":"significant word/phrase","meaning":"original meaning and why it matters"}],'
        '"life_lessons":["lesson requiring something from reader","lesson about relationship/situation","lesson challenging an assumption"],'
        '"discussion_prompts":["question surfacing doubt/tension","question from personal experience","question about this week"],'
        '"youth_angle":"1-2 sentences. Specific situation (school/friendship/identity) where this verse is concrete."}'
    )

    raw = generate_with_gemini(prompt, max_tokens=420)

    if raw == QUOTA_EXCEEDED:
        return {
            "context": f"{reference} was written to people navigating real uncertainty — the human need is the same.",
            "summary": verse_text[:200],
            "key_words": [{"word": "the passage", "meaning": "Read it slowly a second time."}],
            "life_lessons": [
                "What we believe about God shows up in how we treat ordinary moments.",
                "Scripture was written for communities, not private consumption.",
                "Faithful response is usually something small and specific.",
            ],
            "discussion_prompts": [
                "What do you find hardest to believe here?",
                "When have you lived something close to this?",
                "What would living this look like in one relationship this week?",
            ],
            "youth_angle": "If you're under pressure to perform or fit in, this verse speaks directly to what you're actually worth — and who gets to decide.",
            "_quota_error": True,
        }

    parsed = _parse(raw) or {}
    parsed.update({"reference": reference, "text": verse_text})
    return parsed