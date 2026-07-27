# HolyHolyHoly ✦

### A digital devotional experience for daily Scripture, reflection, prayer, and spiritual growth.

HolyHolyHoly is a Streamlit-based Christian devotional application designed to create a calm, immersive, and personalised daily Bible experience.

The application combines a carefully designed devotional interface with AI-assisted content generation, curated fallback content, church identity customisation, Scripture study features, prayer, journaling, and spiritual journey tracking.

The prototype is intentionally designed to feel less like a conventional productivity dashboard and more like a **digital devotional sanctuary**.

---

## Table of Contents

* [Overview](#overview)
* [Vision](#vision)
* [Core Features](#core-features)
* [Product Philosophy](#product-philosophy)
* [AI Generation System](#ai-generation-system)
* [Fallback Architecture](#fallback-architecture)
* [Church Identity](#church-identity)
* [UI & Design System](#ui--design-system)
* [Technology Stack](#technology-stack)
* [Project Structure](#project-structure)
* [Getting Started](#getting-started)
* [Environment Configuration](#environment-configuration)
* [Running the Application](#running-the-application)
* [Gemini Integration](#gemini-integration)
* [AI Reliability & Quota Handling](#ai-reliability--quota-handling)
* [State Management](#state-management)
* [Content Architecture](#content-architecture)
* [Development Guidelines](#development-guidelines)
* [Known Limitations](#known-limitations)
* [Future Roadmap](#future-roadmap)
* [Prototype Status](#prototype-status)
* [Contributing](#contributing)
* [License](#license)

---

# Overview

HolyHolyHoly is a devotional application prototype built with **Python and Streamlit**.

Its primary purpose is to provide users with a structured spiritual experience around Scripture.

Rather than treating devotionals as simple blocks of generated text, the application attempts to create a complete daily experience consisting of:

* Scripture
* Biblical context
* Reflection
* Practical application
* Prayer
* Memory verses
* Personal spiritual tracking
* Saved devotional content
* Bible study
* Sermon-related content
* Church identity

The application can use Google's Gemini API to generate devotional content dynamically. Because AI services are inherently subject to network failures, model availability, quotas, and API errors, the application also includes a fallback content system.

The fallback system is an intentional part of the architecture rather than an error page.

The core principle is:

> **A temporary AI failure should never destroy the devotional experience.**

---

# Vision

HolyHolyHoly aims to make daily spiritual engagement feel:

* personal
* peaceful
* thoughtful
* biblically grounded
* beautiful
* consistent
* accessible

The product is not intended to feel like a generic AI wrapper.

The long-term product direction is closer to a **digital spiritual companion and church devotional platform**.

---

# Core Features

## Daily Devotional

The central experience of the application.

A devotional can contain:

* Daily theme
* Scripture reference
* Scripture text
* Biblical context
* Reflection
* Practical application
* Prayer
* Memory verse
* Additional devotional insights

The presentation is intentionally designed around reading rather than information density.

---

## AI-Assisted Devotional Generation

HolyHolyHoly can use Google's Gemini API to generate devotional content.

The AI layer is responsible for producing structured devotional material based on prompts supplied by the application.

The application does not simply display raw model output.

Generated content is expected to conform to a defined structure before being presented to the user.

---

## Curated Fallback Content

AI generation is not treated as a single point of failure.

When the AI service is unavailable or a generation fails, the application can return structured fallback content.

The fallback system is designed to ensure:

* the page still works
* users still receive devotional material
* the UI does not expose technical errors
* the application remains usable during API outages
* quota problems do not destroy the user experience

Fallback content is stored in structured form, primarily JSON-compatible objects.

---

## Bible Study

The application provides a dedicated experience for engaging with Scripture beyond the daily devotional.

The study experience can be expanded to include:

* Passage exploration
* Context
* Themes
* Questions
* Reflection prompts
* Cross-references
* Study notes

---

## Prayer

The prayer experience is designed as a dedicated space for reflection and prayer rather than simply another generated text block.

It can support:

* Prayer prompts
* Guided prayer
* Personal prayer
* Prayer themes
* Saved prayers

---

## Sermon Notes / Study

The application provides space for sermon-oriented spiritual engagement.

This creates a bridge between:

**church → sermon → personal reflection → continued study**

The long-term vision is to make sermon content reusable after the church service ends.

---

## Spiritual Journey

HolyHolyHoly includes a journey-oriented experience designed to encourage consistency.

Possible journey features include:

* Daily progress
* Streaks
* Day-by-day devotional progression
* Saved reflections
* Milestones

The purpose is not to gamify spirituality excessively.

The intention is to encourage consistent spiritual practice.

---

## Saved Devotionals

Users can preserve devotional content they want to revisit.

This transforms the application from a purely chronological feed into a personal spiritual library.

---

## Church Identity

HolyHolyHoly supports controlled church personalisation.

A church can configure elements such as:

* Church name
* Church subtitle/tagline
* Optional church logo
* Curated accent theme

The church identity is displayed within the application's sidebar.

For example:

```text
THE WORD
Daily Devotional

Redeemed House Assembly
Walking in Light & Truth
```

The goal is to make the application feel like a church's own devotional environment without allowing unrestricted customisation that could damage the design system.

---

# Product Philosophy

HolyHolyHoly follows several principles.

## 1. Content Before Complexity

The application should remain easy to understand.

Features should serve the devotional experience rather than compete with it.

---

## 2. Calm Over Clutter

The interface should feel peaceful.

Avoid:

* excessive cards
* excessive buttons
* unnecessary animations
* visual noise
* aggressive colours
* dense dashboards

---

## 3. Personalisation Without Chaos

Users and churches should be able to establish identity while the application retains a coherent visual language.

Customisation should therefore be controlled.

---

## 4. Graceful Failure

External services can fail.

The application should not.

If Gemini fails, the devotional experience should continue through fallback mechanisms.

---

## 5. AI Should Assist the Experience

AI is a content-generation mechanism, not the identity of the product.

HolyHolyHoly should still feel useful when AI is temporarily unavailable.

---

# AI Generation System

The Gemini integration is located in:

```text
services/gemini_client.py
```

The application uses Google's modern `google-genai` Python SDK.

A simplified generation flow is:

```text
User action
    ↓
Application prompt
    ↓
Gemini client
    ↓
Gemini API
    ↓
Structured response
    ↓
Validation
    ↓
Devotional UI
```

If the generation fails:

```text
Gemini API
    ↓
Failure
    ↓
Fallback engine
    ↓
Structured devotional
    ↓
Devotional UI
```

This separation is important because the UI should not need to understand the details of the AI provider.

---

# Fallback Architecture

The fallback system exists to protect the user experience.

Instead of exposing errors such as:

```text
Gemini API error
Quota exceeded
Connection failed
Model unavailable
```

the application can return valid devotional content.

The conceptual architecture is:

```text
                  ┌──────────────────┐
                  │ User requests    │
                  │ devotional       │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │ Generation       │
                  │ service          │
                  └────────┬─────────┘
                           │
                    ┌──────┴──────┐
                    │             │
                 Success        Failure
                    │             │
                    ▼             ▼
              Gemini output    Fallback
                    │             │
                    └──────┬──────┘
                           ▼
                  ┌──────────────────┐
                  │ Structured       │
                  │ devotional       │
                  └────────┬─────────┘
                           ▼
                  ┌──────────────────┐
                  │ UI presentation  │
                  └──────────────────┘
```

This architecture means the application remains functional even when external AI infrastructure is unavailable.

---

# Important AI Limitation

The fallback system should not become so dominant that Gemini is effectively unused.

If generated content consistently looks identical or highly templated, the application should be investigated to determine whether:

1. Gemini is failing frequently
2. Gemini quota is being exhausted
3. the model is returning malformed responses
4. the response parser is rejecting valid responses
5. the fallback is being triggered too aggressively
6. the AI prompt is insufficiently specific

Future versions should therefore include AI diagnostics such as:

```text
AI Requests
Successful Generations
Failed Generations
Fallback Generations
Success Rate
```

This makes it possible to distinguish an AI problem from a fallback problem.

---

# Church Identity

Church identity is deliberately controlled.

Supported customisation should include:

### Church Name

A short name displayed within the sidebar.

Recommended maximum:

```text
32 characters
```

### Church Subtitle

Optional short description or tagline.

Recommended maximum:

```text
45 characters
```

### Logo

Optional church logo displayed within a constrained container.

### Theme

The application should use curated themes rather than unrestricted colour selection.

This protects the visual identity of the product.

---

# UI & Design System

HolyHolyHoly uses a warm, cinematic visual language.

The design direction combines:

* deep brown / charcoal surfaces
* warm gold accents
* muted cream typography
* subtle indigo tones
* elegant serif typography
* restrained borders
* soft shadows
* subtle animations

The design intentionally avoids a conventional bright SaaS interface.

---

## Typography

The application uses:

### Cormorant Garamond

Primarily for:

* titles
* Scripture
* prominent devotional text
* major headings

### EB Garamond

Primarily for:

* body text
* navigation
* supporting content
* labels

The typography is intended to evoke a literary and devotional atmosphere.

---

## Sidebar

The sidebar is structured into clear sections:

1. Application identity
2. Church identity
3. Primary navigation
4. Secondary utilities
5. Progress / status

The sidebar should never become an unstructured collection of buttons.

---

## Readability

Readability is treated as a core requirement.

Avoid:

* low-contrast text
* invisible dropdown text
* white backgrounds inside dark components
* overly dim muted text
* excessive text compression
* oversized decorative elements

All interactive controls should remain visually consistent with the application theme.

---

# Technology Stack

| Technology       | Purpose                           |
| ---------------- | --------------------------------- |
| Python           | Core application language         |
| Streamlit        | Web application framework         |
| Google GenAI SDK | Gemini integration                |
| Gemini           | AI-assisted devotional generation |
| python-dotenv    | Local environment configuration   |
| JSON             | Structured fallback/content data  |
| CSS              | Application styling               |
| Google Fonts     | Typography                        |

---

# Project Structure

A representative structure is:

```text
HolyHolyHoly/
│
├── app.py
│
├── services/
│   └── gemini_client.py
│
├── data/
│   └── ...
│
├── components/
│   └── ...
│
├── assets/
│   └── ...
│
├── .streamlit/
│   └── secrets.toml
│
├── .env
├── requirements.txt
└── README.md
```

The exact structure may evolve as the prototype grows.

---

# Getting Started

## Requirements

You should have:

* Python 3.10+
* pip
* Git
* a Gemini API key
* a modern browser

---

## Clone the Repository

```bash
git clone <repository-url>
cd HolyHolyHoly
```

---

## Create a Virtual Environment

macOS / Linux:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

If the Gemini SDK is not already included:

```bash
pip install google-genai
```

---

# Environment Configuration

The application expects a Gemini API key.

## Local `.env`

Create:

```text
.env
```

and add:

```env
GEMINI_API_KEY=your_api_key_here
```

Do not commit this file.

Your `.gitignore` should contain:

```text
.env
.streamlit/secrets.toml
.venv/
__pycache__/
```

---

## Streamlit Secrets

For Streamlit deployments, use:

```text
.streamlit/secrets.toml
```

Example:

```toml
GEMINI_API_KEY = "your_api_key_here"
```

Never expose your API key in source code.

---

# Running the Application

Start Streamlit with:

```bash
streamlit run app.py
```

The application should become available at:

```text
http://localhost:8501
```

Streamlit will also display a network URL when appropriate.

---

# Gemini Integration

The Gemini client is intentionally isolated from the rest of the application.

The basic responsibility of:

```text
services/gemini_client.py
```

is to:

1. obtain the API key
2. initialise the Gemini client
3. send a prompt
4. receive a response
5. return clean text
6. raise a controlled error if generation fails

A simplified implementation resembles:

```python
from google import genai

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="MODEL_NAME",
    contents=prompt,
)

text = response.text
```

The exact model should be configured based on the currently supported Gemini models rather than hardcoded around an obsolete model.

---

# AI Reliability & Quota Handling

AI providers impose limits.

Potential causes of failure include:

* quota exhaustion
* rate limiting
* temporary API outages
* invalid API keys
* network failures
* unsupported models
* malformed responses
* provider-side errors

The application should therefore use:

### Retry logic

Retry transient failures with controlled backoff.

### Response validation

Do not blindly trust the returned text.

### Fallbacks

If Gemini cannot generate content, use curated fallback material.

### Caching

Avoid making unnecessary API calls for content that can safely be reused.

### Diagnostics

Track AI success and failure rates during development.

---

# State Management

Streamlit reruns the application whenever users interact with widgets.

Therefore, persistent UI state should be managed through:

```python
st.session_state
```

Examples include:

* church name
* church subtitle
* selected theme
* current devotional
* active navigation item
* saved content
* streak
* journey progress

Example:

```python
if "church_name" not in st.session_state:
    st.session_state.church_name = "The Brook Church"
```

State should not be recreated unnecessarily on every rerun.

---

# Content Architecture

Devotional content should be represented using structured data wherever possible.

Example:

```json
{
  "title": "Walking by Faith",
  "reference": "2 Corinthians 5:7",
  "scripture": "...",
  "reflection": "...",
  "application": "...",
  "prayer": "...",
  "memory_verse": "..."
}
```

Structured content makes it easier to:

* validate AI output
* render consistent UI
* build fallback content
* save devotionals
* export content
* migrate to a database later

---

# Development Guidelines

## Do Not Put Business Logic Everywhere

Keep responsibilities separated.

For example:

```text
app.py
    ↓
UI orchestration

services/
    ↓
External/API logic

data/
    ↓
Static/fallback content

components/
    ↓
Reusable interface elements
```

---

## Preserve the Design Language

New components should use existing design tokens rather than introducing arbitrary colours.

Prefer existing variables such as:

```css
--gold
--gold-lt
--text-prim
--text-sec
--text-body
--bg-card
--border
```

Do not introduce random colours unless there is a strong design reason.

---

## Protect Mobile Layout

Every new feature should be tested at:

* desktop width
* tablet width
* mobile width

Long church names, long devotional titles, and large Scripture passages must not break the interface.

---

# Known Limitations

This is a prototype.

Current limitations may include:

* Gemini quota restrictions
* reliance on external AI infrastructure
* local/session-based state
* limited persistence
* prototype-level authentication
* limited multi-user support
* curated rather than comprehensive fallback content
* no full production database architecture
* limited AI observability
* no complete church administration system

These limitations are expected at the prototype stage.

---

# Future Roadmap

The long-term roadmap can evolve toward:

## Phase 1 — Prototype

* [x] Streamlit application
* [x] Devotional experience
* [x] AI generation
* [x] Fallback content
* [x] Church identity
* [x] Custom visual system
* [x] Prayer experience
* [x] Bible study
* [x] Journey / streak concepts

---

## Phase 2 — Reliability

* [ ] AI generation diagnostics
* [ ] Better model selection
* [ ] Improved prompting
* [ ] Structured response validation
* [ ] Multiple fallback libraries
* [ ] Retry/backoff
* [ ] AI response caching
* [ ] Generation analytics

---

## Phase 3 — Persistence

* [ ] User accounts
* [ ] Database
* [ ] Persistent church settings
* [ ] Saved devotionals
* [ ] Saved prayers
* [ ] Personal notes
* [ ] Long-term journey history

---

## Phase 4 — Church Platform

* [ ] Church accounts
* [ ] Church administrators
* [ ] Member accounts
* [ ] Church-specific content
* [ ] Sermon management
* [ ] Church announcements
* [ ] Devotional publishing
* [ ] Church analytics

---

## Phase 5 — Production Product

Potential future capabilities:

* Web application
* Android application
* iOS application
* Push notifications
* Personal devotional plans
* Bible reading plans
* AI-assisted Bible study
* Church-wide devotional campaigns
* Multi-church architecture
* White-label deployments
* Subscription infrastructure

---

# Prototype Status

HolyHolyHoly is currently a **functional prototype**.

The purpose of this stage is to validate:

1. the devotional experience
2. the visual language
3. user interaction patterns
4. AI-assisted content generation
5. fallback reliability
6. church personalisation
7. potential church adoption

The prototype should therefore prioritise:

> **experience → validation → reliability → architecture → scale**

rather than premature infrastructure complexity.

---

# Contributing

Contributions should preserve the project's central philosophy:

> **Technology should make spiritual engagement easier, calmer, and more meaningful — not more complicated.**

When adding a feature, consider:

* Does it improve the devotional experience?
* Does it make the application easier to use?
* Does it preserve the visual language?
* Does it work when AI is unavailable?
* Does it introduce unnecessary complexity?
* Is it scalable to multiple churches later?

---

# Security

Never commit:

```text
.env
.streamlit/secrets.toml
API keys
passwords
private credentials
```

If an API key is accidentally exposed, revoke and rotate it immediately.

---

# License

Add the project's chosen license here once the licensing decision has been made.

---

# Final Note

HolyHolyHoly is being built around a simple idea:

> **A devotional should not feel like another task to complete. It should feel like a place to return to.**

The technology is there to support that experience.

The AI is there to assist.

The design is there to create atmosphere.

The church identity is there to create belonging.

And the Scripture remains at the centre.
