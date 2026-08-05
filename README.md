# Sezhi

Sezhi is an AI-powered healthcare billing transparency platform designed to empower patients with clear, actionable insights into their medical expenses, featuring a conversational WhatsApp assistant named Sezhi.

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

> [!NOTE]
> **Environment Variables & BOM**: If you edit `.env` in Notepad or another editor that adds a byte order mark (BOM), the app now handles it automatically — but if you ever see a `Field required` / `Extra inputs are not permitted` pair of errors for the same field on startup, re-save `.env` as plain UTF-8.

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

## Authentication

The web dashboard endpoints require JWT Bearer token authentication.

### Registering a User

To create a new user:
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com", "password":"mysecurepassword", "name":"Test User", "phone_number":"1234567890"}'
```
This will return an `access_token` that you can use to authenticate.

### Logging In

To log in and retrieve a token:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com", "password":"mysecurepassword"}'
```
You will receive a JSON response containing the `access_token`.

## Uploading a bill

You can upload a bill (PDF, JPEG, or PNG) to the API for OCR parsing and line-item extraction. Make sure you pass your JWT token in the `Authorization` header. Example `curl` request:

```bash
curl -X POST http://localhost:8000/bills/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/your/bill.pdf"
```

## AI Bill Explanations

To generate AI explanations and flag potential overcharges for line items, make sure you have set the `ANTHROPIC_API_KEY` in your `.env` file. Then, you can call the explain endpoint with your token:

```bash
curl -X POST http://localhost:8000/bills/{bill_id}/explain \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Environment Variables

Environment variables are managed through `.env` files. We provide template files for both applications:
- Backend: `apps/api/.env.example`
- Frontend: `apps/web/.env.example`

To configure your environment, copy these `.example` files to `.env` in their respective directories and fill in the actual values. 
**WARNING: Never commit a real `.env` file containing actual secrets.**

## WhatsApp Integration (Sezhi)

We use the WhatsApp Cloud API to support bill upload and conversational QA via our assistant, Sezhi.

### Setup Instructions
1. **Meta Developer App**: Go to the [Meta Developer Dashboard](https://developers.facebook.com/), create a Business app, and set up the WhatsApp product.
2. **Test Number & Tokens**: Under the WhatsApp > API Setup section, you will find your temporary `WHATSAPP_ACCESS_TOKEN` and `WHATSAPP_PHONE_NUMBER_ID`. Add these to your `.env` file.
3. **Webhook Verification**: Create a random string and add it to your `.env` file as `WHATSAPP_VERIFY_TOKEN`.
4. **Local Testing (Ngrok)**: Meta requires a public HTTPS URL for the webhook. If you're developing locally, use ngrok to expose your API:
   ```bash
   ngrok http 8000
   ```
   Take the resulting ngrok URL (e.g., `https://abcdef123.ngrok.app`) and configure your WhatsApp webhook in the Meta dashboard to point to `https://abcdef123.ngrok.app/webhooks/whatsapp`.
5. Enter your `WHATSAPP_VERIFY_TOKEN` in the Meta dashboard to verify.

## Roadmap

- [x] Milestone 1 scaffolding
- [x] DB models/migrations
- [x] Bill upload + parsing pipeline
- [x] AI-powered bill explanation
- [x] WhatsApp webhook
- [x] Auth
- [x] Frontend bill dashboard
- [x] CI

## Using the Web Dashboard

The dashboard lives at `http://localhost:5173` (when running `npm run dev` in `apps/web`).

### 1. Create an account

Navigate to `/register` and fill in your name, email, phone number, and a password:

```bash
# Or via curl directly against the API:
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"mysecret","name":"Jane","phone_number":"9876543210"}'
```

### 2. Sign in

Go to `/login` with your email and password. On success you'll be redirected to `/dashboard` and your bearer token is stored in `localStorage` so you stay signed in across refreshes.

### 3. Upload a bill

On the dashboard, click **Choose file**, pick a PDF, JPEG, or PNG (max 10 MB), then click **Upload & Parse**. The backend will OCR the file and extract line items automatically.

### 4. View and explain a bill

Click any bill card to see its line items. If the bill hasn't been explained yet, click **✨ Explain this bill** — this calls the AI explanation endpoint and populates each line item with a plain-language explanation. Items that look like potential overcharges are highlighted with a red **⚠️ Flagged** badge.

## Continuous Integration

We use GitHub Actions for CI. On every push and pull request to `main`, the CI pipeline automatically runs:

1. **backend-test**: Runs the FastAPI backend test suite (`pytest`) with SQLite and Redis.
2. **backend-audit**: Scans backend dependencies for known CVEs using `pip-audit`.
3. **frontend-test**: Builds the Vite React frontend and runs its test suite.
4. **frontend-audit**: Scans frontend dependencies for known vulnerabilities using `npm audit`.

## Deployment

Sezhi is configured for deployment using **Railway** (Backend & Infrastructure) and **Vercel** (Frontend).
See the full [Deployment Guide](docs/DEPLOYMENT.md) for step-by-step instructions.

**Live Demo:** [https://sezhi.vercel.app](https://sezhi.vercel.app) *(Placeholder)*

## Contributing

Each new feature should be shipped as its own Pull Request. Please follow our PR templates and branch naming conventions.