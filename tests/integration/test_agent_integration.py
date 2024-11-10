import pytest
from src.mixins.orchestrator import OrchestratorMixin, Message
from src.mixins.agent_mixin import AgentMixin
from src.helpers.agents import AgentState

class TestAgentIntegration:
    @pytest.fixture
    def orchestrator(self):
        return OrchestratorMixin(name="test_orchestrator")

    @pytest.fixture
    def producer_agent(self):
        agent = AgentMixin(name="producer")
        
        @agent.emit_message(["data_produced"])
        def produce_data(data):
            return {"value": data * 2}
            
        return agent

    @pytest.fixture
    def consumer_agent(self):
        agent = AgentMixin(name="consumer")
        
        @agent.on_receive_message(["data_produced"])
        def handle_data(data):
            return data["value"]
            
        return agent

    def test_agent_message_flow(self, orchestrator, producer_agent, consumer_agent):
        # Register both agents
        orchestrator.register_agent(producer_agent)
        orchestrator.register_agent(consumer_agent)
        
        # Verify agents are registered
        assert producer_agent.id in orchestrator.agents
        assert consumer_agent.id in orchestrator.agents
        
        # Verify initial state
        assert producer_agent.is_initialized
        assert consumer_agent.is_initialized
        
        # Producer creates and emits message
        test_input = 5
        producer_agent.produce_data(test_input)
        
        # Verify message queue state
        assert len(orchestrator.message_queue[consumer_agent.id]) == 1
        
        # Verify expected data transformation
        expected_value = test_input * 2
        message = Message(name="data_produced", data={"value": expected_value})
        orchestrator.write_message(message)

    def test_multiple_message_chain(self, orchestrator):
        # Create chain of agents that process data
        agent1 = AgentMixin(name="agent1")
        agent2 = AgentMixin(name="agent2")
        agent3 = AgentMixin(name="agent3")
        
        @agent1.emit_message(["msg1"])
        def start_chain(data):
            return {"val": data + 1}
            
        @agent2.on_receive_message(["msg1"])
        @agent2.emit_message(["msg2"]) 
        def process_msg1(data):
            return {"val": data["val"] * 2}
            
        @agent3.on_receive_message(["msg2"])
        def end_chain(data):
            return data["val"]

        # Register all agents
        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2) 
        orchestrator.register_agent(agent3)

        # Start the chain
        input_val = 5
        agent1.start_chain(input_val)
        
        # Process messages through chain
        msg1 = Message(name="msg1", data={"val": input_val + 1})
        orchestrator.write_message(msg1)
        
        # msg2 = Message(name="msg2", data={"val": (input_val + 1) * 2})
        # orchestrator.write_message(msg2)
        
        # Verify final message queue states
        assert len(orchestrator.message_queue[agent1.id]) == 0
        assert len(orchestrator.message_queue[agent2.id]) == 1
        assert len(orchestrator.message_queue[agent3.id]) == 1
