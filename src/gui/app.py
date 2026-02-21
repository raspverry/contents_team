"""Streamlit GUI — 재테크는 스크루지 AI 콘텐츠 팀 대시보드."""

import httpx
import streamlit as st

from src.core.config import settings

st.set_page_config(
    page_title="재테크는 스크루지 — AI 콘텐츠 팀",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE = f"http://{settings.api_host}:{settings.api_port}"


def _api_get(path: str, **kwargs) -> dict | list | None:
    """API GET 요청 헬퍼. 연결 실패 시 None 반환."""
    try:
        resp = httpx.get(f"{API_BASE}{path}", timeout=5, **kwargs)
        return resp.json()
    except (httpx.ConnectError, httpx.ReadTimeout):
        return None


def _api_post(path: str, *, json: dict = None, timeout: int = 120) -> dict | None:
    """API POST 요청 헬퍼."""
    try:
        resp = httpx.post(f"{API_BASE}{path}", json=json or {}, timeout=timeout)
        return resp.json()
    except (httpx.ConnectError, httpx.ReadTimeout):
        return None


def _show_api_error():
    st.error("⚠️ API 서버에 연결할 수 없습니다. `uv run api` 로 서버를 먼저 실행하세요.")


def main():
    st.sidebar.title("💰 재테크는 스크루지")
    st.sidebar.caption("AI 콘텐츠 팀 운영 시스템")
    st.sidebar.divider()

    page = st.sidebar.radio(
        "메뉴",
        ["🏠 대시보드", "🤖 에이전트", "⚡ 워크플로우", "💬 팀 채팅", "📝 산출물", "⚙️ 설정"],
    )

    pages = {
        "🏠 대시보드": _page_dashboard,
        "🤖 에이전트": _page_agents,
        "⚡ 워크플로우": _page_workflows,
        "💬 팀 채팅": _page_chat,
        "📝 산출물": _page_outputs,
        "⚙️ 설정": _page_settings,
    }
    pages[page]()


# ── 대시보드 ─────────────────────────────────────────────────


def _page_dashboard():
    st.title("🏠 대시보드")

    status = _api_get("/api/status")
    if not status:
        _show_api_error()
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("AI 에이전트", f"{status['agents_count']}명")
    col2.metric("워크플로우", f"{status['workflows_count']}개")
    col3.metric("산출물", f"{status['outputs_count']}개")
    col4.metric("오늘 날짜", status["today"])

    st.divider()

    st.subheader("📋 조직 구조")
    st.code(
        "대표: 재테크는 스크루지 (전체 방향 지시 & 최종 승인)\n"
        "│\n"
        "├── 🎯 브랜딩 전략팀 (2명)   — 브랜드 전략가, 포지셔닝 분석가\n"
        "├── 🔍 콘텐츠 분석팀 (3명)   — 트렌드 헌터, 벤치마킹 분석가, 성과 분석가\n"
        "├── 🎬 릴스 제작팀 (4명)     — 기획자, 대본 작가, 캡션&DM 작가, 편집 가이드\n"
        "├── 🧵 스레드 콘텐츠팀 (2명) — 기획자, 작가\n"
        "└── 🎙 팬딩 멤버십팀 (4명)   — 전략가, 컬럼니스트, 브리퍼, ETF 리서처",
        language=None,
    )

    st.subheader("⚡ 빠른 실행")
    col1, col2, col3 = st.columns(3)

    workflows_to_run = {
        "daily-threads": ("🧵 오늘 스레드 3개", col1),
        "reels-fullset": ("🎬 릴스 풀세트", col2),
        "daily-briefing": ("📰 데일리 브리핑", col3),
    }

    for wf_id, (label, col) in workflows_to_run.items():
        with col:
            if st.button(label, use_container_width=True, key=f"dash_{wf_id}"):
                st.session_state["quick_run"] = wf_id
                st.rerun()

    # 빠른 실행 처리
    if "quick_run" in st.session_state:
        wf_id = st.session_state.pop("quick_run")
        _run_workflow_inline(wf_id)


# ── 에이전트 ─────────────────────────────────────────────────


def _page_agents():
    st.title("🤖 에이전트")

    agents = _api_get("/api/agents")
    if not agents:
        _show_api_error()
        return

    teams: dict[str, list] = {}
    for a in agents:
        teams.setdefault(a["team_display"], []).append(a)

    tabs = st.tabs(list(teams.keys()))
    for tab, (_, team_agents) in zip(tabs, teams.items()):
        with tab:
            for agent in team_agents:
                with st.expander(
                    f"**{agent['name']}** — {agent['role']}", expanded=False
                ):
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
                                result = _api_post(
                                    f"/api/agents/{agent['id']}/run",
                                    json={"user_message": user_msg},
                                )
                                if result is None:
                                    st.error("API 요청 실패. 서버를 확인하세요.")
                                elif result["status"] == "completed":
                                    st.success(
                                        f"완료! (토큰: {result['tokens_used']})"
                                    )
                                    st.markdown(result["content"])
                                    if result.get("output_file"):
                                        st.caption(f"저장됨: {result['output_file']}")
                                else:
                                    st.error(f"실패: {result['error']}")


# ── 워크플로우 ───────────────────────────────────────────────


def _page_workflows():
    st.title("⚡ 워크플로우")

    workflows = _api_get("/api/workflows")
    if not workflows:
        _show_api_error()
        return

    for wf in workflows:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(wf["name"])
                st.caption(wf["description"])
                st.code(_visualize_steps(wf["steps"]), language=None)

            with col2:
                if st.button(
                    "▶ 실행", key=f"wf_{wf['id']}", use_container_width=True
                ):
                    _run_workflow_inline(wf["id"])


def _visualize_steps(steps: list[dict]) -> str:
    """워크플로우 스텝을 텍스트로 시각화."""
    groups: list[list[str]] = []
    placed: set[str] = set()
    remaining = list(steps)

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

    parts = []
    for g in groups:
        parts.append(g[0] if len(g) == 1 else f"[{' + '.join(g)}]")
    return " → ".join(parts)


def _run_workflow_inline(workflow_id: str):
    """워크플로우를 실행하고 결과를 인라인으로 표시."""
    with st.spinner("워크플로우 실행 중..."):
        result = _api_post(
            f"/api/workflows/{workflow_id}/run",
            timeout=300,
        )

    if result is None:
        st.error("API 요청 실패 (시간 초과 또는 서버 오류)")
        return

    st.success(f"완료! ({len(result['results'])}개 스텝)")
    for r in result["results"]:
        icon = "✅" if r["status"] == "completed" else "❌"
        with st.expander(f"{icon} {r['agent_id']}"):
            if r["status"] == "completed":
                st.markdown(r["content"])
                st.caption(f"토큰: {r['tokens_used']}")
            else:
                st.error(r["error"])


# ── 산출물 ───────────────────────────────────────────────────


def _page_outputs():
    st.title("📝 산출물")

    outputs = _api_get("/api/outputs")
    if outputs is None:
        _show_api_error()
        return

    if not outputs:
        st.info("아직 산출물이 없습니다. 에이전트를 실행해서 콘텐츠를 생산하세요!")
        return

    teams = sorted(set(o["team"] for o in outputs))
    selected_team = st.selectbox("팀 필터", ["전체"] + teams)

    filtered = outputs
    if selected_team != "전체":
        filtered = [o for o in outputs if o["team"] == selected_team]

    for item in filtered:
        with st.expander(f"📄 {item['filename']} ({item['team']})"):
            data = _api_get(f"/api/outputs/{item['team']}/{item['filename']}")
            if data:
                st.markdown(data["content"])
            else:
                st.error("파일을 불러올 수 없습니다.")


# ── 팀 채팅 ──────────────────────────────────────────────

_TEAM_EMOJI: dict[str, str] = {
    "team1-branding": "🎯",
    "team2-analysis": "🔍",
    "team3-reels": "🎬",
    "team4-threads": "🧵",
    "team5-fanding": "🎙",
    "team6-cardnews": "🎨",
}


def _page_chat():
    st.title("💬 팀 채팅")

    if "chat_room_id" not in st.session_state:
        st.session_state["chat_room_id"] = None
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []

    if st.session_state["chat_room_id"] is None:
        _chat_setup()
    else:
        _chat_conversation()


def _chat_setup():
    """채팅방 생성 UI."""
    st.markdown("에이전트들을 모아 주제에 대해 토론시키고, 직접 대화에 참여하세요.")
    st.divider()

    agents = _api_get("/api/agents")
    if not agents:
        _show_api_error()
        return

    # 팀별 그룹핑
    teams: dict[str, list] = {}
    for a in agents:
        teams.setdefault(a["team_display"], []).append(a)

    st.subheader("참여 에이전트 선택")

    selected_ids: list[str] = []
    for team_name, team_agents in teams.items():
        st.caption(team_name)
        cols = st.columns(min(len(team_agents), 4))
        for i, agent in enumerate(team_agents):
            with cols[i % len(cols)]:
                if st.checkbox(agent["name"], key=f"chat_sel_{agent['id']}"):
                    selected_ids.append(agent["id"])

    st.divider()
    topic = st.text_input(
        "토론 주제",
        placeholder="예: 이번 주 콘텐츠 전략을 어떻게 가져갈까?",
    )

    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"선택된 에이전트: {len(selected_ids)}명")
    with col2:
        if st.button(
            "채팅방 만들기",
            use_container_width=True,
            disabled=not (selected_ids and topic),
        ):
            result = _api_post(
                "/api/chat/rooms",
                json={"agent_ids": selected_ids, "topic": topic},
            )
            if result and "room_id" in result:
                st.session_state["chat_room_id"] = result["room_id"]
                st.session_state["chat_messages"] = result.get("messages", [])
                st.rerun()
            else:
                st.error("채팅방 생성 실패. API 서버를 확인하세요.")


