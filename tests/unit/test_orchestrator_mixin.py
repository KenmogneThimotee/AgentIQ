import pytest
from src.mixins.orchestrator import OrchestratorMixin, Message
from src.mixins.agent_mixin import AgentMixin
from src.helpers.agents import AgentState

class TestOrchestratorMixin:
    @pytest.fixture
    def orchestrator(self):
        return OrchestratorMixin(name="test_orchestrator")

    @pytest.fixture 
    def test_agent(self):
        agent = AgentMixin(name="test_agent")
        
        @agent.on_receive_message(["test_message"])
        def handle_message(data):
            return data
            
        return agent

    def test_register_agent(self, orchestrator, test_agent):
        # Test agent registration
        orchestrator.register_agent(test_agent)
        
        # Verify agent was added to orchestrator
        assert test_agent.id in orchestrator.agents
        assert orchestrator.agents[test_agent.id] == test_agent
        
        # Verify message queue was initialized
        assert test_agent.id in orchestrator.message_queue
        assert len(orchestrator.message_queue[test_agent.id]) == 1

    def test_write_message(self, orchestrator, test_agent):
        orchestrator.register_agent(test_agent)

        # Create test message
        test_data = {"test": "data"}
        message = Message(name="test_message", data=test_data)
        
        # Write message
        orchestrator.write_message(message)

        # Verify message was processed
        assert len(orchestrator.message_queue[test_agent.id]) == 1

    def test_multiple_agents(self, orchestrator):
        # Create multiple test agents
        agent1 = AgentMixin(name="agent1")
        agent2 = AgentMixin(name="agent2")
        
        @agent1.on_receive_message(["msg"])
        def handle_1(data):
            return data
            
        @agent2.on_receive_message(["msg"]) 
        def handle_2(data):
            return data

        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)

        # Write message that both agents handle
        message = Message(name="msg", data={"test": "data"})
        orchestrator.write_message(message)

        # Verify both agents processed message
        assert len(orchestrator.message_queue[agent1.id]) == 1
        assert len(orchestrator.message_queue[agent2.id]) == 1

    def test_agent_context_id(self, orchestrator, test_agent):
        # Test that agent gets assigned context ID on registration
        orchestrator.register_agent(test_agent)
        assert test_agent.agent_context_id is not None
        
        # Verify ID matches what's stored in orchestrator
        assert test_agent.id in orchestrator.agents

    def test_orchestrator_initialization(self):
        name = "test_orchestrator"
        orchestrator = OrchestratorMixin(name=name)
        
        assert orchestrator.name == name
        assert orchestrator.agents == {}
        assert orchestrator.event_mapping == {}
        assert len(orchestrator.message_queue) == 0
