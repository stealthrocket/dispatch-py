import asyncio
import json
import threading
import unittest
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Coroutine, Dict, Optional, TypeVar

import aiohttp
from aiohttp import web
from google.protobuf.timestamp_pb2 import Timestamp
from typing_extensions import ParamSpec

import dispatch.experimental.durable.registry
from dispatch.function import Client as BaseClient
from dispatch.function import (
    ClientError,
    Input,
    Output,
    Registry,
    default_registry,
    set_default_registry,
)
from dispatch.http import Dispatch, FunctionService
from dispatch.http import Server as BaseServer
from dispatch.sdk.v1.call_pb2 import Call, CallResult
from dispatch.sdk.v1.dispatch_pb2 import DispatchRequest, DispatchResponse
from dispatch.sdk.v1.error_pb2 import Error
from dispatch.sdk.v1.function_pb2 import RunRequest, RunResponse
from dispatch.sdk.v1.poll_pb2 import PollResult
from dispatch.sdk.v1.status_pb2 import STATUS_OK

from .client import EndpointClient
from .server import DispatchServer
from .service import DispatchService

__all__ = [
    "EndpointClient",
    "DispatchServer",
    "DispatchService",
    "function",
    "method",
    "main",
    "run",
    "Client",
    "Server",
    "Service",
    "Registry",
    "DISPATCH_ENDPOINT_URL",
    "DISPATCH_API_URL",
    "DISPATCH_API_KEY",
]

P = ParamSpec("P")
T = TypeVar("T")

DISPATCH_ENDPOINT_URL = "http://127.0.0.1:0"
DISPATCH_API_URL = "http://127.0.0.1:0"
DISPATCH_API_KEY = "916CC3D280BB46DDBDA984B3DD10059A"


class Client(BaseClient):
    def session(self) -> aiohttp.ClientSession:
        # Use an individual sessionn in the test client instead of the default
        # global session from dispatch.http so we don't crash when a different
        # event loop is employed in each test.
        return aiohttp.ClientSession()


class Server(BaseServer):
    def __init__(self, app: web.Application):
        super().__init__("127.0.0.1", 0, app)

    @property
    def url(self):
        return f"http://{self.host}:{self.port}"


class Service(web.Application):
    tasks: Dict[str, asyncio.Task]
    _session: Optional[aiohttp.ClientSession] = None

    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        super().__init__()
        self.dispatch_ids = (str(i) for i in range(2**32 - 1))
        self.tasks = {}
        self.add_routes(
            [
                web.post(
                    "/dispatch.sdk.v1.DispatchService/Dispatch",
                    self.handle_dispatch_request,
                ),
                web.post(
                    "/dispatch.sdk.v1.DispatchService/Wait",
                    self.handle_wait_request,
                ),
            ]
        )

    async def close(self):
        await self.session.close()

    async def authenticate(self, request: web.Request):
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            raise web.HTTPUnauthorized(text="missing authentication token")

        token = auth[len("Bearer ") :]
        if token != DISPATCH_API_KEY:
            raise web.HTTPUnauthorized(text="invalid authentication token")

    async def handle_dispatch_request(self, request: web.Request):
        await self.authenticate(request)
        req = DispatchRequest.FromString(await request.read())
        res = await self.dispatch(req)
        return web.Response(
            content_type="application/proto", body=res.SerializeToString()
        )

    async def handle_wait_request(self, request: web.Request):
        await self.authenticate(request)
        req = str(await request.read(), "utf-8")
        res = await self.wait(req)
        return web.Response(
            content_type="application/proto", body=res.SerializeToString()
        )

    async def dispatch(self, req: DispatchRequest) -> DispatchResponse:
        dispatch_ids = [next(self.dispatch_ids) for _ in req.calls]

        for call, dispatch_id in zip(req.calls, dispatch_ids):
            self.tasks[dispatch_id] = asyncio.create_task(
                self.call(call, dispatch_id),
                name=f"dispatch:{dispatch_id}",
            )

        return DispatchResponse(dispatch_ids=dispatch_ids)

    # TODO: add to protobuf definitions
    async def wait(self, dispatch_id: str) -> CallResult:
        task = self.tasks[dispatch_id]
        return await task

    async def call(
        self,
        call: Call,
        dispatch_id: str,
        parent_dispatch_id: Optional[str] = None,
        root_dispatch_id: Optional[str] = None,
    ) -> CallResult:
        root_dispatch_id = root_dispatch_id or dispatch_id

        now = datetime.now()
        exp = now + (
            timedelta(
                seconds=call.expiration.seconds,
                microseconds=call.expiration.nanos // 1000,
            )
            if call.expiration
            else timedelta(seconds=60)
        )

        creation_time = Timestamp()
        creation_time.FromDatetime(now)

        expiration_time = Timestamp()
        expiration_time.FromDatetime(exp)

        def make_request(call: Call) -> RunRequest:
            return RunRequest(
                function=call.function,
                input=call.input,
                creation_time=creation_time,
                expiration_time=expiration_time,
                dispatch_id=dispatch_id,
                parent_dispatch_id=parent_dispatch_id,
                root_dispatch_id=root_dispatch_id,
            )

        req = make_request(call)
        while True:
            res = await self.run(call.endpoint, req)

            if res.status != STATUS_OK:
                # TODO: emulate retries etc...
                if (
                    res.HasField("exit")
                    and res.exit.HasField("result")
                    and res.exit.result.HasField("error")
                ):
                    error = res.exit.result.error
                else:
                    error = Error(type="status", message=str(res.status))
                return CallResult(
                    dispatch_id=dispatch_id,
                    error=error,
                )

            if res.HasField("exit"):
                if res.exit.HasField("tail_call"):
                    req = make_request(res.exit.tail_call)
                    continue
                result = res.exit.result
                return CallResult(
                    dispatch_id=dispatch_id,
                    output=result.output if result.HasField("output") else None,
                    error=result.error if result.HasField("error") else None,
                )

            # TODO: enforce poll limits
            results = await asyncio.gather(
                *[
                    self.call(
                        call=subcall,
                        dispatch_id=subcall_dispatch_id,
                        parent_dispatch_id=dispatch_id,
                        root_dispatch_id=root_dispatch_id,
                    )
                    for subcall, subcall_dispatch_id in zip(
                        res.poll.calls, next(self.dispatch_ids)
                    )
                ]
            )

            req = RunRequest(
                function=req.function,
                creation_time=creation_time,
                expiration_time=expiration_time,
                dispatch_id=dispatch_id,
                parent_dispatch_id=parent_dispatch_id,
                root_dispatch_id=root_dispatch_id,
                poll_result=PollResult(
                    coroutine_state=res.poll.coroutine_state,
                    results=results,
                ),
            )

    async def run(self, endpoint: str, req: RunRequest) -> RunResponse:
        async with await self.session.post(
            f"{endpoint}/dispatch.sdk.v1.FunctionService/Run",
            data=req.SerializeToString(),
        ) as response:
            data = await response.read()
            if response.status != 200:
                raise ClientError.from_response(response.status, data)
            return RunResponse.FromString(data)

    @property
    def session(self) -> aiohttp.ClientSession:
        if not self._session:
            self._session = aiohttp.ClientSession()
        return self._session


