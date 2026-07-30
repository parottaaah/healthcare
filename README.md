# DecryptCare

DecryptCare is an AI-powered healthcare billing transparency platform designed to empower patients with clear, actionable insights into their medical expenses, featuring a conversational WhatsApp assistant named Nalam.

## Project Structure

```text
.
├── docker-compose.yml     # Infrastructure services (Postgres, Redis, API)
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

### 1. Start the Backend & Infrastructure
The easiest way to run the API alongside its required background services (Postgres and Redis) is using Docker Compose. Make sure you've copied the `.env` file first:
```bash
cp apps/api/.env.example apps/api/.env
docker compose up -d
```
This spins up the database, cache, and the FastAPI backend together.

**(Alternative: Run the API without Docker)**
If you prefer to run the API directly on your machine for debugging:
```bash
docker compose up -d postgres redis  # Start only the infrastructure
cd apps/api
python -m venv .venv
source .venv/bin/activate  # Or `.venv\Scripts\activate` on Windows
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

### 2. Set Up the Vite Frontend
Navigate to the frontend directory and start the dev server:
```bash
cd apps/web
npm install
cp .env.example .env
npm run dev
```

## Database

To run database migrations and update the schema, navigate to the `apps/api/` directory and use Alembic:
```bash
cd apps/api
alembic upgrade head
```

If you change any SQLAlchemy models, you can generate a new migration script automatically:
```bash
alembic revision --autogenerate -m "description of changes"
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