
from typing import Any


class ProcessorMixin:

    def process(self, data: Any) -> Any:
        return data