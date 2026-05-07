# Bluesky Post Explainer

An AI agent that explains Bluesky posts by searching the web for relevant context and returning structured, sourced bullet points.

---

## How it works

```
User pastes a Bluesky URL
        ↓
Backend fetches the post via AT Protocol API
        ↓
Agent builds a search query and retrieves web results (DuckDuckGo / Tavily)
        ↓
Gemini 2.5 Flash synthesizes context into 3–5 bullets + curated sources
        ↓
React frontend displays the explanation
```

The agent uses a **retrieval-augmented** approach: it never fabricates facts — every bullet is grounded in the retrieved search results. The model also selects which source URLs best support the explanation, rather than listing all results blindly.

---

## Stack

| Layer | Technology |
|---|---|
| LLM | Gemini 2.5 Flash (JSON mode with schema) |
| Search | DuckDuckGo (free, no key) · Tavily (optional, higher quality) |
| Post fetching | Bluesky AT Protocol public API |
| Backend | FastAPI + Pydantic |
| Frontend | React + Vite + TypeScript + Tailwind + shadcn/ui |
| Tests | pytest (backend) · Vitest + React Testing Library (frontend) |
| Eval | Keyword-matching harness with 12 labeled test cases |

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [Gemini API key](https://aistudio.google.com/apikey) (free tier)

### Backend

```bash
cd backend

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

uvicorn main:app --reload --port 8001
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

### Environment variables

```env
GEMINI_API_KEY=your_key_here   # required — get at aistudio.google.com/apikey
TAVILY_API_KEY=                # optional — falls back to DuckDuckGo if not set
```

---

## API

### `POST /explain`

**Request**
```json
{ "url": "https://bsky.app/profile/user.bsky.social/post/abc123" }
```

**Response**
```json
{
  "post": {
    "text": "I think politicians should wear sponsor jackets like F1 drivers...",
    "author": "user.bsky.social",
    "image_url": null
  },
  "bullets": [
    "This idea was popularized by comedian Robin Williams in 2009...",
    "The post uses the F1 driver sponsorship metaphor to critique...",
    "The humor lands because it makes political funding visible in a visceral way..."
  ],
  "sources": [
    "https://www.snopes.com/fact-check/robin-williams-nascar-drivers/",
    "https://www.brennancenter.org/our-work/analysis-opinion/..."
  ]
}
```

### `GET /health`

```json
{ "status": "ok" }
```

---

## Running tests

```bash
# Backend — unit + integration + API tests
cd backend
pytest

# Frontend — component + API client tests
cd frontend
npm test
```

### Test architecture

Tests follow a TDD approach — written before the implementation. Three layers:

- **Unit** (`tests/unit/`) — pure functions: URL parsing, query building, bullet formatting
- **Integration** (`tests/integration/`) — external APIs mocked with `unittest.mock`
- **API** (`tests/api/`) — full request/response via FastAPI `TestClient`

---

## Eval harness

The eval harness runs the agent against 12 labeled Bluesky posts and scores output quality.

```bash
cd eval
python run_eval.py            # all 12 cases
python run_eval.py --limit 3  # quick smoke test
```

**Scoring**: 70% keyword matching (did the bullets surface expected concepts?) + 30% bullet count validation (3–5 bullets returned?). Results are written to `eval_results.json`.

The eval acts as **acceptance tests for the agent** — analogous to end-to-end tests, but for non-deterministic AI output.

---

## Design decisions

**JSON mode over free-form text**
The agent uses Gemini's `response_mime_type: application/json` with a strict schema. This eliminates fragile text parsing and guarantees the model always returns the expected structure, regardless of how the response is phrased.

**Source curation by the model**
Instead of returning all search result URLs, the model selects 2–5 URLs that directly support its explanation. This makes sources meaningful rather than exhaustive.

**Dual search providers**
DuckDuckGo requires no API key and works out of the box. If a `TAVILY_API_KEY` is set, Tavily is used instead for higher-quality, longer snippets — better for obscure memes and slang.

**Lazy client initialization**
The Gemini client is initialized on first request, not at module import time. This prevents startup crashes when API keys are missing and makes the server more resilient.

**Frontend state machine**
App state is modeled as a discriminated union (`idle | loading | success | error`), making impossible states unrepresentable and simplifying conditional rendering.

**Image understanding**
When a post contains an image, the agent fetches it and passes the raw bytes to Gemini alongside the text. Gemini 2.5 Flash is multimodal and incorporates visual context into the explanation.
