from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.api import router as api_router

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

# Include routers
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
