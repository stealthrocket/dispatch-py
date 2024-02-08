import pickle
import unittest
from typing import Any

import fastapi
import google.protobuf.any_pb2
import google.protobuf.wrappers_pb2
import httpx
from fastapi.testclient import TestClient

import dispatch.fastapi
import dispatch.function
from dispatch.function import Error, Input, Output, Status
from dispatch.sdk.v1 import call_pb2 as call_pb
from dispatch.sdk.v1 import function_pb2 as function_pb

from . import function_service


class TestFastAPI(unittest.TestCase):
    def test_configure(self):
        app = fastapi.FastAPI()

        dispatch.fastapi.configure(app, endpoint="https://127.0.0.1:9999")

        @app.get("/")
        def read_root():
            return {"Hello": "World"}

        client = TestClient(app)

        # Ensure existing routes are still working.
        resp = client.get("/")
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(resp.json(), {"Hello": "World"})

        # Ensure Dispatch root is available.
        resp = client.post("/dispatch.sdk.v1.FunctionService/Run")
        self.assertEqual(resp.status_code, 400)

    def test_configure_no_app(self):
        with self.assertRaises(ValueError):
            dispatch.fastapi.configure(None, endpoint="http://127.0.0.1:9999")

    def test_configure_no_public_url(self):
        app = fastapi.FastAPI()
        with self.assertRaises(ValueError):
            dispatch.fastapi.configure(app, endpoint="")

    def test_configure_public_url_no_scheme(self):
        app = fastapi.FastAPI()
        with self.assertRaises(ValueError):
            dispatch.fastapi.configure(app, endpoint="127.0.0.1:9999")

    def test_fastapi_simple_request(self):
        app = fastapi.FastAPI()
        dispatch.fastapi.configure(app, endpoint="http://127.0.0.1:9999/")

        @app.dispatch_function()
        def my_function(input: Input) -> Output:
            return Output.value(
                f"You told me: '{input.input}' ({len(input.input)} characters)"
            )

        http_client = TestClient(app)

        client = function_service.client(http_client)

        pickled = pickle.dumps("Hello World!")
        input_any = google.protobuf.any_pb2.Any()
        input_any.Pack(google.protobuf.wrappers_pb2.BytesValue(value=pickled))

        req = function_pb.RunRequest(
            function=my_function.name,
            input=input_any,
        )

        resp = client.Run(req)

        self.assertIsInstance(resp, function_pb.RunResponse)

        resp.exit.result.output.Unpack(
            output_bytes := google.protobuf.wrappers_pb2.BytesValue()
        )
        output = pickle.loads(output_bytes.value)

        self.assertEqual(output, "You told me: 'Hello World!' (12 characters)")


def response_output(resp: function_pb.RunResponse) -> Any:
    return dispatch.function._any_unpickle(resp.exit.result.output)


