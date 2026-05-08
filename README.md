# Bluesky Post Explainer

An AI agent that explains Bluesky posts by searching the web for relevant context and returning structured, sourced bullet points.

---

## How it works

```
User pastes a Bluesky URL
        ↓
Backend fetches the post via AT Protocol public API
        ↓
Agent builds a search query and retrieves web results (DuckDuckGo / Tavily)
        ↓
GPT-4o synthesizes context into 3–5 bullets + curated sources
        ↓
React frontend displays the explanation
```

The agent uses a **retrieval-augmented generation (RAG)** approach: every bullet is grounded in retrieved search results. The model also selects which source URLs best support the explanation, rather than listing all results blindly.

---

## Stack

| Layer | Technology |
|---|---|
| LLM | GPT-4o (structured JSON output with strict schema) |
| Search | DuckDuckGo (free, no key) · Tavily (optional, higher quality) |
| Post fetching | Bluesky AT Protocol public API |
| Backend | FastAPI + Pydantic |
| Frontend | React + Vite + TypeScript + Tailwind + shadcn/ui |
| Observability | Langfuse (optional, traces every LLM call) |
| Tests | pytest (backend) · Vitest + React Testing Library (frontend) |
| Eval | Keyword scoring + LLM-as-judge · 24 labeled real posts · multi-model comparison |

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- An [OpenAI API key](https://platform.openai.com/api-keys)

### 1. Clone and create the virtual environment

```bash
git clone https://github.com/iloopes/rapid.git
cd rapid

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt

cp .env.example .env
# Edit .env and fill in your OPENAI_API_KEY
```

### 3. Frontend

```bash
cd frontend
npm install
```

### 4. Run

```bash
# Terminal 1 — backend (from the backend/ folder)
uvicorn main:app --reload --port 8003

# Terminal 2 — frontend (from the frontend/ folder)
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

### Environment variables

```env
OPENAI_API_KEY=sk-...        # required
TAVILY_API_KEY=tvly-...      # optional — falls back to DuckDuckGo if not set

# Langfuse observability (all optional)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
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
    "text": "Politicians should wear sponsor jackets like F1 drivers...",
    "author": "user.bsky.social",
    "image_url": null
  },
  "bullets": [
    "This idea was popularized by comedian Robin Williams...",
    "The post uses the F1 driver sponsorship metaphor to critique political funding...",
    "The humor lands because it makes political donations visible in a visceral way..."
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

Three layers, written TDD-style before the implementation:

- **Unit** (`tests/unit/`) — pure functions: URL parsing, query building, bullet formatting
- **Integration** (`tests/integration/`) — external APIs mocked with `unittest.mock`
- **API** (`tests/api/`) — full request/response cycle via FastAPI `TestClient`

---

## Eval harness

The eval harness runs the agent against 12 real Bluesky posts and scores output quality using two complementary methods:

```bash
cd eval
python run_eval.py                              # 12 cases, gpt-4o
python run_eval.py --cases cases_v2.json        # 12 new cases (batch 2)
python run_eval.py --limit 3                    # quick smoke test
python run_eval.py --no-judge                   # skip LLM judge (faster)
python run_eval.py --model gpt-4o,gpt-4o-mini   # multi-model comparison
```

### Scoring

| Metric | Weight | Method |
|---|---|---|
| Keyword coverage | 50% | Checks whether expected concepts appear in the bullets |
| Bullet count | 20% | Validates 3–5 bullets were returned |
| LLM-as-judge | 30% | GPT-4o-mini rates factual accuracy and relevance (0–10) |

**Last run (gpt-4o):** score `0.93`, 12/12 passed · **gpt-4o-mini:** score `0.91`, 12/12 passed (threshold `0.60`).

When comparing multiple models, the harness generates `eval_comparison.html` with a side-by-side breakdown showing score per case, delta, and winner for each pair. The LLM judge always uses `gpt-4o-mini` as a fixed referee regardless of the model under test.

The eval acts as **acceptance tests for the agent** — analogous to end-to-end tests, but for non-deterministic AI output.

---

## Design decisions

**Structured JSON output**
The agent uses OpenAI's `json_schema` response format with `strict: true`. This eliminates fragile text parsing and guarantees the model always returns the expected structure, even when phrasing varies.

**Source curation by the model**
Instead of returning all search result URLs, the model selects 2–5 URLs that directly support its explanation. This makes sources meaningful rather than exhaustive.

**Dual search providers**
DuckDuckGo requires no API key and works out of the box. If `TAVILY_API_KEY` is set, Tavily is used instead for higher-quality, longer snippets — better for obscure references.

**Lazy client initialization**
The OpenAI client is initialized on first request, not at import time. This prevents startup crashes when API keys are missing and allows the health endpoint to always respond.

**Frontend state machine**
App state is a discriminated union (`idle | loading | success | error`), making impossible states unrepresentable and keeping conditional rendering simple.

**Image understanding**
When a post contains an image, the agent fetches it, encodes it as base64, and passes it to GPT-4o alongside the text. GPT-4o is multimodal and incorporates visual context into the explanation.

**LLM-as-judge eval**
The eval harness uses GPT-4o-mini as an independent judge to rate each explanation for factual accuracy and relevance. This is more robust than keyword matching alone for catching hallucinations and off-topic responses.
