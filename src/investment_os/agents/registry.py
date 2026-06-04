"""Agent registry: build agent instances from configuration.

Maps the ``type`` string in ``config/agents.yaml`` to a concrete ``Agent``
subclass. Adding a new agent in a future slice is a two-line change here.
"""

from __future__ import annotations

from ..loaders import ConfigError
from ..models import AgentConfig
from .base import Agent
from .momentum import MomentumAgent
from .quality import QualityAgent
from .risk import RiskAgent
from .value import ValueAgent

AGENT_TYPES: dict[str, type[Agent]] = {
    MomentumAgent.type_name: MomentumAgent,
    ValueAgent.type_name: ValueAgent,
    QualityAgent.type_name: QualityAgent,
    RiskAgent.type_name: RiskAgent,
}


def build_agents(agent_configs: dict[str, AgentConfig]) -> list[Agent]:
    """Instantiate every *enabled* configured agent, preserving config order."""

    agents: list[Agent] = []
    for name, cfg in agent_configs.items():
        if not cfg.enabled:
            continue
        agent_cls = AGENT_TYPES.get(cfg.type)
        if agent_cls is None:
            raise ConfigError(
                f"Agent '{name}' has unknown type '{cfg.type}'. Known types: {sorted(AGENT_TYPES)}"
            )
        agents.append(agent_cls(name=name, params=cfg.params))
    if not agents:
        raise ConfigError("No enabled agents configured.")
    return agents
