# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from dispatch.sdk.v1 import function_pb2 as dispatch_dot_sdk_dot_v1_dot_function__pb2


class FunctionServiceStub(object):
    """The FunctionService service is used to interface with programmable endpoints
    exposing remote functions.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Run = channel.unary_unary(
            "/dispatch.sdk.v1.FunctionService/Run",
            request_serializer=dispatch_dot_sdk_dot_v1_dot_function__pb2.RunRequest.SerializeToString,
            response_deserializer=dispatch_dot_sdk_dot_v1_dot_function__pb2.RunResponse.FromString,
        )


class FunctionServiceServicer(object):
    """The FunctionService service is used to interface with programmable endpoints
    exposing remote functions.
    """

    def Run(self, request, context):
        """Run runs the function identified by the request, and returns a response
        that either contains a result when the function completed, or a poll
        directive and the associated coroutine state if the function was suspended.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_FunctionServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "Run": grpc.unary_unary_rpc_method_handler(
            servicer.Run,
            request_deserializer=dispatch_dot_sdk_dot_v1_dot_function__pb2.RunRequest.FromString,
            response_serializer=dispatch_dot_sdk_dot_v1_dot_function__pb2.RunResponse.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "dispatch.sdk.v1.FunctionService", rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))


# This class is part of an EXPERIMENTAL API.
class FunctionService(object):
    """The FunctionService service is used to interface with programmable endpoints
    exposing remote functions.
    """

    @staticmethod
    def Run(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/dispatch.sdk.v1.FunctionService/Run",
            dispatch_dot_sdk_dot_v1_dot_function__pb2.RunRequest.SerializeToString,
            dispatch_dot_sdk_dot_v1_dot_function__pb2.RunResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )
