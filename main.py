import sys
import os
import logging

# Configure logging to show in terminal
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.agent import router as agent_router
from models.database_models import connect_to_mongo, close_mongo_connection

app = FastAPI(
    title="Mental Health Bot API",
    description="API for Mental Health Bot application",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to Mental Health Bot API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize MongoDB connection on startup"""
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    """Close MongoDB connection on shutdown"""
    await close_mongo_connection()

# Include routers
app.include_router(agent_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
