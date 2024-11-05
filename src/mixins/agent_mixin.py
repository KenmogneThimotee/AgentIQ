from enum import Enum
from typing import Any
from pydantic import AbstractBaseModel
from pydantic.fields import String

from mixins.orchestrator import OrchestratorMixin
from .result_mixin import ResultMixin
from .input_mixin import InputMixin

class NotificationType(Enum):
    SUCCESS = "success"
    ERROR = "error"

class AgentState(Enum):
    INITIALIZED = "initialized"
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"

class Message:
    name: str
    data: Any
    agent_name: str
    agent_id: str

class AgentMixin(AbstractBaseModel):
    """Mixin for agent handling."""

    name: String
    output: Any
    agent_context_id: String
    state: AgentState

    def __init__(self, name: str):
        self.name = name 

    def register_orchestrator(self, orchestrator: 'OrchestratorMixin') -> None:
        self.orchestrator = orchestrator
    
    def notify(self, notification_type: NotificationType) -> None:
        self.orchestrator.update_execution_graph_state(self.id, notification_type)

    def set_agent_context_id(self, agent_context_id: String) -> None:
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
        # TODO: Implement the run method
        # 1. Set the input
        # 2. Run the agent
        # 3. Store the result
        # 4. Return the result
        self.notify(NotificationType.SUCCESS)
        pass 