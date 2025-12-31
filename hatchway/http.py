import json
from typing import Generic, TypeVar

import msgspec
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse

T = TypeVar("T")


class ApiResponse(Generic[T], HttpResponse):
    """
    A way to return extra information with a response if you want
    headers, etc.
    """

    def __init__(
        self,
        data: T,
        encoder=DjangoJSONEncoder,
        json_dumps_params: dict[str, object] | None = None,
        finalize: bool = False,
        **kwargs
    ):
        self.data = data
        self.encoder = encoder
        self.json_dumps_params = json_dumps_params or {}
        kwargs.setdefault("content_type", "application/json")
        super().__init__(content=b"(unfinalised)", **kwargs)
        if finalize:
            self.finalize()

    def finalize(self):
        """
        Converts whatever our current data is into HttpResponse content
        """
        # Use msgspec for faster JSON encoding instead of stdlib json
        # Falls back to json.dumps if encoder is customized
        if self.encoder == DjangoJSONEncoder and not self.json_dumps_params:
            self.content = msgspec.json.encode(self.data)
        else:
            self.content = json.dumps(
                self.data, cls=self.encoder, **self.json_dumps_params
            )


class ApiError(BaseException):
    """
    A handy way to raise an error with JSONable contents
    """

    def __init__(self, status: int, error: str):
        self.status = status
        self.error = error
