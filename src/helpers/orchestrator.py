
from typing import Any


class Message:
    name: str
    data: Any
    agent_name: str
    agent_id: str

    def __init__(self, name: str, data: Any):
        self.name = name
        self.data = data


