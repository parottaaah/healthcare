from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.services.auth import verify_csrf
from app.api.routes import health
from app.routers import bills
from app.routers import whatsapp
from app.routers import auth
from app.core.config import settings

app = FastAPI(title="DecryptCare API", dependencies=[Depends(verify_csrf)])

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(bills.router)
app.include_router(whatsapp.router)