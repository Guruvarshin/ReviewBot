# ReviewBot

AI-powered code review for GitHub pull requests. Four specialist LangGraph agents (security, performance, code quality, and testing) analyze a PR's diff plus static-analysis output, stream their findings live to the browser via SSE, and produce a consolidated overall score. Reviews are persisted to MongoDB, with history and per-repo trend views.

## Architecture

```
                        ┌───────────────┐
   GitHub PR URL ─────► │   fetch_pr     │  (GitHub REST API: metadata + diffs)
                        └──────┬────────┘
                               ▼
                        ┌───────────────┐
                        │ static_analysis│  (ruff / bandit / radon, Python files only)
                        └──────┬────────┘
                               ▼
        ┌──────────┬──────────┬──────────┬──────────┐
        ▼          ▼          ▼          ▼
   security   performance   quality    testing        (4 agents, run in parallel)
   (Claude)    (Claude)   (GPT-4o-mini) (GPT-4o-mini)
        └──────────┴──────────┴──────────┘
                               ▼
                        ┌───────────────┐
                        │   synthesize   │  (Claude — consolidated score + summary)
                        └──────┬────────┘
                               ▼
                        ┌───────────────┐
                        │    persist     │  (MongoDB)
                        └────────────────┘
```

- **Backend**: FastAPI + LangGraph (Python 3.11). Streams progress via Server-Sent Events.
- **Frontend**: Next.js 14 (App Router, plain JavaScript) + Tailwind CSS + recharts.
- **Database**: MongoDB (Atlas free tier), via the async `motor` driver.
- **Static analysis**: `ruff`, `bandit`, `radon` — Python files only. Non-Python files are reviewed purely via LLM reasoning over the diff.

## Project structure

```
ReviewBot/
├── backend/
│   ├── app/
│   │   ├── agents/            # 4 specialist agents + synthesis + persist nodes
│   │   ├── config.py          # env var loading
│   │   ├── db.py               # MongoDB (motor) setup
│   │   ├── diff_utils.py       # diff parsing helpers
│   │   ├── github_client.py    # GitHub REST API client
│   │   ├── graph.py             # LangGraph graph wiring
│   │   ├── graph_state.py       # ReviewState TypedDict
│   │   ├── main.py               # FastAPI app + routes
│   │   ├── models.py             # Pydantic models
│   │   ├── static_analysis.py    # ruff/bandit/radon pipeline
│   │   └── streaming.py          # SSE event mapping
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.js                  # submit PR form
│   │   ├── review/page.js            # live streaming review
│   │   ├── review/[id]/page.js       # past review detail + chart
│   │   ├── repo/[owner]/[name]/page.js # repo trend chart
│   │   └── history/page.js           # all past reviews
│   ├── components/                   # ScoreBadge, DimensionCard, FindingItem, charts...
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── .env.example
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- A [GitHub personal access token](https://github.com/settings/tokens) (classic, `public_repo` scope is enough)
- An [Anthropic API key](https://console.anthropic.com/) (used by security, performance, and synthesis agents)
- An [OpenAI API key](https://platform.openai.com/) (used by quality and testing agents)
- (Optional) A [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) free cluster — without it, live reviews still work, but history/trend/persistence are disabled

## Environment variables

Copy `.env.example` and fill in your values:

```
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GITHUB_TOKEN=
MONGODB_URI=
MONGODB_DB_NAME=reviewbot
CORS_ORIGINS=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

| Variable | Used by | Required? |
|---|---|---|
| `ANTHROPIC_API_KEY` | backend (security, performance, synthesis agents) | Yes |
| `OPENAI_API_KEY` | backend (quality, testing agents) | Yes |
| `GITHUB_TOKEN` | backend (PR fetching) | Yes — app crashes at startup without it |
| `MONGODB_URI` | backend (persistence/history/trend) | No — persistence silently disables if unset |
| `MONGODB_DB_NAME` | backend | No (defaults to `reviewbot`) |
| `CORS_ORIGINS` | backend (allowed frontend origins, comma-separated) | No (defaults to `http://localhost:3000`) |
| `NEXT_PUBLIC_API_URL` | frontend (backend base URL, no trailing slash) | Yes |

## Running locally (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate      # macOS/Linux
pip install -r requirements.txt

# create backend/.env with the variables above (ANTHROPIC_API_KEY, OPENAI_API_KEY,
# GITHUB_TOKEN, MONGODB_URI, MONGODB_DB_NAME, CORS_ORIGINS)

uvicorn app.main:app --reload --port 8000
```

Backend runs at `http://localhost:8000`. Check `http://localhost:8000/health`.

### Frontend

```bash
cd frontend
npm install

# create frontend/.env.local with:
# NEXT_PUBLIC_API_URL=http://localhost:8000

npm run dev
```

Frontend runs at `http://localhost:3000`.

## Running with Docker Compose

```bash
# create a .env file in the project root with all variables from .env.example
docker compose up --build
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

## API endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/pr?pr_url=...` | Fetch PR metadata + diffs |
| GET | `/api/static-analysis?pr_url=...` | Run static analysis on a PR |
| GET | `/api/review/stream?pr_url=...` | **SSE** — stream a full review |
| GET | `/api/reviews?repo_owner=&repo_name=&limit=` | List past reviews (summary) |
| GET | `/api/repo/{owner}/{name}/trend` | Score history for a repo (for charts) |
| GET | `/api/reviews/{review_id}` | Full detail for one past review |

### SSE events from `/api/review/stream`

| Event | Payload |
|---|---|
| `pr_fetched` | PR title, author, branches, file/line counts |
| `static_analysis_complete` | number of Python files analyzed |
| `agent_complete` | one specialist agent's `AgentResult` (score, summary, findings) — fires 4×, one per agent |
| `review_complete` | full `ReviewResult` (overall score, consolidated summary, all agent results) |
| `error` | `{ "message": "..." }` on failure (invalid/missing PR, GitHub rate limit) |

## Deployment

- **Backend** → [Render](https://render.com) (Docker-based web service, using `backend/Dockerfile`). Set all backend env vars in the Render dashboard.
- **Frontend** → [Vercel](https://vercel.com) (auto-detected Next.js build). Set `NEXT_PUBLIC_API_URL` to your Render backend URL (no trailing slash).
- After deploying both, set `CORS_ORIGINS` on Render to your Vercel URL (no trailing slash), e.g. `https://your-app.vercel.app`.

**Note**: Render's free tier spins down after ~15 minutes of inactivity — the first request after idle can take 30-50s to wake up.

## Known limitations

- **Non-Python files** get no static-analysis tool signal (ruff/bandit/radon are Python-only) — they're reviewed purely via LLM reasoning over the diff.
- **Large PRs are truncated**: each file's diff is capped at 500 lines, and PRs with more than 300 changed files only have the first 300 processed.
- **Anthropic rate limits**: security, performance, and synthesis agents all call Claude. On large PRs run back-to-back, you may hit the default 30k-input-tokens/min tier-1 limit — agent LLM calls retry with exponential backoff, but persistent issues require raising your Anthropic usage tier.