async def main(coro: Coroutine[Any, Any, None]) -> None:
    reg = default_registry()
    api = Service()
    app = Dispatch(reg)
    try:
        async with Server(api) as backend:
            async with Server(app) as server:
                # Here we break through the abstraction layers a bit, it's not
                # ideal but it works for now.
                reg.client.api_url.value = backend.url
                reg.endpoint = server.url
                await coro
    finally:
        await api.close()
        # TODO: let's figure out how to get rid of this global registry
        # state at some point, which forces tests to be run sequentially.
        dispatch.experimental.durable.registry.clear_functions()


def run(coro: Coroutine[Any, Any, None]) -> None:
    return asyncio.run(main(coro))


# TODO: these decorators still need work, until we figure out serialization
# for cell objects, they are not very useful since the registry they receive
# as argument cannot be used to register dispatch functions.
#
# The simplest would be to use a global registry for external application tests,
# maybe we can figure out a way to make this easy with a syntax like:
#
# import main
# import dispatch.test
#
# @dispatch.test.function(main.dispatch)
# async def test_something():
#     ...
#
# (WIP)


def function(fn: Callable[[], Coroutine[Any, Any, None]]) -> Callable[[], None]:
    @wraps(fn)
    def wrapper():
        return run(fn())

    return wrapper


def method(fn: Callable[[T], Coroutine[Any, Any, None]]) -> Callable[[T], None]:
    @wraps(fn)
    def wrapper(self: T):
        return run(fn(self))

    return wrapper


def aiotest(
    fn: Callable[["TestCase"], Coroutine[Any, Any, None]]
) -> Callable[["TestCase"], None]:
    """Decorator to run tests declared as async methods of the TestCase class
    using the event loop of the test case instance.

    This decorator is internal only, it shouldn't be exposed in the public API
    of this module.
    """

    @wraps(fn)
    def test(self):
        self.server_loop.run_until_complete(fn(self))

    return test


_registry = Registry(
    name=__name__,
    endpoint=DISPATCH_ENDPOINT_URL,
    client=Client(api_key=DISPATCH_API_KEY, api_url=DISPATCH_API_URL),
)


@_registry.function
def greet() -> str:
    return "Hello World!"


@_registry.function
def greet_name(name: str) -> str:
    return f"Hello world: {name}"


@_registry.function
def echo(name: str) -> str:
    return name


@_registry.function
async def echo_nested(name: str) -> str:
    return await echo(name)


@_registry.function
def length(name: str) -> int:
    return len(name)


