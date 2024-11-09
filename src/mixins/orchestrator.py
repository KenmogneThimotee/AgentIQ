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
    event_mapping: Dict[str, List[str]]
    message_queue: Dict[str, List[Dict[str, Any]]]

    def __init__(self, name: str):
        self.name = name 
        self.agents = {}
        self.event_mapping = {}
        self.message_queue = defaultdict(list({}))
        
    def update_execution_graph_state(self, agent_id: str, notification_type: NotificationType) -> None:
        # Handle successful agent completion
        if notification_type == NotificationType.SUCCESS:
            agent = self.agents[agent_id]
            if agent.is_success:
                #TODO: Implement
                print(f"Agent {agent_id} completed successfully")
                pass

    def register_agent(self, agent: AgentMixin):
        agent_id = f"{agent.name}"
        agent.set_agent_context_id(sha256(agent_id.encode()).hexdigest())
        self.agents[agent.id] = agent
        agent.register_orchestrator(self)

        for message in agent.get_ingress_messages():
            try:
                self.event_mapping[message].add(agent.id)
            except:
                self.event_mapping[message] = set([agent.id])

        self.message_queue[agent.id] = [{message: None} for message in agent.get_ingress_messages()]
    
    def __check_if_all_messages_received(self, event_message: Dict[str, Any]) -> bool:
        for message in event_message.values():
            if message is None:
                return False
        return True

    def write_message(self, message: Message):
        # Get the list of agent IDs subscribed to this message type
        try:
            agent_ids = self.event_mapping[message.name]
        except:
            raise ValueError("No agent for this event")
        
        # Process message for each subscribed agent
        for agent_id in list(agent_ids):
            print(f"Running agent : {self.agents[agent_id]}")
            agent = self.agents[agent_id]

            # If agent processes messages independently, call its callback directly
            if agent.process_ingress_independently:
                agent.get_ingress_messages_callbacks[message.name](message)
            else:
                # Otherwise check message queue for this agent
                for index, event_message in enumerate(self.message_queue[agent_id]):
                    # If this message slot is empty, store the message data
                    if not event_message[message.name]:
                        event_message[message.name] = message.data
                        break

                    # If all required messages are received, process them
                    if self.__check_if_all_messages_received(event_message):
                        # Remove processed message set from queue
                        self.message_queue[agent_id].pop(index)
                        # Run agent with collected message data
                        agent.run(event_message.values())
