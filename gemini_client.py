"""
services/gemini_client.py
Single-responsibility Gemini 1.5 Flash client.
All LLM interaction flows through here.
"""

import os
import time
import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _get_api_key() -> str:
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
def _get_model():
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError("Run: pip install google-generativeai")
    genai.configure(api_key=_get_api_key())
    return genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={"temperature": 0.72, "top_p": 0.9, "max_output_tokens": 1500},
        safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ],
    )


def generate_with_gemini(prompt: str, retries: int = 2) -> str:
    """
    Send prompt to Gemini 1.5 Flash. Returns clean text.
    Exponential backoff on transient failure.
    """
    model = _get_model()
    last_err = None
    for attempt in range(retries + 1):
        try:
            resp = model.generate_content(prompt)
            if resp.parts:
                return resp.text.strip()
            finish = getattr(resp.candidates[0], "finish_reason", None) if resp.candidates else None
            if finish and str(finish) != "STOP":
                raise RuntimeError(f"Blocked (finish_reason={finish})")
            return resp.text.strip()
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Gemini failed after {retries + 1} attempts: {last_err}")
