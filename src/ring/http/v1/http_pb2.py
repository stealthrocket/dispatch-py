# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: ring/http/v1/http.proto
# Protobuf Python Version: 4.25.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x17ring/http/v1/http.proto\x12\x0cring.http.v1"u\n\x07Request\x12\x16\n\x06method\x18\x01 \x01(\tR\x06method\x12\x10\n\x03url\x18\x02 \x01(\tR\x03url\x12,\n\x06header\x18\x04 \x03(\x0b\x32\x14.ring.http.v1.HeaderR\x06header\x12\x12\n\x04\x62ody\x18\x03 \x01(\x0cR\x04\x62ody"m\n\x08Response\x12\x1f\n\x0bstatus_code\x18\x01 \x01(\x05R\nstatusCode\x12,\n\x06header\x18\x02 \x03(\x0b\x32\x14.ring.http.v1.HeaderR\x06header\x12\x12\n\x04\x62ody\x18\x03 \x01(\x0cR\x04\x62ody"2\n\x06Header\x12\x12\n\x04name\x18\x01 \x01(\tR\x04name\x12\x14\n\x05value\x18\x02 \x01(\tR\x05valueBo\n\x10\x63om.ring.http.v1B\tHttpProtoP\x01\xa2\x02\x03RHX\xaa\x02\x0cRing.Http.V1\xca\x02\x0cRing\\Http\\V1\xe2\x02\x18Ring\\Http\\V1\\GPBMetadata\xea\x02\x0eRing::Http::V1b\x06proto3'
)

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, "ring.http.v1.http_pb2", _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    _globals["DESCRIPTOR"]._options = None
    _globals["DESCRIPTOR"]._serialized_options = (
        b"\n\020com.ring.http.v1B\tHttpProtoP\001\242\002\003RHX\252\002\014Ring.Http.V1\312\002\014Ring\\Http\\V1\342\002\030Ring\\Http\\V1\\GPBMetadata\352\002\016Ring::Http::V1"
    )
    _globals["_REQUEST"]._serialized_start = 41
    _globals["_REQUEST"]._serialized_end = 158
    _globals["_RESPONSE"]._serialized_start = 160
    _globals["_RESPONSE"]._serialized_end = 269
    _globals["_HEADER"]._serialized_start = 271
    _globals["_HEADER"]._serialized_end = 321
# @@protoc_insertion_point(module_scope)
