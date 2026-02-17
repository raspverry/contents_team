"""FastAPI 서버 진입점."""

from __future__ import annotations

import uvicorn

from src.core.config import settings


def main():
    uvicorn.run(
        "src.api.routes:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )


if __name__ == "__main__":
    main()
