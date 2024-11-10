from src.mixins.agent_mixin import AgentMixin


class MyAgent(AgentMixin):
    pass

agent = MyAgent("test", received_messages=["hello", "goodbye"])
agent.set_agent_context_id("test_context")
@agent.on_receive_message("hello")
def handle_hello(self, data):
    print(f"Got hello with data: {data}")

@agent.on_receive_message("goodbye")
def handle_goodbye(self, data):
    print(f"Got goodbye with data: {data}")

@agent.emit_message("hello")
def emit_hello(data):
    print(f"Emitting hello with data: {data}")
    return data

agent.emit_hello(data={"test": "world"})


# Handlers are available immediately after creation
# handlers = agent.ingress_messages_callbacks
# print(handlers)
# Output will be something like:
# {
#     'hello': {'method_name': 'handle_hello', 'method': <bound method MyAgent.handle_hello>},
#     'goodbye': {'method_name': 'handle_goodbye', 'method': <bound method MyAgent.handle_goodbye>}
# }