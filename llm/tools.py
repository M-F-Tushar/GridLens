from __future__ import annotations

from typing import Any, Callable

from domain.models import ScenarioRequest
from engine.scenario_engine import run_scenario


def _run_scenario_tool(**kwargs: Any) -> dict:
    request = ScenarioRequest(**kwargs)
    result = run_scenario(request)
    return result.model_dump(mode="json")


class ToolSpec:
    """One callable tool plus its JSON-schema contract."""

    def __init__(
        self,
        name: str,
        description: str,
        parameters_schema: dict,
        handler: Callable[..., Any]
        ):
        self.name = name
        self.description = description
        self.parameters_schema = parameters_schema
        self.handler = handler

    def as_openai_tool(self) -> dict:
        """This converts the tool description into the format expected by many chat-completion APIs."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema,
            },
        }

    def invoke(self, arguments: dict) -> Any:
        return self.handler(**arguments)




TOOLS: dict[str, ToolSpec] = {
    "run_scenario": ToolSpec(
        name="run_scenario",
        description=(
            "Run a deterministic energy-system scenario (demand, solar, battery, "
            "grid import/export, cost, emissions) and return the full hourly result."
        ),
        parameters_schema=ScenarioRequest.model_json_schema(),
        handler=_run_scenario_tool,
    ),
}


def list_tools() -> list[dict]:
    return [tool.as_openai_tool() for tool in TOOLS.values()]


def call_tool(name: str, arguments: dict) -> Any:
    if name not in TOOLS:
        raise KeyError(f"Unknown tool: {name!r}. Known tools: {sorted(TOOLS)}")
    return TOOLS[name].invoke(arguments)