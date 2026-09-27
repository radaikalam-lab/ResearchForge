"""FastAPI application factory and lifecycle."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from researchforge.api.router import api_router


def create_app() -> FastAPI:
    """Instantiate and configure ResearchForge FastAPI engine."""
    app = FastAPI(
        title="ResearchForge API",
        description="Local-first Computational Research Lifecycle Engine",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(api_router, prefix="/api")

    @app.get("/healthz", tags=["System"])
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "engine": "ResearchForge", "version": "0.1.0"}

    return app


app = create_app()
