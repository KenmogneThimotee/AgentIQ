from enum import Enum
from typing import Any

from src.helpers.agents import AgentState, NotificationType
from src.helpers.orchestrator import Message
from .result_mixin import ResultMixin
from .input_mixin import InputMixin



class AgentMixin:
    """Mixin for agent handling."""

    name: str
    output: Any
    agent_context_id: str
    state: AgentState

    def __init__(self, name: str):
        self.name = name 

    def register_orchestrator(self, orchestrator: 'OrchestratorMixin') -> None:
        self.orchestrator = orchestrator
    
    def notify(self, notification_type: NotificationType) -> None:
        self.orchestrator.update_execution_graph_state(self.id, notification_type)

    def set_agent_context_id(self, agent_context_id: str) -> None:
        self.agent_context_id = agent_context_id

    def get_result(self) -> Any:
        return self.output
    
    @property
    def is_initialized(self) -> bool:
        return self.state == AgentState.INITIALIZED
    
    @property
    def is_idle(self) -> bool:
        return self.state == AgentState.IDLE
    
    @property
    def is_running(self) -> bool:
        return self.state == AgentState.RUNNING
    
    @property
    def is_success(self) -> bool:
        return self.state == AgentState.SUCCESS
    
    @property
    def is_error(self) -> bool:
        return self.state == AgentState.ERROR

    @property
    def id(self) -> str:
        """Get the agent's context ID."""
        if self.agent_context_id is None:
            raise ValueError("Agent context ID has not been set")
        return self.agent_context_id
    
    def send_message(self, message: Message):
        self.orchestrator.write_message(message)

    def run(self, input: Any):
        print(f"Running agent {self.id} ::: {self.name}")
        self.state = AgentState.RUNNING
        self.output = input
        self.state = AgentState.SUCCESS
        self.notify(NotificationType.SUCCESS)
        pass 