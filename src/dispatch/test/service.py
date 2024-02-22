import os
from collections import OrderedDict

import grpc

import dispatch.sdk.v1.call_pb2 as call_pb
import dispatch.sdk.v1.dispatch_pb2 as dispatch_pb
import dispatch.sdk.v1.dispatch_pb2_grpc as dispatch_grpc
import dispatch.sdk.v1.function_pb2 as function_pb
from dispatch.id import DispatchID
from dispatch.proto import Status
from dispatch.test import EndpointClient

_default_retry_on_status = {
    Status.THROTTLED,
    Status.TIMEOUT,
    Status.TEMPORARY_ERROR,
    Status.DNS_ERROR,
    Status.TCP_ERROR,
    Status.TLS_ERROR,
    Status.HTTP_ERROR,
}


class DispatchService(dispatch_grpc.DispatchServiceServicer):
    """Test instance of Dispatch that provides the bare minimum
    functionality required to test functions locally."""

    def __init__(
        self,
        endpoint_client: EndpointClient,
        api_key: str | None = None,
        retry_on_status: set[Status] | None = None,
        collect_responses: bool = False,
    ):
        """Initialize the Dispatch service.

        Args:
            endpoint_client: Client to use to interact with the local Dispatch
                endpoint (that provides the functions).
            api_key: Expected API key on requests to the service. If omitted, the
                value of the DISPATCH_API_KEY environment variable is used instead.
            retry_on_status: Set of status codes to enable retries for.
            collect_responses: Enable collection of responses.
        """
        super().__init__()

        self.endpoint_client = endpoint_client

        if api_key is None:
            api_key = os.getenv("DISPATCH_API_KEY")
        self.api_key = api_key

        if retry_on_status is None:
            retry_on_status = _default_retry_on_status
        self.retry_on_status = retry_on_status

        self._next_dispatch_id = 1

        self.queue: list[tuple[DispatchID, call_pb.Call]] = []

        self.responses: OrderedDict[DispatchID, function_pb.RunResponse] = OrderedDict()
        self.collect_responses = collect_responses

    def Dispatch(self, request: dispatch_pb.DispatchRequest, context):
        """RPC handler for Dispatch requests. Requests are only queued for
        processing here."""
        self._validate_authentication(context)

        resp = dispatch_pb.DispatchResponse()

        for call in request.calls:
            dispatch_id = self._make_dispatch_id()
            resp.dispatch_ids.append(dispatch_id)
            self.queue.append((dispatch_id, call))

        return resp

    def _validate_authentication(self, context: grpc.ServicerContext):
        expected = f"Bearer {self.api_key}"
        for key, value in context.invocation_metadata():
            if key == "authorization":
                if value == expected:
                    return
                context.abort(
                    grpc.StatusCode.UNAUTHENTICATED,
                    f"Invalid authorization header. Expected '{expected}', got {value!r}",
                )
        context.abort(grpc.StatusCode.UNAUTHENTICATED, "Missing authorization header")

    def _make_dispatch_id(self) -> DispatchID:
        dispatch_id = self._next_dispatch_id
        self._next_dispatch_id += 1
        return "{:032x}".format(dispatch_id)

    def dispatch_calls(self):
        """Synchronously dispatch pending function calls to the
        configured endpoint."""
        _next_queue = []
        while self.queue:
            dispatch_id, call = self.queue.pop(0)

            resp = self.endpoint_client.run(
                function_pb.RunRequest(
                    function=call.function,
                    input=call.input,
                )
            )

            if self.collect_responses:
                self.responses[dispatch_id] = resp

            if Status(resp.status) in self.retry_on_status:
                dispatch_id = self._make_dispatch_id()
                _next_queue.append((dispatch_id, call))

        self.queue = _next_queue
