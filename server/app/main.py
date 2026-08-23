from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import analysis

app = FastAPI(
    title="CodeLens API",
    description="Intelligent source-code repository analysis platform API",
    version="1.0.0",
)

# Enable CORS for local Vite development client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows local dev client (http://localhost:5173, etc.)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis.router, prefix="/api", tags=["Analysis"])


@app.get("/")
def root():
    return {
        "name": "CodeLens API",
        "health_endpoint": "/api/health",
        "analyze_endpoint": "/api/analyze",
    }
