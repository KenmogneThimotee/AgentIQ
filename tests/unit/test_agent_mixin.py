import pytest
from unittest.mock import Mock

from src.helpers.agents import AgentState, NotificationType
from src.helpers.orchestrator import Message
from src.mixins.agent_mixin import AgentMixin
from src.mixins.orchestrator import OrchestratorMixin

class TestAgentMixin:
    @pytest.fixture
    def agent(self):
        agent = AgentMixin(name="test_agent")
        return agent
    
    @pytest.fixture
    def orchestrator(self):
        orchestrator = Mock(spec=OrchestratorMixin)
        orchestrator.name = "test_orchestrator"
        orchestrator.agents = {}
        orchestrator.event_mapping = {}
        return orchestrator

    def test_initialization(self, agent):
        assert agent.name == "test_agent"
        assert not hasattr(agent, 'orchestrator')
        
    def test_register_orchestrator(self, agent, orchestrator):
        agent.register_orchestrator(orchestrator)
        assert agent.orchestrator == orchestrator
        
    def test_set_and_get_agent_context_id(self, agent):
        agent.set_agent_context_id("test_context_id")
        assert agent.agent_context_id == "test_context_id"
        assert agent.id == "test_context_id"
        
    def test_id_property_raises_error_when_not_set(self, agent):
        with pytest.raises(ValueError, match="Agent context ID has not been set"):
            _ = agent.id
            
    def test_state_properties(self, agent):
        # Test all state properties
        agent.state = AgentState.INITIALIZED
        assert agent.is_initialized is True
        assert agent.is_idle is False
        
        agent.state = AgentState.IDLE
        assert agent.is_idle is True
        assert agent.is_initialized is False
        
        agent.state = AgentState.RUNNING
        assert agent.is_running is True
        
        agent.state = AgentState.SUCCESS
        assert agent.is_success is True
        
        agent.state = AgentState.ERROR
        assert agent.is_error is True
        
    def test_notify(self, agent, orchestrator):
        agent.register_orchestrator(orchestrator)
        agent.set_agent_context_id("test_id")
        agent.notify(NotificationType.SUCCESS)
        orchestrator.update_execution_graph_state.assert_called_once_with(
            "test_id", NotificationType.SUCCESS
        )
        
    def test_send_message(self, orchestrator):
        agent = AgentMixin(name="test_agent")
        agent.register_orchestrator(orchestrator)
        agent.set_agent_context_id("test_id")
        orchestrator.agents["test_id"] = agent
        orchestrator.event_mapping["test_message"] = set(["test_id"])
        message = Message(data="test", name="test_message")
        agent.send_message(message)
        orchestrator.write_message.assert_called_once_with(message)
        
    def test_run(self, agent, orchestrator):
        agent.register_orchestrator(orchestrator)
        agent.set_agent_context_id("test_id")
        
        test_input = "test_input"
        agent.run(test_input)
        
        assert agent.state == AgentState.SUCCESS
        assert agent.get_result() == test_input
        orchestrator.update_execution_graph_state.assert_called_once_with(
            "test_id", NotificationType.SUCCESS
        ) 