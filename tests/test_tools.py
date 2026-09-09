
from __future__ import annotations

import pytest

from llm.tools import call_tool, list_tools


def test_list_tools_exposes_run_scenario_with_valid_json_schema():
    tools = list_tools()
    names = [t["function"]["name"] for t in tools]
    assert "run_scenario" in names
    run_scenario_tool = next(t for t in tools if t["function"]["name"] == "run_scenario")
    schema = run_scenario_tool["function"]["parameters"]
    assert schema["type"] == "object"
    assert "scenario_id" in schema["properties"]


def test_call_tool_run_scenario_returns_a_dict_result():
    result = call_tool("run_scenario", {"scenario_id": "tool-call-test", "horizon_hours": 6})
    assert result["scenario_id"] == "tool-call-test"
    assert len(result["records"]) == 6


def test_call_tool_rejects_unknown_tool_name():
    with pytest.raises(KeyError):
        call_tool("does_not_exist", {})


def test_call_tool_rejects_invalid_arguments():
    with pytest.raises(Exception):
        call_tool("run_scenario", {"scenario_id": "bad", "horizon_hours": 999999})