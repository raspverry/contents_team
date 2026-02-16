"""Streamlit GUI — 재테크는 스크루지 AI 콘텐츠 팀 대시보드."""

import streamlit as st

st.set_page_config(
    page_title="재테크는 스크루지 — AI 콘텐츠 팀",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    # 사이드바
    st.sidebar.title("💰 재테크는 스크루지")
    st.sidebar.caption("AI 콘텐츠 팀 운영 시스템")
    st.sidebar.divider()

    page = st.sidebar.radio(
        "메뉴",
        [
            "🏠 대시보드",
            "🤖 에이전트",
            "⚡ 워크플로우",
            "📝 산출물",
            "⚙️ 설정",
        ],
    )

    if page == "🏠 대시보드":
        _page_dashboard()
    elif page == "🤖 에이전트":
        _page_agents()
    elif page == "⚡ 워크플로우":
        _page_workflows()
    elif page == "📝 산출물":
        _page_outputs()
    elif page == "⚙️ 설정":
        _page_settings()


def _page_dashboard():
    """대시보드: 전체 현황."""
    st.title("🏠 대시보드")

    import httpx

    try:
        resp = httpx.get("http://127.0.0.1:8000/api/status", timeout=5)
        status = resp.json()
    except httpx.ConnectError:
        st.error("⚠️ API 서버에 연결할 수 없습니다. `uv run api` 로 서버를 먼저 실행하세요.")
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("AI 에이전트", f"{status['agents_count']}명")
    col2.metric("워크플로우", f"{status['workflows_count']}개")
    col3.metric("산출물", f"{status['outputs_count']}개")
    col4.metric("오늘 날짜", status["today"])

    st.divider()

    # 조직도
    st.subheader("📋 조직 구조")
    st.code(
        """
대표: 재테크는 스크루지 (전체 방향 지시 & 최종 승인)
│
├── 🎯 브랜딩 전략팀 (2명)   — 브랜드 전략가, 포지셔닝 분석가
├── 🔍 콘텐츠 분석팀 (3명)   — 트렌드 헌터, 벤치마킹 분석가, 성과 분석가
├── 🎬 릴스 제작팀 (4명)     — 기획자, 대본 작가, 캡션&DM 작가, 편집 가이드
├── 🧵 스레드 콘텐츠팀 (2명) — 기획자, 작가
└── 🎙 팬딩 멤버십팀 (4명)   — 전략가, 컬럼니스트, 브리퍼, ETF 리서처
        """,
        language=None,
    )

    # 빠른 실행 버튼
    st.subheader("⚡ 빠른 실행")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🧵 오늘 스레드 3개", use_container_width=True):
            st.session_state["run_workflow"] = "daily-threads"
            st.switch_page("pages/workflows.py")

    with col2:
        if st.button("🎬 릴스 풀세트", use_container_width=True):
            st.session_state["run_workflow"] = "reels-fullset"
            st.switch_page("pages/workflows.py")

    with col3:
        if st.button("📰 데일리 브리핑", use_container_width=True):
            st.session_state["run_workflow"] = "daily-briefing"
            st.switch_page("pages/workflows.py")


def _page_agents():
    """에이전트 관리 페이지."""
    st.title("🤖 에이전트")

    import httpx

    try:
        resp = httpx.get("http://127.0.0.1:8000/api/agents", timeout=5)
        agents = resp.json()
    except httpx.ConnectError:
        st.error("⚠️ API 서버에 연결할 수 없습니다.")
        return

    # 팀별 탭
    teams = {}
    for a in agents:
        teams.setdefault(a["team_display"], []).append(a)

    tabs = st.tabs(list(teams.keys()))
    for tab, (team_name, team_agents) in zip(tabs, teams.items()):
        with tab:
            for agent in team_agents:
                with st.expander(f"**{agent['name']}** — {agent['role']}", expanded=False):
                    st.caption(f"실행 빈도: {agent['frequency']}")

                    user_msg = st.text_area(
                        "요청 메시지",
                        key=f"msg_{agent['id']}",
                        placeholder="이 에이전트에게 시킬 작업을 입력하세요...",
                    )

                    if st.button("▶ 실행", key=f"run_{agent['id']}"):
                        if not user_msg:
                            st.warning("메시지를 입력해주세요.")
                        else:
                            with st.spinner(f"{agent['name']} 작업 중..."):
                                try:
                                    result = httpx.post(
                                        f"http://127.0.0.1:8000/api/agents/{agent['id']}/run",
                                        json={"user_message": user_msg},
                                        timeout=120,
                                    ).json()

                                    if result["status"] == "completed":
                                        st.success(f"완료! (토큰: {result['tokens_used']})")
                                        st.markdown(result["content"])
                                        if result.get("output_file"):
                                            st.caption(f"저장됨: {result['output_file']}")
                                    else:
                                        st.error(f"실패: {result['error']}")
                                except httpx.ReadTimeout:
                                    st.error("시간 초과. 다시 시도해주세요.")


def _page_workflows():
    """워크플로우 실행 페이지."""
    st.title("⚡ 워크플로우")

    import httpx

    try:
        resp = httpx.get("http://127.0.0.1:8000/api/workflows", timeout=5)
        workflows = resp.json()
    except httpx.ConnectError:
        st.error("⚠️ API 서버에 연결할 수 없습니다.")
        return

    for wf in workflows:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(wf["name"])
                st.caption(wf["description"])

                # 스텝 시각화
                step_names = [s["agent_id"] for s in wf["steps"]]
                deps = {s["agent_id"]: s["depends_on"] for s in wf["steps"]}

                # 그룹으로 나누기
                groups = []
                placed = set()
                remaining = list(wf["steps"])
                while remaining:
                    group = [
                        s for s in remaining if all(d in placed for d in s["depends_on"])
                    ]
                    if not group:
                        break
                    groups.append([s["agent_id"] for s in group])
                    for s in group:
                        placed.add(s["agent_id"])
                        remaining.remove(s)

                flow_parts = []
                for g in groups:
                    if len(g) == 1:
                        flow_parts.append(g[0])
                    else:
                        flow_parts.append(f"[{' + '.join(g)}]")
                st.code(" → ".join(flow_parts), language=None)

            with col2:
                if st.button("▶ 실행", key=f"wf_{wf['id']}", use_container_width=True):
                    with st.spinner(f"'{wf['name']}' 실행 중..."):
                        try:
                            result = httpx.post(
                                f"http://127.0.0.1:8000/api/workflows/{wf['id']}/run",
                                json={},
                                timeout=300,
                            ).json()

                            st.success(f"완료! ({len(result['results'])}개 스텝)")
                            for r in result["results"]:
                                status_icon = "✅" if r["status"] == "completed" else "❌"
                                with st.expander(f"{status_icon} {r['agent_id']}"):
                                    if r["status"] == "completed":
                                        st.markdown(r["content"])
                                        st.caption(f"토큰: {r['tokens_used']}")
                                    else:
                                        st.error(r["error"])
                        except httpx.ReadTimeout:
                            st.error("시간 초과 (5분). 워크플로우가 너무 복잡할 수 있습니다.")


def _page_outputs():
    """산출물 조회 페이지."""
    st.title("📝 산출물")

    import httpx

    try:
        resp = httpx.get("http://127.0.0.1:8000/api/outputs", timeout=5)
        outputs = resp.json()
    except httpx.ConnectError:
        st.error("⚠️ API 서버에 연결할 수 없습니다.")
        return

    if not outputs:
        st.info("아직 산출물이 없습니다. 에이전트를 실행해서 콘텐츠를 생산하세요!")
        return

    # 팀별 필터
    teams = sorted(set(o["team"] for o in outputs))
    selected_team = st.selectbox("팀 필터", ["전체"] + teams)

    filtered = outputs
    if selected_team != "전체":
        filtered = [o for o in outputs if o["team"] == selected_team]

    for item in filtered:
        with st.expander(f"📄 {item['filename']} ({item['team']})"):
            try:
                content = httpx.get(
                    f"http://127.0.0.1:8000/api/outputs/{item['team']}/{item['filename']}",
                    timeout=5,
                ).json()
                st.markdown(content["content"])
            except Exception:
                st.error("파일을 불러올 수 없습니다.")


def _page_settings():
    """설정 페이지."""
    st.title("⚙️ 설정")

    st.subheader("API 설정")
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        help="ANTHROPIC_API_KEY 환경 변수 또는 .env 파일로도 설정 가능",
    )
    model = st.selectbox(
        "모델",
        [
            "claude-sonnet-4-5-20250929",
            "claude-haiku-4-5-20251001",
            "claude-opus-4-6",
        ],
        help="기본: claude-sonnet-4-5-20250929",
    )

    if st.button("저장"):
        from pathlib import Path
        from src.core.config import BASE_DIR

        env_path = BASE_DIR / ".env"
        lines = []
        if env_path.exists():
            lines = env_path.read_text().splitlines()

        # 기존 키 업데이트 또는 추가
        env_dict = {}
        for line in lines:
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env_dict[k.strip()] = v.strip()

        if api_key:
            env_dict["ANTHROPIC_API_KEY"] = api_key
        env_dict["MODEL"] = model

        env_content = "\n".join(f"{k}={v}" for k, v in env_dict.items()) + "\n"
        env_path.write_text(env_content)
        st.success("설정이 저장되었습니다. 서버를 재시작하세요.")

    st.divider()
    st.subheader("시스템 정보")
    st.json(
        {
            "version": "0.1.0",
            "python_project": "uv",
            "backend": "FastAPI",
            "frontend": "Streamlit",
            "ai_model": "Anthropic Claude",
        }
    )


if __name__ == "__main__":
    main()
