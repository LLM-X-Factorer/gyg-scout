# GYG Scout

GetYourGuide 商品调研与竞品分析工具。输入关键词，自动爬取 GYG 平台数据，通过 AI 生成商家视角的竞品分析报告。

## Features

- **智能爬取**：基于 Playwright 自动化浏览器，绕过反爬保护，支持搜索结果页 + 商品详情页
- **AI 分析**：Google Gemini 2.5 Flash 从商家竞品调研角度生成结构化报告
- **数据可视化**：价格分布、评分分布、价格-评分散点图
- **PDF 导出**：一键导出专业排版的 PDF 报告
- **异步任务**：后台执行爬取和分析，前端实时展示进度
- **中文报告**：报告以中文撰写，价格以人民币（CNY）显示

## Architecture

```
┌─────────────────┐     ┌──────────────────────────────────┐
│   Frontend      │     │          Backend                 │
│   React + TS    │────▶│  FastAPI                         │
│   TailwindCSS   │     │  ├── Scraper (Playwright)        │
│   Recharts      │     │  ├── Analyzer (Gemini 2.5 Flash) │
│   nginx         │     │  ├── SQLite (WAL mode)           │
└─────────────────┘     │  └── PDF Export (Playwright)     │
                        └──────────────────────────────────┘
```

- **Backend**: Python 3.12 / FastAPI / Playwright / SQLite / google-genai
- **Frontend**: React 19 / TypeScript / TailwindCSS v4 / Recharts
- **Deployment**: Docker Compose (Playwright official image + nginx)

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Google Gemini API Key ([get one here](https://aistudio.google.com/apikey))

### Run

```bash
cp .env.example .env
# Edit .env and set your GEMINI_API_KEY

docker compose up --build
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs

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

## Usage

1. Open http://localhost:3000
2. Enter a search keyword (e.g. `shenzhen`, `paris walking tour`)
3. Set the number of pages to scrape (1-10)
4. Click **Start Research** and wait for the task to complete
5. View the analysis report with charts and data tables
6. Click **Download PDF** to export the report

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/tasks` | Create a research task |
| `GET` | `/api/tasks` | List all tasks |
| `GET` | `/api/tasks/{id}` | Get task detail + report |
| `DELETE` | `/api/tasks/{id}` | Delete a task |
| `GET` | `/api/tasks/{id}/export` | Export report as PDF |
| `GET` | `/health` | Health check |

### Create Task Example

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"keyword": "shenzhen", "max_pages": 5}'
```

## Project Structure

```
gyg-scout/
├── docker-compose.yml          # Docker orchestration
├── .env.example                # Environment variables template
├── backend/
│   ├── Dockerfile              # Playwright official image based
│   ├── requirements.txt
│   └── app/
│       ├── main.py             # FastAPI app entry point
│       ├── config.py           # Settings (pydantic-settings)
│       ├── database.py         # SQLite + WAL + async sessions
│       ├── report_template.py  # HTML/CSS report template
│       ├── api/
│       │   └── tasks.py        # REST API routes + PDF export
│       ├── models/
│       │   └── task.py         # Task & Activity ORM models
│       ├── schemas/
│       │   └── task.py         # Pydantic request/response schemas
│       ├── scraper/
│       │   └── gyg.py          # Playwright GYG scraper
│       └── analyzer/
│           └── gemini.py       # Gemini LLM analysis + report
└── frontend/
    ├── Dockerfile              # Multi-stage: build + nginx
    ├── nginx.conf              # API reverse proxy config
    └── src/
        ├── App.tsx             # Main app with task list + detail
        ├── api.ts              # API client
        ├── types.ts            # TypeScript type definitions
        └── components/
            ├── CreateTask.tsx   # Keyword input form
            ├── TaskList.tsx     # Task list with status/progress
            ├── TaskDetail.tsx   # Report viewer + data table + PDF export
            └── Charts.tsx       # Price/rating distribution charts
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | - | Google Gemini API key |
| `DATABASE_URL` | No | `sqlite+aiosqlite:///./data/gyg_scout.db` | Database URL |
| `SCRAPER_HEADLESS` | No | `true` | Run browser in headless mode |
| `SCRAPER_TIMEOUT` | No | `30000` | Page load timeout (ms) |
| `SCRAPER_MAX_PAGES` | No | `5` | Max search result pages to scrape |
| `SCRAPER_DELAY_MIN` | No | `2` | Min delay between requests (sec) |
| `SCRAPER_DELAY_MAX` | No | `5` | Max delay between requests (sec) |

## Technical Notes

- **Anti-bot bypass**: Uses real Chromium with randomized User-Agent and webdriver detection bypass
- **GYG page layouts**: Supports both grid layout (e.g. paris) and list layout (e.g. shenzhen)
- **Deduplication**: Activities are deduplicated by GYG ID across pages
- **Fallback report**: If Gemini API is unavailable, generates a statistical summary report
- **Currency**: All prices displayed in CNY (RMB)

## License

MIT
