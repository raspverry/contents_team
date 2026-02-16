# 재테크는 스크루지 — AI 콘텐츠 팀 운영 시스템

15명의 AI 에이전트가 콘텐츠를 생산하는 1인 회사 운영 시스템.

인스타그램 릴스, 스레드, 팬딩 멤버십 콘텐츠를 AI 에이전트 팀이 기획부터 제작까지 자동으로 처리합니다.

## 팀 구성

| 팀 | 에이전트 | 역할 |
|----|---------|------|
| **브랜딩 전략팀** | 브랜드 전략가, 포지셔닝 분석가 | 브랜드 방향성 수립 |
| **콘텐츠 분석팀** | 트렌드 헌터, 벤치마킹 분석가, 성과 분석가 | 데이터 기반 분석 |
| **인스타 릴스 제작팀** | 릴스 기획자, 대본 작가, 캡션&DM 작가, 영상 편집 가이드 | 릴스 콘텐츠 제작 |
| **스레드 콘텐츠팀** | 스레드 기획자, 스레드 작가 | 일일 스레드 기획/작성 |
| **팬딩 멤버십팀** | 멤버십 전략가, 주간 컬럼니스트, 데일리 브리퍼, ETF 리서처 | 유료 콘텐츠 제작 |

## 빠른 시작

### 사전 요구사항

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/) (패키지 매니저)
- Anthropic API 키

### 설치

```bash
git clone <repository-url>
cd contents_team

# 의존성 설치
uv sync
```

### 환경 설정

```bash
cp .env.example .env
# .env 파일을 열고 ANTHROPIC_API_KEY를 설정하세요
```

### 실행

터미널 2개에서 각각 실행합니다.

```bash
# 터미널 1: API 서버
uv run api

# 터미널 2: GUI (Streamlit)
uv run streamlit run src/gui/app.py
```

- API: http://127.0.0.1:8000
- API 문서: http://127.0.0.1:8000/docs
- GUI: http://127.0.0.1:8501

## 프리셋 워크플로우

| ID | 이름 | 설명 |
|----|------|------|
| `weekly-planning` | 주간 기획 | 분석팀 리포트 → 기획자 캘린더 수립 (월요일) |
| `daily-threads` | 오늘의 스레드 | 오늘의 스레드 3개 작성 (아침/점심/저녁) |
| `reels-fullset` | 릴스 풀세트 | 릴스 대본 → 캡션 + 편집가이드 (병렬) |
| `daily-briefing` | 데일리 브리핑 | 오늘의 경제 뉴스 요약 브리핑 |
| `weekly-column` | 주간 컬럼 | 프리미엄 주간 컬럼 작성 |
| `etf-report` | ETF 리포트 | 주간 ETF 모니터링 리포트 |

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/status` | 시스템 상태 |
| GET | `/api/agents` | 에이전트 목록 |
| GET | `/api/agents/{id}` | 에이전트 상세 (시스템 프롬프트 포함) |
| POST | `/api/agents/{id}/run` | 에이전트 단독 실행 |
| GET | `/api/workflows` | 워크플로우 목록 |
| POST | `/api/workflows/{id}/run` | 워크플로우 실행 |
| GET | `/api/outputs` | 산출물 목록 (`?team=`, `?date_str=` 필터) |
| GET | `/api/outputs/{team}/{filename}` | 산출물 내용 조회 |

## 프로젝트 구조

```
contents_team/
├── agents/                  # 에이전트 프롬프트 정의 (마크다운)
│   ├── team1-branding/      # 브랜딩 전략팀 (2명)
│   ├── team2-analysis/      # 콘텐츠 분석팀 (3명)
│   ├── team3-reels/         # 인스타 릴스 제작팀 (4명)
│   ├── team4-threads/       # 스레드 콘텐츠팀 (2명)
│   └── team5-fanding/       # 팬딩 멤버십팀 (4명)
├── src/
│   ├── core/                # 핵심 모듈
│   │   ├── config.py        # 환경 설정 (pydantic-settings)
│   │   ├── models.py        # 도메인 모델 (팀, 에이전트, 워크플로우)
│   │   └── clients.py       # Anthropic API 클라이언트 싱글턴
│   ├── services/            # 서비스 레이어
│   │   ├── agent_service.py # 에이전트 로딩/실행
│   │   ├── workflow_service.py  # 워크플로우 프리셋/실행 엔진
│   │   ├── output_service.py    # 산출물 조회
│   │   └── storage.py       # 스토리지 추상화 (FileStorage)
│   ├── api/                 # FastAPI 백엔드
│   │   ├── server.py        # 서버 진입점
│   │   ├── routes.py        # API 라우트
│   │   └── schemas.py       # 요청/응답 스키마
│   └── gui/
│       └── app.py           # Streamlit GUI
├── workflows/               # 워크플로우 가이드 문서
├── outputs/                 # 생성된 산출물 (git-ignored)
├── pyproject.toml           # 프로젝트 설정 (uv)
├── .env.example             # 환경 변수 템플릿
└── CLAUDE.md                # AI 어시스턴트 가이드
```

## 아키텍처

```
Routes (얇은 라우트) → Services (비즈니스 로직) → Core (모델/설정)
                                ↓
                        StorageBackend (ABC)
                                ↓
                        FileStorage (파일시스템)
                        → 향후: DBStorage / S3Storage
```

- **에이전트 프롬프트**: `agents/` 디렉토리의 마크다운 파일에서 런타임 파싱
- **워크플로우 실행**: DAG 기반 의존성 해결, `asyncio.gather`로 병렬 실행
- **스토리지 추상화**: `StorageBackend` ABC → 현재 `FileStorage`, SaaS 전환 시 DB/S3로 교체

## 기술 스택

- **Python** >= 3.11
- **uv** — 패키지 매니저
- **FastAPI** — REST API
- **Streamlit** — GUI (MVP)
- **Anthropic SDK** — Claude API
- **Pydantic** — 데이터 검증/스키마
- **pydantic-settings** — 환경 변수 관리

## 라이선스

Private
