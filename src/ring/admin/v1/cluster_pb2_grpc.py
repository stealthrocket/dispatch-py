# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from ring.admin.v1 import cluster_pb2 as ring_dot_admin_dot_v1_dot_cluster__pb2


class ClusterServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.DescribeInstances = channel.unary_unary(
            "/ring.admin.v1.ClusterService/DescribeInstances",
            request_serializer=ring_dot_admin_dot_v1_dot_cluster__pb2.DescribeInstancesRequest.SerializeToString,
            response_deserializer=ring_dot_admin_dot_v1_dot_cluster__pb2.DescribeInstancesResponse.FromString,
        )
        self.DescribePartitions = channel.unary_unary(
            "/ring.admin.v1.ClusterService/DescribePartitions",
            request_serializer=ring_dot_admin_dot_v1_dot_cluster__pb2.DescribePartitionsRequest.SerializeToString,
            response_deserializer=ring_dot_admin_dot_v1_dot_cluster__pb2.DescribePartitionsResponse.FromString,
        )
        self.DescribeZones = channel.unary_unary(
            "/ring.admin.v1.ClusterService/DescribeZones",
            request_serializer=ring_dot_admin_dot_v1_dot_cluster__pb2.DescribeZonesRequest.SerializeToString,
            response_deserializer=ring_dot_admin_dot_v1_dot_cluster__pb2.DescribeZonesResponse.FromString,
        )
        self.ListInstances = channel.unary_unary(
            "/ring.admin.v1.ClusterService/ListInstances",
            request_serializer=ring_dot_admin_dot_v1_dot_cluster__pb2.ListInstancesRequest.SerializeToString,
            response_deserializer=ring_dot_admin_dot_v1_dot_cluster__pb2.ListInstancesResponse.FromString,
        )
        self.ListPartitions = channel.unary_unary(
            "/ring.admin.v1.ClusterService/ListPartitions",
            request_serializer=ring_dot_admin_dot_v1_dot_cluster__pb2.ListPartitionsRequest.SerializeToString,
            response_deserializer=ring_dot_admin_dot_v1_dot_cluster__pb2.ListPartitionsResponse.FromString,
        )
        self.ListZones = channel.unary_unary(
            "/ring.admin.v1.ClusterService/ListZones",
            request_serializer=ring_dot_admin_dot_v1_dot_cluster__pb2.ListZonesRequest.SerializeToString,
            response_deserializer=ring_dot_admin_dot_v1_dot_cluster__pb2.ListZonesResponse.FromString,
        )


class ClusterServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def DescribeInstances(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def DescribePartitions(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def DescribeZones(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def ListInstances(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def ListPartitions(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def ListZones(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_ClusterServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "DescribeInstances": grpc.unary_unary_rpc_method_handler(
            servicer.DescribeInstances,
            request_deserializer=ring_dot_admin_dot_v1_dot_cluster__pb2.DescribeInstancesRequest.FromString,
            response_serializer=ring_dot_admin_dot_v1_dot_cluster__pb2.DescribeInstancesResponse.SerializeToString,
        ),
        "DescribePartitions": grpc.unary_unary_rpc_method_handler(
            servicer.DescribePartitions,
            request_deserializer=ring_dot_admin_dot_v1_dot_cluster__pb2.DescribePartitionsRequest.FromString,
            response_serializer=ring_dot_admin_dot_v1_dot_cluster__pb2.DescribePartitionsResponse.SerializeToString,
        ),
        "DescribeZones": grpc.unary_unary_rpc_method_handler(
            servicer.DescribeZones,
            request_deserializer=ring_dot_admin_dot_v1_dot_cluster__pb2.DescribeZonesRequest.FromString,
            response_serializer=ring_dot_admin_dot_v1_dot_cluster__pb2.DescribeZonesResponse.SerializeToString,
        ),
        "ListInstances": grpc.unary_unary_rpc_method_handler(
            servicer.ListInstances,
            request_deserializer=ring_dot_admin_dot_v1_dot_cluster__pb2.ListInstancesRequest.FromString,
            response_serializer=ring_dot_admin_dot_v1_dot_cluster__pb2.ListInstancesResponse.SerializeToString,
        ),
        "ListPartitions": grpc.unary_unary_rpc_method_handler(
            servicer.ListPartitions,
            request_deserializer=ring_dot_admin_dot_v1_dot_cluster__pb2.ListPartitionsRequest.FromString,
            response_serializer=ring_dot_admin_dot_v1_dot_cluster__pb2.ListPartitionsResponse.SerializeToString,
        ),
        "ListZones": grpc.unary_unary_rpc_method_handler(
            servicer.ListZones,
            request_deserializer=ring_dot_admin_dot_v1_dot_cluster__pb2.ListZonesRequest.FromString,
            response_serializer=ring_dot_admin_dot_v1_dot_cluster__pb2.ListZonesResponse.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "ring.admin.v1.ClusterService", rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))


# This class is part of an EXPERIMENTAL API.
class ClusterService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def DescribeInstances(
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
            "/ring.admin.v1.ClusterService/DescribeInstances",
            ring_dot_admin_dot_v1_dot_cluster__pb2.DescribeInstancesRequest.SerializeToString,
            ring_dot_admin_dot_v1_dot_cluster__pb2.DescribeInstancesResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def DescribePartitions(
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
            "/ring.admin.v1.ClusterService/DescribePartitions",
            ring_dot_admin_dot_v1_dot_cluster__pb2.DescribePartitionsRequest.SerializeToString,
            ring_dot_admin_dot_v1_dot_cluster__pb2.DescribePartitionsResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def DescribeZones(
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
            "/ring.admin.v1.ClusterService/DescribeZones",
            ring_dot_admin_dot_v1_dot_cluster__pb2.DescribeZonesRequest.SerializeToString,
            ring_dot_admin_dot_v1_dot_cluster__pb2.DescribeZonesResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def ListInstances(
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
            "/ring.admin.v1.ClusterService/ListInstances",
            ring_dot_admin_dot_v1_dot_cluster__pb2.ListInstancesRequest.SerializeToString,
            ring_dot_admin_dot_v1_dot_cluster__pb2.ListInstancesResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def ListPartitions(
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
            "/ring.admin.v1.ClusterService/ListPartitions",
            ring_dot_admin_dot_v1_dot_cluster__pb2.ListPartitionsRequest.SerializeToString,
            ring_dot_admin_dot_v1_dot_cluster__pb2.ListPartitionsResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def ListZones(
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
            "/ring.admin.v1.ClusterService/ListZones",
            ring_dot_admin_dot_v1_dot_cluster__pb2.ListZonesRequest.SerializeToString,
            ring_dot_admin_dot_v1_dot_cluster__pb2.ListZonesResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )