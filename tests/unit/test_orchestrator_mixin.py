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
