"""Integration of Dispatch programmable endpoints for FastAPI.

Example:

    import fastapi
    import dispatch.fastapi

    app = fastapi.FastAPI()
    dispatch.fastapi.configure(app, api_key="test-key")

    @app.dispatch_coroutine()
    def my_cool_coroutine():
        return "Hello World!"

    @app.get("/")
    def read_root():
        my_cool_coroutine.call()
"""

import ring.coroutine.v1.coroutine_pb2
from collections.abc import Callable
from typing import Any
import os
import fastapi
import fastapi.responses
import google.protobuf.wrappers_pb2
import dispatch.coroutine


def configure(
    app: fastapi.FastAPI,
    api_key: None | str = None,
    mount_path: str = "/dispatch",
):
    """Configure the FastAPI app to use Dispatch programmable endpoints.

    It mounts a sub-app at the given mount path that implements the Dispatch
    interface. It also adds a a decorator named @app.dispatch_coroutine() to
    register coroutines.

    Args:
        app: The FastAPI app to configure.
        api_key: Dispatch API key to use for authentication. Uses the value of
          the DISPATCH_API_KEY environment variable by default.
        mount_path: The path to mount Dispatch programmable endpoints at.

    Raises:
        ValueError: If any of the required arguments are missing.
    """
    api_key = api_key or os.environ.get("DISPATCH_API_KEY")

    if not app:
        raise ValueError("app is required")
    if not api_key:
        raise ValueError("api_key is required")
    if not mount_path:
        raise ValueError("mount_path is required")

    dispatch_app = _new_app()

    app.__setattr__("dispatch_coroutine", dispatch_app.dispatch_coroutine)
    app.mount(mount_path, dispatch_app)


class _DispatchAPI(fastapi.FastAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._coroutines = {}

    def dispatch_coroutine(self):
        """Register a coroutine with the Dispatch programmable endpoints.

        Args:
            app: The FastAPI app to register the coroutine with.
            coroutine: The coroutine to register.

        Raises:
            ValueError: If the coroutine is already registered.
        """

        def wrap(func: Callable[[dispatch.coroutine.Input], dispatch.coroutine.Output]):
            coro = dispatch.coroutine.Coroutine(func)
            if coro.uri in self._coroutines:
                raise ValueError(f"Coroutine {coro.uri} already registered")
            self._coroutines[coro.uri] = coro
            return coro

        return wrap


class _GRPCResponse(fastapi.Response):
    media_type = "application/grpc+proto"


def _new_app():
    app = _DispatchAPI()
    app._coroutines = {}

    @app.get("/", response_class=fastapi.responses.PlainTextResponse)
    def read_root():
        return "ok"

    @app.post(
        # The endpoint for execution is hardcoded at the moment. If the service
        # gains more endpoints, this should be turned into a dynamic dispatch
        # like the official gRPC server does.
        "/ring.coroutine.v1.ExecutorService/Execute",
        response_class=_GRPCResponse,
    )
    async def execute(request: fastapi.Request):
        # Raw request body bytes are only available through the underlying
        # starlette Request object's body method, which returns an awaitable,
        # forcing execute() to be async.
        data: bytes = await request.body()

        req = ring.coroutine.v1.coroutine_pb2.ExecuteRequest.FromString(data)

        # TODO: be more graceful. This will crash if the coroutine is not found,
        # and the coroutine version is not taken into account.
        coroutine = app._coroutines[
            dispatch.coroutine._coroutine_uri_to_qualname(req.coroutine_uri)
        ]

        coro_input = dispatch.coroutine.Input(req)
        output = coroutine(coro_input)

        if not isinstance(output, dispatch.coroutine.Output):
            raise ValueError(
                f"coroutine output should be an instance of {dispatch.coroutine.Output}, not {type(output)}"
            )

        resp = output._message
        resp.coroutine_uri = req.coroutine_uri
        resp.coroutine_version = req.coroutine_version

        return fastapi.Response(content=resp.SerializeToString())

    return app
