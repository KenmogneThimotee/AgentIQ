# Start orchestrator on one machine
from src.agent_client import AgentClient
from src.helpers.orchestrator import Message
from src.orchestrator import Orchestrator
import time

# Start orchestrator
orchestrator = Orchestrator("main_orchestrator")
orchestrator.start()

# # Create and start an agent
agent = AgentClient("test_agent", "127.0.0.1")
@agent.on_receive_message(["test_message"])
@agent.emit_message(["test_message"])
def handle_test(data):
    print(f"Agent 1 received: {data}")

agent.start()

# Send test message
orchestrator.broadcast_message(Message(name="test_message", data={"test": "data"}))

# Keep the program running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    agent.stop()