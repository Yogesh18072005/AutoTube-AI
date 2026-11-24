from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AutoTube AI API",
    version="0.1.0",
    description="Bilingual AI YouTube production workflow API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "autotube-api", "version": "0.1.0"}

@app.get("/api/v1/config", tags=["system"])
async def public_config() -> dict[str, list[str]]:
    return {
        "languages": ["en", "hi"],
        "formats": ["short", "long"],
        "workflow": ["idea", "research", "script", "assets", "render", "review", "approved", "scheduled", "published"],
    }
