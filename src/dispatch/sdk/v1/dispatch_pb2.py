# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: dispatch/sdk/v1/dispatch.proto
# Protobuf Python Version: 4.25.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from buf.validate import validate_pb2 as buf_dot_validate_dot_validate__pb2
from dispatch.sdk.v1 import call_pb2 as dispatch_dot_sdk_dot_v1_dot_call__pb2

DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b"\n\x1e\x64ispatch/sdk/v1/dispatch.proto\x12\x0f\x64ispatch.sdk.v1\x1a\x1b\x62uf/validate/validate.proto\x1a\x1a\x64ispatch/sdk/v1/call.proto\"\xf3\x02\n\x0f\x44ispatchRequest\x12+\n\x05\x63\x61lls\x18\x01 \x03(\x0b\x32\x15.dispatch.sdk.v1.CallR\x05\x63\x61lls:\xb2\x02\xbaH\xae\x02\x1as\n(dispatch.request.calls.endpoint.nonempty\x12\x1d\x43\x61ll endpoint cannot be empty\x1a(this.calls.all(call, has(call.endpoint))\x1a\xb6\x01\n&dispatch.request.calls.endpoint.scheme\x12)Call endpoint must be a http or https URL\x1a\x61this.calls.all(call, call.endpoint.startsWith('http://') || call.endpoint.startsWith('https://'))\"5\n\x10\x44ispatchResponse\x12!\n\x0c\x64ispatch_ids\x18\x01 \x03(\tR\x0b\x64ispatchIds2d\n\x0f\x44ispatchService\x12Q\n\x08\x44ispatch\x12 .dispatch.sdk.v1.DispatchRequest\x1a!.dispatch.sdk.v1.DispatchResponse\"\x00\x42\x82\x01\n\x13\x63om.dispatch.sdk.v1B\rDispatchProtoP\x01\xa2\x02\x03\x44SX\xaa\x02\x0f\x44ispatch.Sdk.V1\xca\x02\x0f\x44ispatch\\Sdk\\V1\xe2\x02\x1b\x44ispatch\\Sdk\\V1\\GPBMetadata\xea\x02\x11\x44ispatch::Sdk::V1b\x06proto3"
)

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(
    DESCRIPTOR, "dispatch.sdk.v1.dispatch_pb2", _globals
)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals["DESCRIPTOR"]._options = None
    _globals["DESCRIPTOR"]._serialized_options = (
        b"\n\023com.dispatch.sdk.v1B\rDispatchProtoP\001\242\002\003DSX\252\002\017Dispatch.Sdk.V1\312\002\017Dispatch\\Sdk\\V1\342\002\033Dispatch\\Sdk\\V1\\GPBMetadata\352\002\021Dispatch::Sdk::V1"
    )
    _globals["_DISPATCHREQUEST"]._options = None
    _globals["_DISPATCHREQUEST"]._serialized_options = (
        b"\272H\256\002\032s\n(dispatch.request.calls.endpoint.nonempty\022\035Call endpoint cannot be empty\032(this.calls.all(call, has(call.endpoint))\032\266\001\n&dispatch.request.calls.endpoint.scheme\022)Call endpoint must be a http or https URL\032athis.calls.all(call, call.endpoint.startsWith('http://') || call.endpoint.startsWith('https://'))"
    )
    _globals["_DISPATCHREQUEST"]._serialized_start = 109
    _globals["_DISPATCHREQUEST"]._serialized_end = 480
    _globals["_DISPATCHRESPONSE"]._serialized_start = 482
    _globals["_DISPATCHRESPONSE"]._serialized_end = 535
    _globals["_DISPATCHSERVICE"]._serialized_start = 537
    _globals["_DISPATCHSERVICE"]._serialized_end = 637
# @@protoc_insertion_point(module_scope)
