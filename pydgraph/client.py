#
# Copyright 2016 DGraph Labs, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This module contains the main user-facing methods for interacting with the
Dgraph server over gRPC.
"""
import grpc
from pydgraph import txn
from pydgraph import util
from pydgraph.meta import VERSION
from pydgraph.proto import api_pb2 as api
from pydgraph.proto import api_pb2_grpc as api_grpc

__author__ = 'Mohit Ranka <mohitranka@gmail.com>'
__maintainer__ = 'Mohit Ranka <mohitranka@gmail.com>'
__version__ = VERSION
__status__ = 'development'


class DgraphClient(object):
    def __init__(self, host, port):
        self.channel = grpc.insecure_channel("{host}:{port}".format(host=host, port=port))
        self.stub = api_grpc.DgraphStub(self.channel)
        self.start_ts = 0
        self.lin_read = api.LinRead()

    def merge_context(self, context):
        """Merges txn_context into client's state."""
        self.start_ts = context.start_ts
        util.merge_lin_reads(self.lin_read, context.lin_read)

    def Query(self, q, timeout=None):
        request = api.Request(query=q, start_ts=self.start_ts, lin_read=self.lin_read)
        response = self.stub.Query(request, timeout)
        self.merge_context(response.txn)
        return response

    async def aQuery(self, q, timeout=None):
        request = api.Request(query=q, start_ts=self.start_ts, lin_read=self.lin_read)
        response = await self.stub.Query.future(request, timeout)
        self.merge_context(response.txn)
        return response

    def Alter(self, schema, timeout=None):
        """Alter schema at the other end of the connection."""
        operation = api.Operation(schema=schema)
        return self.stub.Alter(operation, timeout)

    async def aAlter(self, schema, timeout=None):
        operation = api.Operation(schema=schema)
        return await self.stub.Alter.future(operation, timeout)

    def DropAttr(self, drop_attr, timeout=None):
        """Drop an attribute from the dgraph server."""
        operation = api.Operation(drop_attr=drop_attr)
        return self.stub.Alter(operation)

    def DropAll(self, timeout=None):
        """Drop all schema from the dgraph server."""
        operation = api.Operation(drop_all=True)
        return self.stub.Alter(operation)

    def txn(self):
        return txn.DgraphTxn(self)
