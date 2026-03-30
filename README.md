# GYG Scout

GetYourGuide product research and competitive analysis tool. Enter keywords, automatically scrape, analyze, and generate structured research reports.

## Architecture

- **Backend**: Python FastAPI + Playwright + SQLite + Google Gemini
- **Frontend**: React + TypeScript + TailwindCSS + Recharts
- **Deployment**: Docker Compose

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Google Gemini API Key

### Run

```bash
cp .env.example .env
# Edit .env and set GEMINI_API_KEY

docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Local Development

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/tasks | Create a research task |
| GET | /api/tasks | List all tasks |
| GET | /api/tasks/{id} | Get task detail + report |
| DELETE | /api/tasks/{id} | Delete a task |
| GET | /api/tasks/{id}/export | Export report as PDF |
| GET | /health | Health check |

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| GEMINI_API_KEY | Yes | - | Google Gemini API key |
| DATABASE_URL | No | sqlite:///./data/gyg_scout.db | Database URL |
| SCRAPER_HEADLESS | No | true | Run browser headless |
| SCRAPER_MAX_PAGES | No | 5 | Max search result pages |
| SCRAPER_DELAY_MIN | No | 2 | Min delay between requests (sec) |
| SCRAPER_DELAY_MAX | No | 5 | Max delay between requests (sec) |
