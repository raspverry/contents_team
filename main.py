"""재테크는 스크루지 — AI 콘텐츠 팀 운영 시스템.

실행 방법:
    API 서버:    uv run api
    GUI:         uv run streamlit run src/gui/app.py
    동시 실행:   uv run python main.py
"""

import subprocess
import sys
import time


def main():
    print("💰 재테크는 스크루지 — AI 콘텐츠 팀")
    print("=" * 42)
    print()
    print("실행 방법:")
    print("  API 서버:  uv run api")
    print("  GUI:       uv run streamlit run src/gui/app.py")
    print()
    print("둘 다 실행하려면 터미널 2개에서 각각 실행하세요.")
    print()

    choice = input("지금 API 서버를 시작할까요? (y/n): ").strip().lower()
    if choice == "y":
        from src.api.server import main as start_api
        start_api()


if __name__ == "__main__":
    main()
