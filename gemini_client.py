"""
services/gemini_client.py
Gemini client — google-genai SDK.
Model: gemini-2.0-flash-lite  (lowest quota consumption, fastest latency)
Strategy: exponential backoff (3 attempts), quota-aware error classification,
          st.cache_resource for the client singleton.
"""
import os
import time
import streamlit as st
from google import genai

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Sentinel returned when quota is exhausted — never raises, always returns.
QUOTA_EXCEEDED = "__quota_exceeded__"


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


def generate_with_gemini(prompt: str) -> str:
    """
    Call Gemini 2.0 Flash Lite.
    Returns: clean text string on success
             QUOTA_EXCEEDED sentinel string on 429
    Raises:  RuntimeError only on non-quota failures after all retries.
    """
    last_err = None
    for attempt in range(3):
        try:
            response = _client().models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=prompt,
            )
            return response.text.strip()

        except Exception as e:
            last_err = e
            msg = str(e).lower()

            # Quota / rate limit — back off and retry
            if "429" in msg or "resource_exhausted" in msg or "quota" in msg:
                if attempt < 2:
                    time.sleep(2 ** attempt)   # 1 s → 2 s
                    continue
                # All retries exhausted — return sentinel, don't raise
                return QUOTA_EXCEEDED

            # API key / auth errors — no point retrying
            if "api_key" in msg or "invalid" in msg or "permission" in msg:
                raise RuntimeError(f"Gemini auth error: {e}")

            # Transient errors — retry with backoff
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue

    raise RuntimeError(f"Gemini API error after 3 attempts: {last_err}")