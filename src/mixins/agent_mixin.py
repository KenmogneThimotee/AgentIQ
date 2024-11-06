from enum import Enum
from typing import Any, Callable, Dict, List

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

    independent_messages: Dict[str, List[Callable]]

    def __init__(self, name: str):
        self.name = name 
        self.agent_context_id = None
        self.state = AgentState.INITIALIZED
        self.output = None
        self.independent_messages = {}

    def register_orchestrator(self, orchestrator: 'OrchestratorMixin') -> None:
        self.orchestrator = orchestrator
    
    def notify(self, notification_type: NotificationType) -> None:
        self.orchestrator.update_execution_graph_state(self.id, notification_type)

    def set_agent_context_id(self, agent_context_id: str) -> None:
        self.agent_context_id = agent_context_id

    def get_result(self) -> Any:
        return self.output
    
    def add_message(self, message: Message, process_independently: bool = False, process_function: Callable = None) -> None:
        if process_independently:
            if message.name not in self.independent_messages:
                self.independent_messages[message.name] = []
            self.independent_messages[message.name].append(process_function)
        else:
            self.messages.append(message)
    
    
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
        message.agent_name = self.name
        message.agent_id = self.id
        self.orchestrator.write_message(message)

    def run(self, input: Any):
        self.state = AgentState.RUNNING
        self.output = input
        self.state = AgentState.SUCCESS
        self.notify(NotificationType.SUCCESS)
        pass 