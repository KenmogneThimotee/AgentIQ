
from pydantic.fields import Any

class ResultMixin:
    """Mixin for result handling."""

    result: Any
    
    def __init__(self):
        self.result = None

    def get_result(self):

        return self.result 