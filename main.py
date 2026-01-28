"""
AI Agent Service - Entry Point
"""
import uvicorn
from settings import settings


def main():
    """Start the FastAPI server."""
    uvicorn.run(
        "app.server:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning",
    )


if __name__ == "__main__":
    main()