def _chat_conversation():
    """채팅 대화 UI."""
    room_id = st.session_state["chat_room_id"]

    # 상단 바
    col_title, col_exit = st.columns([5, 1])
    with col_exit:
        if st.button("나가기", use_container_width=True):
            st.session_state["chat_room_id"] = None
            st.session_state["chat_messages"] = []
            st.rerun()

    # 메시지 표시
    messages = st.session_state["chat_messages"]
    for msg in messages:
        role = msg["role"]
        if role == "system":
            st.info(msg["content"])
        elif role == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        elif role == "agent":
            team = msg.get("team", "")
            emoji = _TEAM_EMOJI.get(team, "🤖")
            agent_name = msg.get("agent_name", "에이전트")
            with st.chat_message(name=agent_name, avatar=emoji):
                st.caption(msg.get("team_display", ""))
                st.markdown(msg["content"])
                if msg.get("tokens_used"):
                    st.caption(f"토큰: {msg['tokens_used']}")

    st.divider()

    # 하단 입력
    col_input, col_send, col_round = st.columns([5, 1, 1])

    with col_input:
        user_input = st.text_input(
            "메시지",
            key="chat_user_input",
            placeholder="에이전트들에게 메시지를 보내세요...",
            label_visibility="collapsed",
        )

    with col_send:
        send_clicked = st.button("전송", use_container_width=True)

    with col_round:
        round_clicked = st.button("토론", use_container_width=True)

    # 사용자 메시지 전송
    if send_clicked and user_input:
        result = _api_post(
            f"/api/chat/rooms/{room_id}/messages",
            json={"content": user_input},
        )
        if result:
            st.session_state["chat_messages"].append(result)
            st.rerun()

    # 에이전트 라운드 실행
    if round_clicked:
        with st.spinner("에이전트들이 대화 중..."):
            result = _api_post(
                f"/api/chat/rooms/{room_id}/round",
                timeout=300,
            )
        if result is None:
            st.error("요청 실패. API 서버를 확인하세요.")
        elif "error" in result:
            st.error(result["error"])
        else:
            for msg in result.get("messages", []):
                st.session_state["chat_messages"].append(msg)
            st.rerun()


# ── 설정 ─────────────────────────────────────────────────────


def _page_settings():
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
    )

    if st.button("저장"):
        from src.core.config import BASE_DIR

        env_path = BASE_DIR / ".env"
        env_dict: dict[str, str] = {}
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env_dict[k.strip()] = v.strip()

        if api_key:
            env_dict["ANTHROPIC_API_KEY"] = api_key
        env_dict["MODEL"] = model

        env_path.write_text(
            "\n".join(f"{k}={v}" for k, v in env_dict.items()) + "\n"
        )
        st.success("설정 저장 완료. 서버를 재시작하세요.")

    st.divider()
    st.subheader("시스템 정보")
    st.json({
        "version": "0.2.0",
        "backend": "FastAPI",
        "frontend": "Streamlit",
        "ai_model": "Anthropic Claude",
        "package_manager": "uv",
    })


if __name__ == "__main__":
    main()
