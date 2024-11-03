from pydantic import AbstractBaseModel

class ProcessorMixin(AbstractBaseModel):

    def process(data: Union[ResultMixin, InputMixin]) -> Union[ResultMixin, InputMixin]:
        return data