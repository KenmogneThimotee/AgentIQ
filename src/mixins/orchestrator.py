from copy import deepcopy
from src.helpers.agents import NotificationType
from src.helpers.orchestrator import Message
from src.mixins.agent_mixin import AgentMixin
from src.mixins.input_mixin import InputMixin
from src.mixins.processor import ProcessorMixin
from typing import Any, Union, Tuple, Dict, Optional, List
from hashlib import sha256

class ExecutionGraphNode:
    id: str
    children: Optional[List[str]]
    parents: Optional[List[str]]


class OrchestratorMixin:

    agents: Dict[str, AgentMixin]
    event_mapping: Dict[str, List[str]]

    def __init__(self, name: str):
        self.name = name 
        self.agents = {}
        self.event_mapping = {}

    def update_execution_graph_state(self, agent_id: str, notification_type: NotificationType) -> None:
        # Handle successful agent completion
        if notification_type == NotificationType.SUCCESS:
            agent = self.agents[agent_id]
            if agent.is_success:
                #TODO: Implement
                print(f"Agent {agent_id} completed successfully")
                pass


    def register_agent(self, agent: AgentMixin, messages: List[str]):
        agent_id = f"{agent.name}"
        agent.set_agent_context_id(sha256(agent_id.encode()).hexdigest())
        self.agents[agent.id] = agent
        agent.register_orchestrator(self)

        for message in messages:
            try:
                self.event_mapping[message].add(agent.id)
            except:
                self.event_mapping[message] = set([agent.id])
    
    def write_message(self, message: Message):
        try:
            agent_ids = self.event_mapping[message.name]
        except:
            raise ValueError("No agent for this event")
        
        for agent_id in list(agent_ids):
            print(f"Running agent : {self.agents[agent_id]}")
            self.agents[agent_id].run(message.data)
