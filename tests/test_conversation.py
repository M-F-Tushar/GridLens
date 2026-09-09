from __future__ import annotations

from domain.models import ScenarioRequest
from engine.scenario_engine import run_scenario
from llm.conversation import ConversationState, SessionRegistry


def test_conversation_state_remembers_turns_and_scenarios():
    state = ConversationState()
    state.add_turn("user", "Run the baseline scenario")
    result = run_scenario(ScenarioRequest(scenario_id="baseline"))
    state.remember_scenario(result)

    assert len(state.recent_turns()) == 1
    assert state.get_scenario("baseline") is result
    assert state.last_scenario_id() == "baseline"
    assert state.get_scenario("does-not-exist") is None


def test_session_registry_isolates_sessions():
    registry = SessionRegistry()
    a = registry.get_or_create("session-a")
    b = registry.get_or_create("session-b")
    a.add_turn("user", "hello")
    assert a is not b
    assert len(b.recent_turns()) == 0
    assert registry.get_or_create("session-a") is a  # same session returns same state


def test_session_registry_reset_clears_state():
    registry = SessionRegistry()
    registry.get_or_create("s").add_turn("user", "hi")
    registry.reset("s")
    fresh = registry.get_or_create("s")
    assert len(fresh.recent_turns()) == 0