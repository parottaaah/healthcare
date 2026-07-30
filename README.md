# DecryptCare

DecryptCare is an AI-powered healthcare billing transparency platform designed to empower patients with clear, actionable insights into their medical expenses, featuring a conversational WhatsApp assistant named Nalam.

## Project Structure

```text
.
├── docker-compose.yml     # Infrastructure services (Postgres, Redis, etc.)
├── apps
│   ├── api                # FastAPI backend Python application
│   └── web                # Vite frontend application
└── ...
```

## Prerequisites

- Node.js 20+
- Python 3.11+
- Docker

## Getting Started

### 1. Start Infrastructure
Start the required background services using Docker Compose:
```bash
docker compose up -d
```

### 2. Set Up the FastAPI Backend
Navigate to the API directory and set up the Python environment:
```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate  # Or `.venv\Scripts\activate` on Windows
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

### 3. Set Up the Vite Frontend
Navigate to the frontend directory and start the dev server:
```bash
cd apps/web
npm install
cp .env.example .env
npm run dev
```

## Environment Variables

Environment variables are managed through `.env` files. We provide template files for both applications:
- Backend: `apps/api/.env.example`
- Frontend: `apps/web/.env.example`

To configure your environment, copy these `.example` files to `.env` in their respective directories and fill in the actual values. 
**WARNING: Never commit a real `.env` file containing actual secrets.**

## Roadmap

- [x] Milestone 1 scaffolding
- [ ] DB models/migrations
- [ ] Bill upload + parsing pipeline
- [ ] AI-powered bill explanation
- [ ] WhatsApp webhook
- [ ] Auth
- [ ] CI

## Contributing

Each new feature should be shipped as its own Pull Request. Please follow our PR templates and branch naming conventions.