from fastapi import FastAPI
from app.api.webhook import router as telegram_router

# Initialize the central application microservice
app = FastAPI(
    title="Digital Second Brain Core API",
    version="1.0.0",
    description="Enterprise-grade production backend managing hybrid graph-vector knowledge retrieval"
)

# Register our sub-module routers
app.include_router(telegram_router)

@app.get("/health")
def health_check():
    """Simple server availability checker."""
    return {"status": "healthy", "service": "digital_second_brain_backend"}