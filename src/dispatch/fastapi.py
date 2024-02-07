"""Integration of Dispatch programmable endpoints for FastAPI.

Example:

    import fastapi
    import dispatch.fastapi

    app = fastapi.FastAPI()
    dispatch.fastapi.configure(app, api_key="test-key")

    @app.dispatch_function()
    def my_function():
        return "Hello World!"

    @app.get("/")
    def read_root():
        my_function.call()
"""

import os
from collections.abc import Callable
from typing import Dict

import fastapi
import fastapi.responses
from httpx import _urlparse

import dispatch.function
from dispatch.sdk.v1 import function_pb2 as function_pb


def configure(
    app: fastapi.FastAPI,
    public_url: str,
):
    """Configure the FastAPI app to use Dispatch programmable endpoints.

    It mounts a sub-app that implements the Dispatch gRPC interface. It also
    adds a a decorator named @app.dispatch_function() to register functions.

    Args:
        app: The FastAPI app to configure.
        public_url: Full URL of the application the dispatch programmable
          endpoint will be running on.

    Raises:
        ValueError: If any of the required arguments are missing.
    """
    if not app:
        raise ValueError("app is required")
    if not public_url:
        raise ValueError("public_url is required")

    parsed_url = _urlparse.urlparse(public_url)
    if not parsed_url.netloc or not parsed_url.scheme:
        raise ValueError("public_url must be a full URL with protocol and domain")

    dispatch_app = _new_app(public_url)

    app.__setattr__("dispatch_function", dispatch_app.dispatch_function)
    app.mount("/dispatch.sdk.v1.FunctionService", dispatch_app)


class _DispatchAPI(fastapi.FastAPI):
    def __init__(self, endpoint: str):
        super().__init__()
        self._functions: Dict[str, dispatch.function.Function] = {}
        self._endpoint = endpoint

    def dispatch_function(self):
        """Register a function with the Dispatch programmable endpoints.

        Args:
            app: The FastAPI app to register the function with.
            function: The function to register.

        Raises:
            ValueError: If the function is already registered.
        """

        def wrap(func: Callable[[dispatch.function.Input], dispatch.function.Output]):
            name = func.__qualname__
            wrapped_func = dispatch.function.Function(self._endpoint, name, func)
            if name in self._functions:
                raise ValueError(f"Function {name} already registered")
            self._functions[name] = wrapped_func
            return wrapped_func

        return wrap


class _GRPCResponse(fastapi.Response):
    media_type = "application/grpc+proto"


def _new_app(endpoint: str):
    app = _DispatchAPI(endpoint)

    @app.post(
        # The endpoint for execution is hardcoded at the moment. If the service
        # gains more endpoints, this should be turned into a dynamic dispatch
        # like the official gRPC server does.
        "/Run",
        response_class=_GRPCResponse,
    )
    async def execute(request: fastapi.Request):
        # Raw request body bytes are only available through the underlying
        # starlette Request object's body method, which returns an awaitable,
        # forcing execute() to be async.
        data: bytes = await request.body()

        req = function_pb.RunRequest.FromString(data)

        if not req.function:
            raise fastapi.HTTPException(status_code=400, detail="function is required")

        # TODO: be more graceful. This will crash if the coroutine is not found,
        # and the coroutine version is not taken into account.

        try:
            func = app._functions[req.function]
        except KeyError:
            # TODO: integrate with logging
            raise fastapi.HTTPException(
                status_code=404, detail=f"Function '{req.function}' does not exist"
            )

        input = dispatch.function.Input(req)

        try:
            output = func(input)
        except Exception as ex:
            # TODO: distinguish uncaught exceptions from exceptions returned by
            # coroutine?
            err = dispatch.function.Error.from_exception(ex)
            output = dispatch.function.Output.error(err)

        resp = output._message

        return fastapi.Response(content=resp.SerializeToString())

    return app
