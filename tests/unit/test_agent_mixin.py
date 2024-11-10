from collections import defaultdict
import pytest
from unittest.mock import Mock, patch
from src.mixins.agent_mixin import AgentMixin
from src.helpers.agents import AgentState, NotificationType
from src.helpers.orchestrator import Message


class TestAgentMixin:
    @pytest.fixture
    def agent(self):
        return AgentMixin(name="test_agent")

    def test_init(self, agent):
        assert agent.name == "test_agent"
        assert agent.agent_context_id is None
        assert agent.state == AgentState.INITIALIZED
        assert isinstance(agent.ingress_messages_callbacks, defaultdict)

    def test_set_agent_context_id(self, agent):
        agent.set_agent_context_id("test_id")
        assert agent.agent_context_id == "test_id"
        assert agent.id == "test_id"

    def test_id_raises_error_when_not_set(self, agent):
        with pytest.raises(ValueError, match="Agent context ID has not been set"):
            _ = agent.id

    def test_state_properties(self, agent):
        # Test initialized state
        assert agent.is_initialized is True
        assert agent.is_idle is False
        assert agent.is_running is False
        assert agent.is_success is False
        assert agent.is_error is False

        # Change state and test
        agent.state = AgentState.IDLE
        assert agent.is_initialized is False
        assert agent.is_idle is True

        agent.state = AgentState.RUNNING
        assert agent.is_running is True

        agent.state = AgentState.SUCCESS
        assert agent.is_success is True

        agent.state = AgentState.ERROR
        assert agent.is_error is True

    def test_register_orchestrator(self, agent):
        mock_orchestrator = Mock()
        agent.register_orchestrator(mock_orchestrator)
        assert agent.orchestrator == mock_orchestrator

    def test_send_message(self, agent):
        mock_orchestrator = Mock()
        agent.register_orchestrator(mock_orchestrator)
        agent.set_agent_context_id("test_id")

        message = Message(name="test_message", data={"test": "data"})
        agent.send_message(message)

        assert message.agent_name == "test_agent"
        assert message.agent_id == "test_id"
        mock_orchestrator.write_message.assert_called_once_with(message)

    def test_on_receive_message_decorator(self, agent):
        @agent.on_receive_message(["test_message"])
        def handle_message(data):
            return data

        assert "test_message" in agent.ingress_messages_callbacks
        assert agent.handle_message in agent.ingress_messages_callbacks["test_message"]
        assert hasattr(agent, "handle_message")

    def test_emit_message_decorator(self, agent):
        mock_orchestrator = Mock()
        agent.register_orchestrator(mock_orchestrator)
        agent.set_agent_context_id("test_id")

        @agent.emit_message(["test_message"])
        def emit_message(data):
            return data

        test_data = {"test": "data"}
        agent.emit_message(test_data)

        expected_message = Message(
            name="test_message",
            data=test_data,
            agent_name="test_agent",
            agent_id="test_id"
        )
        mock_orchestrator.write_message.assert_called_once()
