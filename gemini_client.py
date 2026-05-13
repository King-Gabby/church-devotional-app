"""
services/gemini_client.py
Gemini client — google-genai SDK.

Quota strategy (applied in layers):
  1. max_output_tokens=350  →  cuts token spend ~60% vs uncapped
  2. Exponential backoff    →  survives brief rate spikes without crashing
  3. QUOTA_EXCEEDED sentinel→  returns gracefully, UI shows offline fallback
  4. Auth errors raised     →  surface misconfigured key immediately

Model: gemini-2.0-flash-lite  (lowest RPM/TPD consumption on free tier)
"""

import os
import time
import streamlit as st
from google import genai
from google.genai import types as genai_types

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Returned (never raised) when quota is exhausted — UI decides what to show.
QUOTA_EXCEEDED = "__quota_exceeded__"

# Hard cap on output — keeps every call well under free-tier per-request limit.
_MAX_TOKENS = 350


def _api_key() -> str:
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "GEMINI_API_KEY not set. Add it to .env or Streamlit secrets."
        )
    return key


@st.cache_resource
def _client() -> genai.Client:
    return genai.Client(api_key=_api_key())


def generate_with_gemini(prompt: str, max_tokens: int = _MAX_TOKENS) -> str:
    """
    Call Gemini 2.0 Flash Lite with a hard output token cap.

    Returns:
        str  — model response text on success
        QUOTA_EXCEEDED  — when 429/resource_exhausted, after backoff retries
    Raises:
        RuntimeError  — auth failures or unexpected errors after 3 attempts
    """
    cfg = genai_types.GenerateContentConfig(
        max_output_tokens=max_tokens,
        temperature=0.75,
    )

    last_err = None
    for attempt in range(3):
        try:
            response = _client().models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=prompt,
                config=cfg,
            )
            return response.text.strip()

        except Exception as e:
            last_err = e
            msg = str(e).lower()

            if "429" in msg or "resource_exhausted" in msg or "quota" in msg:
                if attempt < 2:
                    time.sleep(2 ** attempt)   # 1 s → 2 s
                    continue
                return QUOTA_EXCEEDED           # all retries done

            if "api_key" in msg or "invalid_api_key" in msg or "permission" in msg:
                raise RuntimeError(f"Gemini auth error — check GEMINI_API_KEY: {e}")

            if attempt < 2:
                time.sleep(2 ** attempt)
                continue

    raise RuntimeError(f"Gemini error after 3 attempts: {last_err}")