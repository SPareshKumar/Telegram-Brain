from fastapi import FastAPI
from app.api.webhook import router as telegram_router
from app.api.dashboard import router as dashboard_router  # 👈 Import the new UI module

# Initialize the central application microservice
app = FastAPI(
    title="Digital Second Brain Core API",
    version="1.0.0",
    description="Enterprise-grade production backend managing hybrid graph-vector knowledge retrieval"
)

# Register our sub-module routers
app.include_router(telegram_router)
app.include_router(dashboard_router)  # 👈 Register the dashboard routes

@app.get("/health")
def health_check():
    """Simple server availability checker."""
    return {"status": "healthy", "service": "digital_second_brain_backend"}