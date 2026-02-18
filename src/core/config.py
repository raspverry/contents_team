"""프로젝트 설정."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parent.parent.parent

AGENTS_DIR = BASE_DIR / "agents"
OUTPUTS_DIR = BASE_DIR / "outputs"
WORKFLOWS_DIR = BASE_DIR / "workflows"


class Settings(BaseSettings):
    """환경 변수 기반 설정."""

    anthropic_api_key: str = ""
    model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 4096

    # 브랜드 설정
    brand_name: str = "재테크는 스크루지"
    brand_handle: str = "@재테크는스크루지"

    # 서버 설정
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    gui_port: int = 8501

    # 레이트 리미팅
    rate_limit_run: int = 10  # 에이전트/렌더 실행: 분당 N회
    rate_limit_workflow: int = 5  # 워크플로우 실행: 분당 N회

    model_config = {"env_file": str(BASE_DIR / ".env"), "env_prefix": ""}


settings = Settings()
