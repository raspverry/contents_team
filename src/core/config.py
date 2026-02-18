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

    # AI 프로바이더 설정
    ai_provider: str = "anthropic"  # "anthropic" 또는 "openai"

    anthropic_api_key: str = ""
    model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 4096

    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"
    openai_max_tokens: int = 4096

    # 브랜드 설정
    brand_name: str = "재테크는 스크루지"
    brand_handle: str = "@재테크는스크루지"
    brand_topic: str = "재테크"
    brand_description: str = "돈에 관한 모든 이야기를 쉽고 재밌게 전달하는 콘텐츠 브랜드"
    brand_disclaimer: str = "본 콘텐츠는 전문적 조언이 아닙니다. 중요한 결정은 전문가와 상담하세요."

    # 서버 설정
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    gui_port: int = 8501

    # 레이트 리미팅
    rate_limit_run: int = 10  # 에이전트/렌더 실행: 분당 N회
    rate_limit_workflow: int = 5  # 워크플로우 실행: 분당 N회

    model_config = {"env_file": str(BASE_DIR / ".env"), "env_prefix": ""}


settings = Settings()
