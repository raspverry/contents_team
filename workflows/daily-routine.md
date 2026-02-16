# 데일리 루틴 워크플로우

## 매일 실행하는 에이전트

### 오전 루틴 (7~9시)

**1. 데일리 브리핑 작성 (팬딩 멤버십)**

```bash
# GUI: Streamlit에서 "데일리 브리핑" 워크플로우 클릭
# API:
curl -X POST http://127.0.0.1:8000/api/workflows/daily-briefing/run
```

**2. 아침 스레드 작성 (정보형)**

오늘의 스레드 워크플로우에 아침 슬롯이 포함되어 있습니다.

```bash
# 3개 슬롯(아침/점심/저녁) 일괄 생성
curl -X POST http://127.0.0.1:8000/api/workflows/daily-threads/run
```

또는 개별 실행:

```bash
curl -X POST http://127.0.0.1:8000/api/agents/threads-writer/run \
  -H "Content-Type: application/json" \
  -d '{"user_message": "오늘 아침 슬롯 스레드를 작성해주세요. 카테고리: 정보형. 재테크 팁이나 지식을 10줄 이내, 반말+친근 톤으로 작성하세요."}'
```

### 점심 루틴 (12~13시)

**3. 점심 스레드 작성 (공감형)**

```bash
curl -X POST http://127.0.0.1:8000/api/agents/threads-writer/run \
  -H "Content-Type: application/json" \
  -d '{"user_message": "오늘 점심 슬롯 스레드를 작성해주세요. 카테고리: 공감형. 일상 속 돈 이야기를 10줄 이내, 반말+친근 톤으로 작성하세요."}'
```

### 저녁 루틴 (19~21시)

**4. 저녁 스레드 작성 (인사이트형)**

```bash
curl -X POST http://127.0.0.1:8000/api/agents/threads-writer/run \
  -H "Content-Type: application/json" \
  -d '{"user_message": "오늘 저녁 슬롯 스레드를 작성해주세요. 카테고리: 인사이트형. 깊이 있는 경제/투자 생각을 10줄 이내, 반말+친근 톤으로 작성하세요."}'
```

---

## 릴스 제작일 추가 루틴 (주 2~3회)

릴스 기획 캘린더에 따라 제작일에 추가 실행:

```bash
# 릴스 풀세트: 대본 → 캡션 + 편집가이드 (병렬)
curl -X POST http://127.0.0.1:8000/api/workflows/reels-fullset/run
```

또는 단계별 실행:

```bash
# 1단계: 대본 작성
curl -X POST http://127.0.0.1:8000/api/agents/reels-scriptwriter/run \
  -H "Content-Type: application/json" \
  -d '{"user_message": "오늘의 릴스 대본을 작성해주세요. 20~30초 분량, 후킹→본문→CTA 구조로 작성하세요."}'

# 2단계: 캡션 & 편집가이드 (대본 완성 후 병렬 가능)
curl -X POST http://127.0.0.1:8000/api/agents/caption-dm-writer/run \
  -H "Content-Type: application/json" \
  -d '{"user_message": "위 릴스 대본에 맞는 캡션과 DM 전송 자료를 작성해주세요."}'

curl -X POST http://127.0.0.1:8000/api/agents/video-editing-guide/run \
  -H "Content-Type: application/json" \
  -d '{"user_message": "위 릴스 대본에 맞는 편집 가이드 시트를 작성해주세요."}'
```

---

## 빠른 실행 명령어 모음

### GUI (Streamlit)

Streamlit GUI에서 워크플로우 탭을 열고 원하는 워크플로우를 클릭하여 실행합니다.

### API

| 작업 | API 호출 |
|------|---------|
| 오늘 스레드 3개 | `POST /api/workflows/daily-threads/run` |
| 데일리 브리핑 | `POST /api/workflows/daily-briefing/run` |
| 릴스 풀세트 | `POST /api/workflows/reels-fullset/run` |
| 주간 기획 | `POST /api/workflows/weekly-planning/run` |
| 주간 컬럼 | `POST /api/workflows/weekly-column/run` |
| ETF 리포트 | `POST /api/workflows/etf-report/run` |
| 산출물 목록 | `GET /api/outputs?team=threads&date_str=2026-02-16` |

---

## 주의사항

1. **순서 준수** — 기획 → 대본 → 캡션/편집가이드 순서를 지킬 것 (워크플로우가 자동 처리)
2. **캘린더 참조** — 항상 주간 캘린더를 먼저 확인 후 제작
3. **파일명** — 시스템이 자동 생성 (`YYYY-MM-DD-{agent_id}-{timestamp}.md`)
4. **대표 리뷰** — 최종 퍼블리싱 전 대표(스크루지) 확인 필수
