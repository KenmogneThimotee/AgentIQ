from copy import deepcopy
import uuid
from mixins.agent_mixin import AgentMixin, NotificationType
from mixins.input_mixin import InputMixin
from .processor import ProcessorMixin
from typing import Any, Union, Tuple, Dict, Optional, List
from pydantic import AbstractBaseModel, BaseModel
from hashlib import sha256
from collections import sta

class ExecutionGraphNode(BaseModel):
    id: str
    children: Optional[List[str]]
    parents: Optional[List[str]]
    
class OrchestratorMixin(AbstractBaseModel):
    """Mixin for orchestrator handling."""

    name: str
    agents: Dict[str, AgentMixin]

    nodes: List[ExecutionGraphNode]
    execution_graph: Dict[str, ExecutionGraphNode]
    current_node: ExecutionGraphNode

    roots: Dict[str, ExecutionGraphNode]


    def __init__(self, name: str):
        self.name = name 
        self.execution_graph = None

    @property
    def copy(self) -> 'OrchestratorMixin':
        self_copy = deepcopy(self)
        self_copy.execution_graph = deepcopy(self.execution_graph)
        self_copy.nodes = deepcopy(self.nodes)
        self_copy.roots = deepcopy(self.roots)
        self_copy.current_node = deepcopy(self.current_node)
        self_copy.agents = self.agents
        return self_copy

    def register_agent(self, agent: AgentMixin):
        agent_id = f"{agent.name}"
        agent.set_agent_context_id(sha256(agent_id.encode()).hexdigest())
        self.agents[agent.id] = agent
        agent.register_orchestrator(self)


    def initialize(self, agent: AgentMixin) -> 'OrchestratorMixin':
        self.execution_graph[agent.id] = ExecutionGraphNode(id=agent.id, children=[], parents=[])
        self.roots[agent.id] = self.execution_graph[agent.id]
        self.nodes.append(self.execution_graph[agent.id])
        return self.copy

    
    def next(self, agent: AgentMixin) -> 'OrchestratorMixin':
        """
        Set the next agent to run.

        Args:
            agent_config: The next agent to run.
                format:
                    dict: {agent_context_id: processor}
        Returns:
            The orchestrator.
        """

        parent_node = self.nodes[-1]
        # Add the current agent as a child of the previous node
        parent_node.children.append(agent.id)

        # Create a new execution graph node for this agent
        node_graph = self.execution_graph[agent.id]

        # Set the parent of this node to the previous execution graph node
        node_graph.parents.append(parent_node.id)

        return self.copy

    def update_execution_graph_state(self, agent_id: str, notification_type: NotificationType) -> None:
        # Handle successful agent completion
        if notification_type == NotificationType.SUCCESS:
            agent = self.agents[agent_id]
            if agent.is_success:
                # Get all child nodes that should run next
                children = self.execution_graph[agent_id].children
                for child in children:
                    # Check if all parent nodes of this child have completed successfully
                    parents = self.execution_graph[child].parents
                    for parent in parents:
                        if not parent.is_success:
                            break
                    else:
                        # All parents succeeded, run the child node with parent results
                        child.run([agt.get_result() for agt in parents])

    def run(self, inputs: Dict[str, Any]) -> None:
        
        for id, input in inputs.items():
            execution_graph_node = self.roots[id]
            agent = self.agents[execution_graph_node.id]
            agent.run(input)
        