class TestCoroutine(unittest.TestCase):
    def setUp(self):
        self.app = fastapi.FastAPI()
        dispatch.fastapi.configure(self.app, endpoint="https://127.0.0.1:9999")
        http_client = TestClient(self.app)
        self.client = function_service.client(http_client)

    def execute(
        self, func, input=None, state=None, calls=None
    ) -> function_pb.RunResponse:
        """Test helper to invoke coroutines on the local server."""
        req = function_pb.RunRequest(function=func.name)

        if input is not None:
            input_bytes = pickle.dumps(input)
            input_any = google.protobuf.any_pb2.Any()
            input_any.Pack(google.protobuf.wrappers_pb2.BytesValue(value=input_bytes))
            req.input.CopyFrom(input_any)
        if state is not None:
            req.poll_result.coroutine_state = state
        if calls is not None:
            for c in calls:
                req.poll_result.results.append(c)

        resp = self.client.Run(req)
        self.assertIsInstance(resp, function_pb.RunResponse)
        return resp

    def call(self, call: call_pb.Call) -> call_pb.CallResult:
        req = function_pb.RunRequest(
            function=call.function,
            input=call.input,
        )
        resp = self.client.Run(req)
        self.assertIsInstance(resp, function_pb.RunResponse)

        # Assert the response is terminal. Good enough until the test client can
        # orchestrate coroutines.
        self.assertTrue(len(resp.poll.coroutine_state) == 0)

        resp.exit.result.correlation_id = call.correlation_id
        return resp.exit.result

    def test_no_input(self):
        @self.app.dispatch_function()
        def my_function(input: Input) -> Output:
            return Output.value("Hello World!")

        resp = self.execute(my_function)

        out = response_output(resp)
        self.assertEqual(out, "Hello World!")

    def test_missing_coroutine(self):
        req = function_pb.RunRequest(
            function="does-not-exist",
        )

        with self.assertRaises(httpx.HTTPStatusError) as cm:
            self.client.Run(req)
        self.assertEqual(cm.exception.response.status_code, 404)

    def test_string_input(self):
        @self.app.dispatch_function()
        def my_function(input: Input) -> Output:
            return Output.value(f"You sent '{input.input}'")

        resp = self.execute(my_function, input="cool stuff")
        out = response_output(resp)
        self.assertEqual(out, "You sent 'cool stuff'")

    def test_error_on_access_state_in_first_call(self):
        @self.app.dispatch_function()
        def my_function(input: Input) -> Output:
            print(input.coroutine_state)
            return Output.value("not reached")

        resp = self.execute(my_function, input="cool stuff")
        self.assertEqual("ValueError", resp.exit.result.error.type)
        self.assertEqual(
            "This input is for a first function call", resp.exit.result.error.message
        )

    def test_error_on_access_input_in_second_call(self):
        @self.app.dispatch_function()
        def my_function(input: Input) -> Output:
            if input.is_first_call:
                return Output.poll(state=42)
            print(input.input)
            return Output.value("not reached")

        resp = self.execute(my_function, input="cool stuff")
        resp = self.execute(my_function, state=resp.poll.coroutine_state)

        self.assertEqual("ValueError", resp.exit.result.error.type)
        self.assertEqual(
            "This input is for a resumed coroutine", resp.exit.result.error.message
        )

    def test_duplicate_coro(self):
        @self.app.dispatch_function()
        def my_function(input: Input) -> Output:
            return Output.value("Do one thing")

        with self.assertRaises(ValueError):

            @self.app.dispatch_function()
            def my_function(input: Input) -> Output:
                return Output.value("Do something else")

    def test_two_simple_coroutines(self):
        @self.app.dispatch_function()
        def echoroutine(input: Input) -> Output:
            return Output.value(f"Echo: '{input.input}'")

        @self.app.dispatch_function()
        def len_coroutine(input: Input) -> Output:
            return Output.value(f"Length: {len(input.input)}")

        data = "cool stuff"
        resp = self.execute(echoroutine, input=data)
        out = response_output(resp)
        self.assertEqual(out, "Echo: 'cool stuff'")

        resp = self.execute(len_coroutine, input=data)
        out = response_output(resp)
        self.assertEqual(out, "Length: 10")

    def test_coroutine_with_state(self):
        @self.app.dispatch_function()
        def coroutine3(input: Input) -> Output:
            if input.is_first_call:
                counter = input.input
            else:
                counter = input.coroutine_state
            counter -= 1
            if counter <= 0:
                return Output.value("done")
            return Output.poll(state=counter)

        # first call
        resp = self.execute(coroutine3, input=4)
        state = resp.poll.coroutine_state
        self.assertTrue(len(state) > 0)

        # resume, state = 3
        resp = self.execute(coroutine3, state=state)
        state = resp.poll.coroutine_state
        self.assertTrue(len(state) > 0)

        # resume, state = 2
        resp = self.execute(coroutine3, state=state)
        state = resp.poll.coroutine_state
        self.assertTrue(len(state) > 0)

        # resume, state = 1
        resp = self.execute(coroutine3, state=state)
        state = resp.poll.coroutine_state
        self.assertTrue(len(state) == 0)
        out = response_output(resp)
        self.assertEqual(out, "done")

    def test_coroutine_poll(self):
        @self.app.dispatch_function()
        def coro_compute_len(input: Input) -> Output:
            return Output.value(len(input.input))

        @self.app.dispatch_function()
        def coroutine_main(input: Input) -> Output:
            if input.is_first_call:
                text: str = input.input
                return Output.poll(state=text, calls=[coro_compute_len.call_with(text)])
            text = input.coroutine_state
            length = input.call_results[0].output
            return Output.value(f"length={length} text='{text}'")

        resp = self.execute(coroutine_main, input="cool stuff")

        # main saved some state
        state = resp.poll.coroutine_state
        self.assertTrue(len(state) > 0)
        # main asks for 1 call to compute_len
        self.assertEqual(len(resp.poll.calls), 1)
        call = resp.poll.calls[0]
        self.assertEqual(call.function, coro_compute_len.name)
        self.assertEqual(dispatch.function._any_unpickle(call.input), "cool stuff")

        # make the requested compute_len
        resp2 = self.call(call)
        # check the result is the terminal expected response
        len_resp = dispatch.function._any_unpickle(resp2.output)
        self.assertEqual(10, len_resp)

        # resume main with the result
        resp = self.execute(coroutine_main, state=state, calls=[resp2])
        # validate the final result
        self.assertTrue(len(resp.poll.coroutine_state) == 0)
        out = response_output(resp)
        self.assertEqual("length=10 text='cool stuff'", out)

    def test_coroutine_poll_error(self):
        @self.app.dispatch_function()
        def coro_compute_len(input: Input) -> Output:
            return Output.error(Error(Status.PERMANENT_ERROR, "type", "Dead"))

        @self.app.dispatch_function()
        def coroutine_main(input: Input) -> Output:
            if input.is_first_call:
                text: str = input.input
                return Output.poll(state=text, calls=[coro_compute_len.call_with(text)])
            msg = input.call_results[0].error.message
            type = input.call_results[0].error.type
            return Output.value(f"msg={msg} type='{type}'")

        resp = self.execute(coroutine_main, input="cool stuff")

        # main saved some state
        state = resp.poll.coroutine_state
        self.assertTrue(len(state) > 0)
        # main asks for 1 call to compute_len
        self.assertEqual(len(resp.poll.calls), 1)
        call = resp.poll.calls[0]
        self.assertEqual(call.function, coro_compute_len.name)
        self.assertEqual(dispatch.function._any_unpickle(call.input), "cool stuff")

        # make the requested compute_len
        resp2 = self.call(call)

        # resume main with the result
        resp = self.execute(coroutine_main, state=state, calls=[resp2])
        # validate the final result
        self.assertTrue(len(resp.poll.coroutine_state) == 0)
        out = response_output(resp)
        self.assertEqual(out, "msg=Dead type='type'")

    def test_coroutine_error(self):
        @self.app.dispatch_function()
        def mycoro(input: Input) -> Output:
            return Output.error(Error(Status.PERMANENT_ERROR, "sometype", "dead"))

        resp = self.execute(mycoro)
        self.assertEqual("sometype", resp.exit.result.error.type)
        self.assertEqual("dead", resp.exit.result.error.message)

    def test_coroutine_expected_exception(self):
        @self.app.dispatch_function()
        def mycoro(input: Input) -> Output:
            try:
                1 / 0
            except ZeroDivisionError as e:
                return Output.error(Error.from_exception(e))
            self.fail("should not reach here")

        resp = self.execute(mycoro)
        self.assertEqual("ZeroDivisionError", resp.exit.result.error.type)
        self.assertEqual("division by zero", resp.exit.result.error.message)
        self.assertEqual(Status.TEMPORARY_ERROR, resp.status)

    def test_coroutine_unexpected_exception(self):
        @self.app.dispatch_function()
        def mycoro(input: Input) -> Output:
            1 / 0
            self.fail("should not reach here")

        resp = self.execute(mycoro)
        self.assertEqual("ZeroDivisionError", resp.exit.result.error.type)
        self.assertEqual("division by zero", resp.exit.result.error.message)
        self.assertEqual(Status.TEMPORARY_ERROR, resp.status)

    def test_specific_status(self):
        @self.app.dispatch_function()
        def mycoro(input: Input) -> Output:
            return Output.error(Error(Status.THROTTLED, "foo", "bar"))

        resp = self.execute(mycoro)
        self.assertEqual("foo", resp.exit.result.error.type)
        self.assertEqual("bar", resp.exit.result.error.message)
        self.assertEqual(Status.THROTTLED, resp.status)

    def test_tailcall(self):
        @self.app.dispatch_function()
        def other_coroutine(input: Input) -> Output:
            return Output.value(f"Hello {input.input}")

        @self.app.dispatch_function()
        def mycoro(input: Input) -> Output:
            return Output.tail_call(other_coroutine.call_with(42))

        resp = self.execute(mycoro)
        self.assertEqual(other_coroutine.name, resp.exit.tail_call.function)
        self.assertEqual(42, dispatch.function._any_unpickle(resp.exit.tail_call.input))


class TestError(unittest.TestCase):
    def test_missing_type_and_message(self):
        with self.assertRaises(ValueError):
            Error(Status.TEMPORARY_ERROR, type=None, message=None)

    def test_error_with_ok_status(self):
        with self.assertRaises(ValueError):
            Error(Status.OK, type="type", message="yep")

    def test_from_exception_timeout(self):
        err = Error.from_exception(TimeoutError())
        self.assertEqual(Status.TIMEOUT, err.status)

    def test_from_exception_syntax_error(self):
        err = Error.from_exception(SyntaxError())
        self.assertEqual(Status.PERMANENT_ERROR, err.status)
