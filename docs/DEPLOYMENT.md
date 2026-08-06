# Deployment Guide

This document outlines how to deploy Sezhi's FastAPI backend and Vite frontend to production using Railway and Vercel.

## 1. Backend (API) Deployment to Railway

Railway provides an easy way to deploy Docker-based applications alongside managed databases.

### Provisioning Infrastructure
1. Log in to [Railway](https://railway.app/) and create a new project.
2. Add a **PostgreSQL** database service to the project.
3. Add a **Redis** service to the project.
4. Add a new service connected to your GitHub repository, pointing it to the root of the repository. Railway will detect `apps/api/railway.json` and build the API using `apps/api/Dockerfile`.

### Environment Variables
In your Railway API service settings, add the following variables:
- `DATABASE_URL`: Set this using the connection string provided by your Railway Postgres service (usually injected automatically by Railway).
- `REDIS_URL`: Set this using the connection string from your Railway Redis service.
- `JWT_SECRET`: A strong, randomly generated string for signing JWT tokens.
- `JWT_EXPIRES_IN_MINUTES`: E.g., `60`.
- `ANTHROPIC_API_KEY`: Your Anthropic Claude API key.
- `WHATSAPP_ACCESS_TOKEN`: The permanent access token from your Meta App.
- `WHATSAPP_PHONE_NUMBER_ID`: Your WhatsApp phone number ID.
- `WHATSAPP_VERIFY_TOKEN`: A custom string you will use to verify the webhook.
- `FRONTEND_ORIGIN`: The URL of your Vercel frontend (e.g., `https://sezhi.vercel.app`), which configuring CORS.
- `S3_BUCKET_NAME`: (Optional but recommended) The name of your AWS S3 bucket for storing medical bills. If omitted, falls back to local disk storage.
- `AWS_REGION`: The AWS region for your S3 bucket (e.g., `us-east-1`).
- `AWS_ACCESS_KEY_ID`: Your AWS access key with S3 permissions.
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key.
- `KMS_KEY_ID`: (Optional) A KMS Key ID for encrypting S3 objects. If omitted, AES-256 encryption is used.

### Running Migrations
After the backend is deployed, you must run the database migrations on the production database:
1. In the Railway dashboard, open the terminal/shell for your API service.
2. Run the following command:
   ```bash
   cd apps/api
   alembic upgrade head
   ```

### Webhook Configuration
Once the backend is live, configure your Meta WhatsApp app to point to your new production URL:
1. Go to the Meta App Dashboard > WhatsApp > Configuration.
2. Click "Edit" under Webhook.
3. Set the Callback URL to `https://<your-railway-app-domain>/webhooks/whatsapp`.
4. Enter your `WHATSAPP_VERIFY_TOKEN` (the same one you set in Railway).
5. Click "Verify and Save".

---

## 2. Frontend (Web) Deployment to Vercel

Vercel is optimized for deploying Vite/React applications.

1. Log in to [Vercel](https://vercel.com/) and click "Add New..." > "Project".
2. Import your GitHub repository.
3. Vercel will automatically detect the settings from `apps/web/vercel.json`, but verify the following:
   - **Framework Preset**: Vite
   - **Root Directory**: `apps/web`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Expand the "Environment Variables" section and add:
   - `VITE_API_URL`: The URL of your deployed Railway backend (e.g., `https://sezhi-production.up.railway.app`).
5. Click **Deploy**.

---

## 3. Security Notes & Secret Rotation

- **Never hardcode secrets** in the codebase. Always use environment variables.
- **Rotating Keys**: If your `JWT_SECRET`, `ANTHROPIC_API_KEY`, or `WHATSAPP_ACCESS_TOKEN` is ever exposed, you must rotate them immediately:
  1. Generate a new key/secret in the respective platform.
  2. Update the environment variables in Railway.
  3. Restart the Railway service to pick up the new secrets.
  4. Note that rotating the `JWT_SECRET` will log out all currently authenticated users (invalidating their tokens).
