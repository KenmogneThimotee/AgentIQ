from collections import defaultdict
from enum import Enum
from typing import Any, Callable, Dict, List, Set

from src.helpers.agents import AgentState, NotificationType
from src.helpers.orchestrator import Message
from .result_mixin import ResultMixin
from .input_mixin import InputMixin





class AgentMixin:
    """Mixin for agent handling."""

    name: str
    agent_context_id: str
    state: AgentState

    ingress_messages_callbacks: Dict[str, Set[Callable]]

    def __init__(self, name: str):
        self.name = name 
        self.agent_context_id = None
        self.state = AgentState.INITIALIZED
        self.ingress_messages_callbacks = defaultdict(set)

        
    def on_receive_message(self, message_names: List[str]):
        """Decorator to register a method as a message handler.
        
        Args:
            message_name: The name of the message to handle
            
        Returns:
            Decorator function that registers the method as a handler
        """
        def decorator(func):
            print(f"Decorating {func.__name__} for messages {message_names} for agent {self.name}")
            self.set_ingress_message_callback((",").join(message_names), func)
            setattr(self, func.__name__, func)

        return decorator

    def emit_message(self, message_names: List[str]):
        """Decorator to register a method as a message handler."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                data = kwargs.get('data', args[0] if args else None)
                result = func(data)
                for message_name in message_names:
                    print(f"Emitting message {message_name} with data: {result}")
                    message = Message(name=message_name, data=result)
                    self.send_message(message)
            # Attach the wrapped function to the instance
            setattr(self, func.__name__, wrapper)
            return wrapper
        return decorator


    def set_ingress_message_callback(self, message: str, callback: Callable):
        try:
            self.ingress_messages_callbacks[message].add(callback)
        except KeyError:
            self.ingress_messages_callbacks[message] = set([callback])


    def get_ingress_message_callback(self, message: str) -> Callable:
        return self.ingress_messages_callbacks[message]

    def register_orchestrator(self, orchestrator: 'OrchestratorMixin') -> None:
        self.orchestrator = orchestrator
    
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
        print(f"Sending message {message.name} to orchestrator")
        message.agent_name = self.name
        message.agent_id = self.id
        self.orchestrator.write_message(message)
