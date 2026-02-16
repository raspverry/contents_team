# 데일리 루틴 워크플로우

## 매일 실행하는 에이전트

### 오전 루틴 (7~9시)

```
# 1. 데일리 브리핑 작성 (팬딩 멤버십)
Task(
  subagent_type="general-purpose",
  prompt="""
  agents/team5-fanding/daily-briefer.md의 시스템 프롬프트를 따라서,
  오늘의 데일리 브리핑을 작성하세요.

  오늘 날짜: {오늘 날짜}

  다음 소스를 참고하세요:
  - 주요 경제 뉴스
  - 전일 주요 지수 변동
  - 글로벌 시장 동향

  결과를 outputs/fanding/{오늘날짜}-daily-briefing.md에 저장하세요.
  """
)

# 2. 아침 스레드 작성 (정보형)
Task(
  subagent_type="general-purpose",
  prompt="""
  agents/team4-threads/threads-writer.md의 시스템 프롬프트를 따라서,
  오늘 아침 슬롯 스레드를 작성하세요.

  주간 캘린더 참조: outputs/threads/이번주-calendar.md
  오늘 아침 주제: {캘린더에서 확인}

  10줄 이내, 반말+친근 톤으로 작성하세요.
  """
)
```

### 점심 루틴 (12~13시)

```
# 3. 점심 스레드 작성 (공감형)
Task(
  subagent_type="general-purpose",
  prompt="""
  agents/team4-threads/threads-writer.md의 시스템 프롬프트를 따라서,
  오늘 점심 슬롯 스레드를 작성하세요.

  주간 캘린더 참조: outputs/threads/이번주-calendar.md
  오늘 점심 주제: {캘린더에서 확인}

  10줄 이내, 반말+친근 톤으로 작성하세요.
  """
)
```

### 저녁 루틴 (19~21시)

```
# 4. 저녁 스레드 작성 (인사이트형)
Task(
  subagent_type="general-purpose",
  prompt="""
  agents/team4-threads/threads-writer.md의 시스템 프롬프트를 따라서,
  오늘 저녁 슬롯 스레드를 작성하세요.

  주간 캘린더 참조: outputs/threads/이번주-calendar.md
  오늘 저녁 주제: {캘린더에서 확인}

  10줄 이내, 반말+친근 톤으로 작성하세요.
  """
)
```

---

## 릴스 제작일 추가 루틴 (주 2~3회)

릴스 기획 캘린더에 따라 제작일에 추가 실행:

```
# 1단계: 대본 작성
Task(
  subagent_type="general-purpose",
  prompt="""
  agents/team3-reels/reels-scriptwriter.md의 시스템 프롬프트를 따라서,
  오늘의 릴스 대본을 작성하세요.

  릴스 기획 브리프 참조: outputs/reels/이번주-calendar.md
  오늘 릴스 주제: {캘린더에서 확인}

  20~30초 분량, 후킹→본문→CTA 구조로 작성하세요.
  결과를 outputs/reels/{오늘날짜}-script.md에 저장하세요.
  """
)

# 2단계: 대본 완성 후 캡션 & 편집가이드 병렬 실행
Task(
  subagent_type="general-purpose",
  prompt="""
  agents/team3-reels/caption-dm-writer.md의 시스템 프롬프트를 따라서,
  오늘의 릴스 캡션과 DM 자료를 작성하세요.

  대본 참조: outputs/reels/{오늘날짜}-script.md
  결과를 outputs/reels/{오늘날짜}-caption.md에 저장하세요.
  """
)

Task(
  subagent_type="general-purpose",
  prompt="""
  agents/team3-reels/video-editing-guide.md의 시스템 프롬프트를 따라서,
  오늘의 릴스 편집 가이드를 작성하세요.

  대본 참조: outputs/reels/{오늘날짜}-script.md
  결과를 outputs/reels/{오늘날짜}-editing-guide.md에 저장하세요.
  """
)
```

---

## 빠른 실행 명령어 모음

| 작업 | 설명 |
|------|------|
| `오늘 스레드 3개 작성해줘` | 아침/점심/저녁 스레드 일괄 생성 |
| `오늘 데일리 브리핑 작성해줘` | 팬딩 멤버십 데일리 브리핑 |
| `이번 릴스 대본 써줘` | 캘린더 기반 릴스 대본 작성 |
| `이번 주 캘린더 세워줘` | 스레드 + 릴스 주간 캘린더 수립 |
| `주간 컬럼 써줘` | 팬딩 프리미엄 컬럼 작성 |
| `ETF 리포트 작성해줘` | 주간 ETF 모니터링 리포트 |

---

## 주의사항

1. **순서 준수** — 기획 → 대본 → 캡션/편집가이드 순서를 지킬 것
2. **캘린더 참조** — 항상 주간 캘린더를 먼저 확인 후 제작
3. **파일명 규칙** — `YYYY-MM-DD-유형.md` 형식 준수
4. **대표 리뷰** — 최종 퍼블리싱 전 대표(스크루지) 확인 필수
