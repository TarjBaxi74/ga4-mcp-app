from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from analytics import router as analytics_router
from chat import router as chat_router

from auth import router as auth_router

app = FastAPI(title="GA4 MCP App")
app.include_router(auth_router, prefix="/auth")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ga4-mcp-frontend-550184459078.us-central1.run.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# analytics routes
app.include_router(
    analytics_router,
    prefix="/analytics",
    tags=["analytics"],
)

# chat route
app.include_router(
    chat_router,
    prefix="/chat",
    tags=["chat"],
)


@app.get("/")
def health():
    return {
        "status": "ok",
        "service": "ga4-mcp-backend",
    }