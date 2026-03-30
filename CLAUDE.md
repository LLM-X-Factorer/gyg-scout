# GYG Scout - Project Guide

## What is this?
A web tool for GetYourGuide product research and competitive analysis. Merchants input keywords, the system scrapes GYG, analyzes data with Gemini AI, and generates Chinese-language competitive reports.

## Tech Stack
- Backend: Python 3.12 / FastAPI / Playwright / SQLite (WAL) / google-genai (Gemini 2.5 Flash)
- Frontend: React 19 / TypeScript / TailwindCSS v4 / Recharts / Vite 8
- Deployment: Docker Compose

## Key Development Notes

### Scraper
- GYG blocks plain HTTP requests (403). Must use Playwright with webdriver bypass.
- Two page layouts exist: grid (`vertical-activity-card`) and list (`a[href*="-t"]`). The JS extraction code handles both.
- Currency param: `currency=CNY`. Price format on page: `From RMB¥XXX`.
- Dedup by gyg_id both in JS (per page) and Python (across pages).

### Gemini
- Use `google-genai` SDK (not deprecated `google-generativeai`).
- Model: `gemini-2.5-flash`. Older models (2.0-flash) return 404.
- Report prompt is in Chinese, merchant competitive analysis perspective.

### Database
- SQLite with WAL mode set via SQLAlchemy engine connect event (not PRAGMA in transaction).
- Async via aiosqlite. URL must use `sqlite+aiosqlite:///` prefix.

### Docker
- Backend image: `mcr.microsoft.com/playwright/python:v1.52.0-noble` (includes Chromium).
- Frontend: multi-stage build (node → nginx), nginx proxies `/api/` to backend.
- `.env` file required (not committed). Copy from `.env.example`.

### Frontend
- `verbatimModuleSyntax: true` in tsconfig — use `import type` for type-only imports.
- Report HTML rendered in iframe (isolated styling with Noto Sans SC font).

## Commands
```bash
# Start
docker compose up --build

# Rebuild backend only
docker compose build backend && docker compose up -d

# Clean DB and restart
rm -f data/gyg_scout.db* && docker compose down && docker compose up -d

# Frontend type check
cd frontend && npx tsc --noEmit

# Test API
curl -X POST http://localhost:8000/api/tasks -H "Content-Type: application/json" -d '{"keyword":"shenzhen","max_pages":5}'
```
