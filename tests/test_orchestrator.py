import pytest
from unittest.mock import Mock, patch
from src.mixins.orchestrator import OrchestratorMixin
from src.helpers.agents import NotificationType
from src.mixins.agent_mixin import AgentMixin
from mailbox import Message

class TestOrchestratorMixin:
    @pytest.fixture
    def orchestrator(self):
        return OrchestratorMixin(name="test_orchestrator")

    @pytest.fixture
    def mock_agent(self):
        agent = Mock(spec=AgentMixin)
        agent.name = "test_agent"
        agent.is_success = True
        return agent

    # Unit Tests
    def test_init(self, orchestrator):
        assert orchestrator.name == "test_orchestrator"
        assert orchestrator.agents == {}
        assert orchestrator.event_mapping == {}

    def test_register_agent(self, orchestrator, mock_agent):
        messages = ["test_message"]
        orchestrator.register_agent(mock_agent, messages)
        
        print(mock_agent.id)
        assert mock_agent.id in orchestrator.agents
        assert mock_agent.id in orchestrator.event_mapping["test_message"]
        mock_agent.register_orchestrator.assert_called_once_with(orchestrator)

    def test_write_message_success(self, orchestrator, mock_agent):
        messages = ["test_message"]
        orchestrator.register_agent(mock_agent, messages)
        
        message = Mock(spec=Message)
        message.name = "test_message"
        message.data = {"test": "data"}
        
        orchestrator.write_message(message)
        mock_agent.run.assert_called_once_with(message.data)

    def test_write_message_invalid_event(self, orchestrator):
        message = Mock(spec=Message)
        message.name = "invalid_message"
        
        with pytest.raises(ValueError, match="No agent for this event"):
            orchestrator.write_message(message)

    # Integration Tests
    class MockAgent(AgentMixin):
        def __init__(self, name):
            self.name = name
            self.run_called = False
            
        def run(self, data):
            self.run_called = True
            return True

    def test_full_orchestration_flow(self, orchestrator):
        # Create real agents
        agent1 = self.MockAgent("agent1")
        agent2 = self.MockAgent("agent2")
        
        # Register agents with different message types
        orchestrator.register_agent(agent1, ["message1"])
        orchestrator.register_agent(agent2, ["message2"])
        
        # Create and send messages
        message1 = Mock(spec=Message)
        message1.name = "message1"
        message1.data = {"test": "data1"}
        
        message2 = Mock(spec=Message)
        message2.name = "message2"
        message2.data = {"test": "data2"}
        
        # Test message routing
        orchestrator.write_message(message1)
        assert agent1.run_called
        assert not agent2.run_called
        
        orchestrator.write_message(message2)
        assert agent2.run_called 