@_registry.function
def broken() -> str:
    raise ValueError("something went wrong!")


@_registry.function
async def broken_nested(name: str) -> str:
    return await broken()


set_default_registry(_registry)


class TestCase(unittest.TestCase):
    """TestCase implements the generic test suite used in dispatch-py to test
    various integrations of the SDK with frameworks like FastAPI, Flask, etc...

    Applications typically don't use this class directly, the test suite is
    mostly useful as an internal testing tool.

    Implementation of the test suite need to override the dispatch_test_init,
    dispatch_test_run, and dispatch_test_stop methods to integrate with the
    testing infrastructure (see the documentation of each of these methods for
    more details).
    """

    def dispatch_test_init(self, reg: Registry) -> str:
        raise NotImplementedError

    def dispatch_test_run(self):
        raise NotImplementedError

    def dispatch_test_stop(self):
        raise NotImplementedError

    def setUp(self):
        self.service = Service()

        self.server = Server(self.service)
        self.server_loop = asyncio.new_event_loop()
        self.server_loop.run_until_complete(self.server.start())

        _registry.client.api_key.value = DISPATCH_API_KEY
        _registry.client.api_url.value = self.server.url
        _registry.endpoint = self.dispatch_test_init(_registry)
        self.client_thread = threading.Thread(target=self.dispatch_test_run)
        self.client_thread.start()

    def tearDown(self):
        self.dispatch_test_stop()
        self.client_thread.join()

        self.server_loop.run_until_complete(self.service.close())
        self.server_loop.run_until_complete(self.server_loop.shutdown_asyncgens())
        self.server_loop.close()

        # TODO: let's figure out how to get rid of this global registry
        # state at some point, which forces tests to be run sequentially.
        #
        # We can't erase the registry because user tests might have registered
        # functions in the global scope that would be lost after the first test
        # we run.
        #
        # dispatch.experimental.durable.registry.clear_functions()

    @property
    def function_service_run_url(self) -> str:
        return f"{_registry.endpoint}/dispatch.sdk.v1.FunctionService/Run"

    @aiotest
    async def test_content_length_missing(self):
        async with aiohttp.ClientSession(
            request_class=ClientRequestContentLengthMissing
        ) as session:
            async with await session.post(self.function_service_run_url) as resp:
                data = await resp.read()
                self.assertEqual(resp.status, 400)
                self.assertEqual(
                    json.loads(data),
                    make_error_invalid_argument("content length is required"),
                )

    @aiotest
    async def test_content_length_too_large(self):
        async with aiohttp.ClientSession(
            request_class=ClientRequestContentLengthTooLarge
        ) as session:
            async with await session.post(self.function_service_run_url) as resp:
                data = await resp.read()
                self.assertEqual(resp.status, 400)
                self.assertEqual(
                    json.loads(data),
                    make_error_invalid_argument("content length is too large"),
                )

    @aiotest
    async def test_call_function_missing(self):
        async with aiohttp.ClientSession() as session:
            async with await session.post(
                self.function_service_run_url,
                data=RunRequest(function="does-not-exist").SerializeToString(),
            ) as resp:
                data = await resp.read()
                self.assertEqual(resp.status, 404)
                self.assertEqual(
                    json.loads(data),
                    make_error_not_found("function 'does-not-exist' does not exist"),
                )

    @aiotest
    async def test_call_function_no_input(self):
        ret = await greet()
        self.assertEqual(ret, "Hello World!")

    @aiotest
    async def test_call_function_with_input(self):
        ret = await greet_name("52")
        self.assertEqual(ret, "Hello world: 52")

    @aiotest
    async def test_call_function_raise_error(self):
        with self.assertRaises(ValueError) as e:
            await broken()

    @aiotest
    async def test_call_two_functions(self):
        self.assertEqual(await echo("hello"), "hello")
        self.assertEqual(await length("hello"), 5)

    @aiotest
    async def test_call_nested_function_with_result(self):
        self.assertEqual(await echo_nested("hello"), "hello")

    @aiotest
    async def test_call_nested_function_with_error(self):
        with self.assertRaises(ValueError) as e:
            await broken_nested("hello")


class ClientRequestContentLengthMissing(aiohttp.ClientRequest):
    def update_headers(self, skip_auto_headers):
        super().update_headers(skip_auto_headers)
        if "Content-Length" in self.headers:
            del self.headers["Content-Length"]


class ClientRequestContentLengthTooLarge(aiohttp.ClientRequest):
    def update_headers(self, skip_auto_headers):
        super().update_headers(skip_auto_headers)
        self.headers["Content-Length"] = "16000001"


def make_error_invalid_argument(message: str) -> dict:
    return make_error("invalid_argument", message)


def make_error_not_found(message: str) -> dict:
    return make_error("not_found", message)


def make_error(code: str, message: str) -> dict:
    return {"code": code, "message": message}
