# ✝️ Church Devotional Platform v3

> **"The Word"** — AI-assisted digital discipleship infrastructure.
> Powered by Google Gemini 1.5 Flash + bible-api.com.

---

## What's New in v3

| Feature | Status |
|---|---|
| ☀️ Daily devotional (shared, date-deterministic) | ✅ New |
| 🗺️ 7-Day topic journeys | ✅ New |
| 🎙️ Sermon outline generator (3 audiences) | ✅ New |
| 📚 Bible study notes mode | ✅ New |
| 🙏 Prayer generator (personal / congregation / intercessory) | ✅ New |
| ⭐ Save / favorite devotionals | ✅ New |
| 🔥 Streak tracking | ✅ New |
| 📊 Analytics with clear history | ✅ New |
| ✓ Trust layer ("powered by real scripture") | ✅ New |
| 🌍 Offline daily verse cache | ✅ New |

---

## Project Structure

```
church-devotional-app/
├── app.py                          # Streamlit UI — 10 modes
├── services/
│   ├── gemini_client.py            # Gemini 1.5 Flash wrapper
│   ├── verse_service.py            # Bible API + journeys + daily verse
│   └── devotional_engine.py        # Devotional / Sermon / Prayer / Study
├── utils/
│   ├── formatters.py               # Social export (IG / WA / Twitter / TXT)
│   └── storage.py                  # History + Favorites + Analytics + Streak
├── requirements.txt
├── .env.example
└── README.md
```

---

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env       # add GEMINI_API_KEY
streamlit run app.py
```

Get your free Gemini API key: https://aistudio.google.com/app/apikey

---

## App Modes

| Mode | Description |
|---|---|
| ☀️ Today's Word | One devotional for the whole congregation, same all day, cached |
| 📖 Topic Devotional | Choose from 12 themes, get a verse + devotional |
| 🗺️ 7-Day Journey | Guided 7-day plans on Anxiety, Faith, Purpose, Strength |
| 🎙️ Sermon Mode | Full sermon outline for Sunday service, youth, or small group |
| 📚 Bible Study | Context, key words, cross-refs, discussion prompts |
| 🙏 Prayer Generator | Personal, congregation, or intercessory prayers |
| 🔍 Search Verse | Any Bible reference → instant devotional |
| ⭐ Favorites | Bookmark and revisit saved devotionals |
| 📊 Analytics | Topic frequency, streak, history export |
| 📁 History | Last 30 devotionals with full content |

---

## Daily Devotional — How It Works

`get_daily_verse()` uses an MD5 hash of the calendar date to pick a deterministic topic + verse. Every user sees the same verse on the same day, creating congregation synchronization. The result is cached in `daily_cache.json` — only one API call per day across all users on the same machine.

---

## Safety & Trust

- Bible text always from `bible-api.com` — never AI-generated
- Gemini prompt explicitly says: "NEVER invent, paraphrase, or modify Bible verses"
- Gemini safety filters set to `BLOCK_MEDIUM_AND_ABOVE`
- Trust badge on every scripture card: "✓ Scripture sourced from bible-api.com"
- Reference validation before any API call
- JSON parse failure returns safe defaults — UI never breaks

---

## Roadmap

- [ ] **Audio devotionals** — TTS integration, "listen mode" for commute/bedtime
- [ ] **Visual verse cards** — image generation with church branding
- [ ] **Social scheduling** — queue Instagram/WhatsApp posts for the week
- [ ] **Church admin panel** — pin devotional of the day, approve content
- [ ] **FastAPI + React migration** — `services/` become REST endpoints, zero logic changes

---

## Deployment

### Streamlit Cloud
```
GEMINI_API_KEY = "your_key"   # in Streamlit secrets
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```
