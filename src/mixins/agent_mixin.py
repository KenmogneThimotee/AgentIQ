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

    ingress_messages_callbacks: Dict[str, Callable]
    ingress_messages: List[Message]

    egress_messages_callbacks: Dict[str, Callable]
    egress_messages: List[Message]
    process_ingress_independently: bool
    def __init__(self, name: str, emitted_messages: List[str], received_messages: List[str], process_ingress_independently: bool = False):
        self.name = name 
        self.agent_context_id = None
        self.state = AgentState.INITIALIZED
        self.output = None
        self.ingress_messages_callbacks = {}
        self.ingress_messages = set(received_messages)
        self.egress_messages_callbacks = {}
        self.egress_messages = set(emitted_messages)
        self.process_ingress_independently = process_ingress_independently

    @staticmethod
    def receive_message(message_name: str):
        """Decorator to register a method as a message handler.
        
        Args:
            message_name: The name of the message to handle
            
        Returns:
            Decorator function that registers the method as a handler
        """
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                if not self.check_ingress_message(message_name):
                    raise ValueError(f"Message {message_name} not registered for agent {self.name}")
                self.set_ingress_message_callback(message_name, func)
                message = args[0]
                return func(self, message.data)
            return wrapper
        return decorator
    
    @staticmethod
    def emit_message(message_name: str):
        """Decorator to register a method as a message handler.
        
        Args:
            message_name: The name of the message to handle
            
        Returns:
            Decorator function that registers the method as a handler
        """
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                if not self.check_egress_message(message_name):
                    raise ValueError(f"Message {message_name} not registered for agent {self.name}")
                self.set_egress_message_callback(message_name, func)
                data = func(self, *args, **kwargs)
                message = Message(name=message_name, data=data)
                self.send_message(message)
            return wrapper
        return decorator
    
    @receive_message("test_message")
    def do_something(self):
        pass

    def set_ingress_message_callback(self, message: str, callback: Callable):
        self.ingress_messages_callbacks[message] = callback

    def set_egress_message_callback(self, message: str, callback: Callable):
        self.egress_messages_callbacks[message] = callback
    
    def get_ingress_message_callback(self, message: str) -> Callable:
        return self.ingress_messages_callbacks[message]
    
    def get_egress_message_callback(self, message: str) -> Callable:
        return self.egress_messages_callbacks[message]
    
    def remove_ingress_message_callback(self, message: str):
        del self.ingress_messages_callbacks[message]

    def remove_egress_message_callback(self, message: str):
        del self.egress_messages_callbacks[message]

    def clear_ingress_message_callbacks(self):
        self.ingress_messages_callbacks = {}

    def clear_egress_message_callbacks(self):
        self.egress_messages_callbacks = {}

    def set_ingress_messages(self, message: str):
        self.ingress_messages.add(message)

    def set_egress_messages(self, message: str):
        self.egress_messages.add(message)
    
    def get_ingress_messages(self) -> List[Message]:
        return self.ingress_messages

    def get_egress_messages(self) -> List[Message]:
        return self.egress_messages
    
    def remove_ingress_message(self, message: str):
        self.ingress_messages.discard(message)

    def remove_egress_message(self, message: str):
        self.egress_messages.discard(message)

    def check_ingress_message(self, message: str) -> bool:
        return message in self.ingress_messages

    def check_egress_message(self, message: str) -> bool:
        return message in self.egress_messages

    def clear_ingress_messages(self):
        self.ingress_messages = set()

    def clear_egress_messages(self):
        self.egress_messages = set()

    def register_orchestrator(self, orchestrator: 'OrchestratorMixin') -> None:
        self.orchestrator = orchestrator
    
    def notify(self, notification_type: NotificationType) -> None:
        self.orchestrator.update_execution_graph_state(self.id, notification_type)

    def set_agent_context_id(self, agent_context_id: str) -> None:
        self.agent_context_id = agent_context_id

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