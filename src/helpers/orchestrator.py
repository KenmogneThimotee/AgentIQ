
from typing import Any


class Message:
    name: str
    data: Any
    agent_name: str
    agent_id: str

    def __init__(self, name: str, data: Any, agent_name: str=None, agent_id: str=None):
        self.name = name
        self.data = data
        self.agent_name = agent_name
        self.agent_id = agent_id


