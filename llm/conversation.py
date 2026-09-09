from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from domain.models import ScenarioResult


@dataclass
class ConversationTurn:
    role: str  # "user" | "assistant" | "tool"
    content: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ConversationState:
    """This stores everything needed for one active user session."""

    turns: list[ConversationTurn] = field(default_factory=list)
    scenario_history: dict[str, ScenarioResult] = field(default_factory=dict)

    def add_turn(self, role: str, content: str) -> None:
        self.turns.append(ConversationTurn(role=role, content=content))

    def remember_scenario(self, result: ScenarioResult) -> None:
        self.scenario_history[result.scenario_id] = result

    def get_scenario(self, scenario_id: str) -> ScenarioResult | None:
        return self.scenario_history.get(scenario_id)

    def last_scenario_id(self) -> str | None:
        if not self.scenario_history:
            return None
        return next(reversed(self.scenario_history))

    def recent_turns(self, limit: int = 20) -> list[ConversationTurn]:
        return self.turns[-limit:]


class SessionRegistry:
    """This manages multiple conversation sessions.
    Imagine several users using the application:
    The registry keeps each session separate.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, ConversationState] = {}

    def get_or_create(self, session_id: str) -> ConversationState:
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationState()
        return self._sessions[session_id]

    def reset(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)