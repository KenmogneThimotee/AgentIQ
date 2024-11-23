# Start orchestrator on one machine
from src.agent_client import AgentClient
from src.helpers.orchestrator import Message

# On another machine, start an agent
agent = AgentClient(
    name="agent1",
    orchestrator_host="127.0.0.1"
)

# Subscribe to messages
@agent.on_receive_message("test_message")
def handle_test(data):
    print(f"Agent 1 received: {data}")

# Start the agent
agent.start()


# # Cleanup
# try:
#     # Your main logic here
#     pass
# finally:
#     agent.stop()
