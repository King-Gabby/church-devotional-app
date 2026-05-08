# ✝️ Church Devotional Platform v2

> A production-ready, modular devotional generator for church congregations and media teams.
> Powered by **Google Gemini 1.5 Flash** + **bible-api.com**.

---

## Project Structure

```
church-devotional-app/
├── app.py                        # Streamlit UI — navigation, layout, rendering
├── services/
│   ├── gemini_client.py          # Gemini API wrapper (all LLM calls here)
│   ├── verse_service.py          # Bible verse fetching + topic maps
│   └── devotional_engine.py      # Devotional generation logic
├── utils/
│   ├── formatters.py             # Social media + export formatting
│   └── storage.py                # CSV history + analytics
├── requirements.txt
├── .env.example
└── README.md
```

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set your Gemini API key
```bash
cp .env.example .env
# Edit .env and add your key
```

Get a free API key at: https://aistudio.google.com/app/apikey

### 3. Run
```bash
streamlit run app.py
```

---

## Architecture Decisions

| Layer | Module | Decision |
|---|---|---|
| LLM | `gemini_client.py` | Single entry point for all Gemini calls. Exponential retry backoff. Safety filters on. Swap model in one place. |
| Verse data | `verse_service.py` | API-first, 3-tier fallback: try selected ref → try alternates → emergency constant. AI **never** touches Bible text. |
| Content gen | `devotional_engine.py` | Strict JSON contract with Gemini. Regex-strips markdown fences. Safe defaults if parse fails. AI scope explicitly limited in prompt. |
| Formatting | `formatters.py` | Zero AI calls. Pure string logic. Platform limits enforced. Easy to add new platforms. |
| Persistence | `storage.py` | Interface-first design. 4 functions. Swap CSV → SQLite by reimplementing internals only. |
| UI | `app.py` | Thin orchestration. All business logic in services/utils. Migratable to FastAPI + React with no logic changes. |

---

## Features

### Verse Selection
- **Random** — random topic + weighted verse
- **Topic-based** — 12 topics, 6 verses each, weighted random (first 2 = 2× probability)
- **Custom reference** — any valid Bible ref (e.g. `Psalm 23:1`)
- **Quick pick chips** — one-click popular verses in Search mode
- **3-tier fallback** — primary ref → alternates → hardcoded emergency

### Devotional Content (Gemini-generated)
All content is generated from a **real API verse**. Gemini only produces:
- Explanation (2–3 sentences, pastoral tone)
- Reflection question (personal)
- Application (one action today)
- Memory summary (≤12 words, optional)
- Prayer prompt (short, optional)

### Social Export
| Platform | Format | Limit |
|---|---|---|
| Instagram | Full devotional + hashtags | 2,200 chars |
| WhatsApp | Bold/italic condensed | 700 chars |
| Twitter/X | Ref + memory + tag | 280 chars |

### Analytics & History
- Topic frequency bar chart
- Total / unique / top-topic metrics
- Last 25 devotionals in expandable history
- CSV export of full history

---

## Bible Translations
| Code | Name |
|---|---|
| `kjv` | King James Version |
| `web` | World English Bible |
| `bbe` | Basic English Bible |

---

## Deployment

### Streamlit Cloud (free)
1. Push to GitHub
2. Connect at [share.streamlit.io](https://share.streamlit.io)
3. Add secret: `GEMINI_API_KEY = "your_key"`

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Migrating to FastAPI + React
- `services/` → FastAPI route handlers, no logic changes
- `utils/formatters.py` → shared utility library
- `utils/storage.py` → swap CSV implementation for PostgreSQL
- `app.py` → replace entirely with React frontend

---

## Extending Topics

In `services/verse_service.py`, add to `TOPIC_VERSES`:
```python
"Patience": [
    "Romans 5:3-4", "James 1:3-4", "Psalm 27:14",
    "Hebrews 12:1", "Isaiah 40:31", "Lamentations 3:25",
],
```

---

## Safety & Reliability
- Bible text always from `bible-api.com` — never AI-generated
- Gemini prompt explicitly forbids scripture fabrication
- Gemini safety filters set to `BLOCK_MEDIUM_AND_ABOVE` on all harm categories
- JSON parse failure returns safe fallback — UI never breaks
- API timeout: 8s for Bible API, exponential backoff for Gemini

---

## Future Roadmap
- [ ] **Daily verse scheduler** — morning email/WhatsApp push via cron + SendGrid/Twilio
- [ ] **Content approval queue** — admin marks AI output as approved before publishing
- [ ] **FastAPI backend** — services become REST endpoints, React SPA frontend
- [ ] **SQLite/Postgres** — swap `storage.py`, enable multi-user church teams
- [ ] **Multi-language** — bible-api.com supports Spanish/French; add locale param to verse service
