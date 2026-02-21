"""팀 채팅 서비스.

멀티 에이전트 그룹 채팅 기능. 에이전트들이 대화에 순차적으로 참여합니다.
채팅은 휘발성(in-memory)이며, 파일 저장 없음.
"""

from __future__ import annotations

from src.core.clients import create_message
from src.core.config import settings
from src.core.models import ChatMessage, ChatRole, ChatRoom, inject_language_guide
from src.services.agent_service import load_all_agents


# ── 인메모리 저장소 ──────────────────────────────────────────

_chat_rooms: dict[str, ChatRoom] = {}
_MAX_ROOMS = 50
_MAX_CONTEXT_MESSAGES = 100


def _cleanup_rooms() -> None:
    """가장 오래된 방을 제거하여 _MAX_ROOMS 유지."""
    while len(_chat_rooms) > _MAX_ROOMS:
        oldest_key = min(_chat_rooms, key=lambda k: _chat_rooms[k].created_at)
        del _chat_rooms[oldest_key]


# ── 공개 API ─────────────────────────────────────────────────


def create_room(agent_ids: list[str], topic: str) -> ChatRoom:
    """새 채팅 방 생성."""
    if not agent_ids:
        raise ValueError("최소 1명의 에이전트가 필요합니다")

    agents = load_all_agents()
    invalid = [aid for aid in agent_ids if aid not in agents]
    if invalid:
        raise ValueError(f"존재하지 않는 에이전트: {', '.join(invalid)}")

    room = ChatRoom(agent_ids=agent_ids, topic=topic)

    agent_names = [agents[aid].name for aid in agent_ids]
    room.messages.append(
        ChatMessage(
            role=ChatRole.SYSTEM,
            content=f"주제: {topic}\n참여자: {', '.join(agent_names)}",
        )
    )

    _chat_rooms[room.room_id] = room
    _cleanup_rooms()
    return room


def get_room(room_id: str) -> ChatRoom | None:
    """채팅 방 조회."""
    return _chat_rooms.get(room_id)


def add_user_message(room_id: str, content: str) -> ChatMessage:
    """사용자 메시지를 채팅방에 추가."""
    room = _chat_rooms.get(room_id)
    if not room:
        raise KeyError(f"채팅 방 '{room_id}'를 찾을 수 없습니다")

    msg = ChatMessage(role=ChatRole.USER, content=content)
    room.messages.append(msg)
    return msg


async def run_chat_round(room_id: str) -> list[ChatMessage]:
    """에이전트 라운드 1회 실행. 모든 에이전트가 순서대로 1번씩 발언."""
    room = _chat_rooms.get(room_id)
    if not room:
        raise KeyError(f"채팅 방 '{room_id}'를 찾을 수 없습니다")

    agents = load_all_agents()
    round_messages: list[ChatMessage] = []

    for agent_id in room.agent_ids:
        agent = agents.get(agent_id)
        if not agent:
            continue

        # 매 턴마다 최신 대화 이력 반영
        conversation = _build_conversation_context(room)

        # 시스템 프롬프트: 에이전트 페르소나 + 언어 가이드 + 채팅 지시
        system = inject_language_guide(agent.system_prompt, settings.content_language)
        system += (
            f"\n\n## 그룹 채팅 컨텍스트"
            f"\n당신은 '{room.topic}' 주제의 그룹 채팅에 참여 중입니다."
            f"\n다른 참여자들의 발언을 참고하되, 당신의 전문 분야 관점에서 의견을 제시하세요."
            f"\n자연스러운 대화체로 답변하세요. 너무 길지 않게 핵심만 전달하세요."
        )

        user_message = (
            f"다음은 지금까지의 대화입니다:\n\n{conversation}\n\n"
            f"위 대화를 읽고, {agent.name}({agent.role})으로서 "
            f"'{room.topic}'에 대해 당신의 관점을 이야기해주세요."
        )

        try:
            ai_response = await create_message(
                system=system,
                user_message=user_message,
            )
            msg = ChatMessage(
                role=ChatRole.AGENT,
                agent_id=agent_id,
                agent_name=agent.name,
                team=agent.team.value,
                content=ai_response.content,
                tokens_used=ai_response.total_tokens,
            )
        except Exception as e:
            msg = ChatMessage(
                role=ChatRole.AGENT,
                agent_id=agent_id,
                agent_name=agent.name,
                team=agent.team.value,
                content=f"[오류 발생: {e}]",
            )

        room.messages.append(msg)
        room.total_tokens += msg.tokens_used
        round_messages.append(msg)

    room.round_count += 1
    return round_messages


# ── 내부 헬퍼 ────────────────────────────────────────────────


def _build_conversation_context(room: ChatRoom) -> str:
    """전체 대화 이력을 하나의 텍스트로 구성."""
    msgs = room.messages
    if len(msgs) > _MAX_CONTEXT_MESSAGES:
        msgs = [msgs[0]] + msgs[-(_MAX_CONTEXT_MESSAGES - 1) :]

    parts: list[str] = []
    for msg in msgs:
        if msg.role == ChatRole.SYSTEM:
            parts.append(f"[시스템] {msg.content}")
        elif msg.role == ChatRole.USER:
            parts.append(f"[사용자] {msg.content}")
        elif msg.role == ChatRole.AGENT:
            parts.append(f"[{msg.agent_name}] {msg.content}")
    return "\n\n".join(parts)
