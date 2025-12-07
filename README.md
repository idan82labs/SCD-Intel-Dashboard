# CI Research Platform

A **universal competitive intelligence research platform** that accepts any research query, plans a comprehensive investigation, executes multi-source data collection, and generates interactive visual reports.

## Features

- **Domain-agnostic**: Works for defense, biotech, fintech, energy, any industry
- **AI research agent**: Creates dynamic investigation plans using Claude
- **Chat-first UX**: Conversational interface with real-time research progress
- **Beautiful UI**: shadcn/ui design with interactive Plotly visualizations
- **Multi-source data**: Patents, government contracts, news, web search

## Tech Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, Plotly.js
- **Backend**: Python 3.11+, FastAPI, Anthropic SDK
- **Data Sources**: Tavily, USAspending, USPTO, RSS feeds, SAM.gov, EPO

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- API Keys (see Configuration)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Configuration

### Required API Keys

| Service | Purpose | Get Key |
|---------|---------|---------|
| **Anthropic** | AI agent and synthesis | [console.anthropic.com](https://console.anthropic.com) |
| **Tavily** | Web search | [tavily.com](https://tavily.com) |

### Optional API Keys

| Service | Purpose | Get Key |
|---------|---------|---------|
| **SAM.gov** | US government opportunities | [sam.gov/api](https://sam.gov/api) |
| **EPO** | European patents | [developers.epo.org](https://developers.epo.org) |

### Environment Variables

See `.env.example` for all configuration options.

## Project Structure

```
ci-research-platform/
├── frontend/                 # Next.js application
│   ├── app/                  # App router pages
│   ├── components/           # React components
│   │   ├── ui/              # shadcn base components
│   │   ├── chat/            # Chat interface
│   │   ├── research/        # Research flow
│   │   ├── report/          # Report viewer
│   │   └── visualizations/  # Charts
│   └── lib/                  # Utilities and hooks
│
├── backend/                  # FastAPI application
│   └── app/
│       ├── api/             # REST endpoints
│       ├── agent/           # Research agent
│       ├── data_sources/    # Data integrations
│       ├── models/          # Pydantic models
│       └── services/        # Business logic
│
└── docker-compose.yml        # Container deployment
```

## Docker Deployment

```bash
# Build and run all services
docker-compose up --build

# Or run in background
docker-compose up -d
```

## Example Research Queries

The system handles any research topic:

- "What's the competitive landscape for cloud security startups?"
- "Map the EV battery supply chain from mining to manufacturing"
- "Who won the largest DoD AI contracts in 2024?"
- "Analyze emerging patents in quantum computing"
- "Track biotech M&A activity in gene therapy"

## License

MIT
