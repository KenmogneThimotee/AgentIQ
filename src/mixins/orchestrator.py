from copy import deepcopy
from uuid import uuid4
from src.helpers.agents import NotificationType
from src.helpers.orchestrator import Message
from src.mixins.agent_mixin import AgentMixin
from src.mixins.input_mixin import InputMixin
from src.mixins.processor import ProcessorMixin
from typing import Any, Union, Tuple, Dict, Optional, List
from hashlib import sha256
from collections import deque, defaultdict

class ExecutionGraphNode:
    id: str
    children: Optional[List[str]]
    parents: Optional[List[str]]


class OrchestratorMixin:

    agents: Dict[str, AgentMixin]
    message_queue: Dict[str, List[Dict[str, Any]]]

    def __init__(self, name: str):
        self.name = name 
        self.agents = {}
        self.event_mapping = {}
        self.message_queue = defaultdict(list)

    def register_agent(self, agent: AgentMixin):
        agent_id = f"{agent.name}"
        agent.set_agent_context_id(sha256(agent_id.encode()).hexdigest())
        self.agents[agent.id] = agent
        agent.register_orchestrator(self)


        self.message_queue[agent.id] = [{message: callback.__name__} for messages, callbacks in agent.ingress_messages_callbacks.items() for message in messages.split(',') for callback in callbacks]

    def __check_if_all_messages_received(self, event_message: Dict[str, Any]) -> bool:
        for message in event_message.values():
            if message is None:
                return False
        return True
    
    def __check_if_all_messages_received(self, callback_name: str, event_message: Dict[str, Any]) -> bool:
        for data_callback in event_message.values():
            if data_callback[1] != callback_name:
                continue
            if data_callback[0] is None:
                return False
        return True

    def write_message(self, message: Message):
        # Get the list of agent IDs subscribed to this message type
        agent_ids = self.message_queue.keys()
        print(f"Message queue : {self.message_queue}")
        # Process message for each subscribed agent
        for agent_id in list(agent_ids):
            print(f"Running agent : {self.agents[agent_id]}")
            agent = self.agents[agent_id]

            if message.name in self.message_queue[agent_id]:
                for event_message in self.message_queue[agent_id]:
                    # If this message slot is empty, store the message data
                    print(f"Event message : {event_message}")
                    print(f"Agent : {agent.name}")
                    getattr(agent, event_message[message.name])(data=message.data)
