from pydantic.fields import Any

class InputMixin:
    """Mixin for input handling."""

    input: Any

    def __init__(self):
        self.input = None 

    def set_input(self, input: Any) -> None:
        self.input = input 

    def get_input(self) -> Any:
        return self.input 