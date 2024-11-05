
from enum import Enum


class NotificationType(Enum):
    SUCCESS = "success"
    ERROR = "error"

class AgentState(Enum):
    INITIALIZED = "initialized"
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
