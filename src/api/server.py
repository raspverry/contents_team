"""FastAPI 서버 진입점."""

import uvicorn

from src.api.routes import app


def main():
    uvicorn.run(
        "src.api.routes:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
