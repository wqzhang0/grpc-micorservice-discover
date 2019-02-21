# Copyright 2017 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Interceptor that ensures a specific header is present."""
import base64

import grpc

from grpc_microservice.common.server.key_pool import SERVER_UUIDS


def _unary_unary_rpc_terminator(code, details):
    def terminate(ignored_request, context):
        context.abort(code, details)

    return grpc.unary_unary_rpc_method_handler(terminate)


class RequestHeaderValidatorInterceptor(grpc.ServerInterceptor):

    def __init__(self, header, code, details):
        self._header = header
        self._terminator = _unary_unary_rpc_terminator(code, details)

    def paser_uuid(self, value):
        # server_access
        _j = str(base64.b64decode(value), encoding='utf-8')
        return _j[:2], _j[2:]

    def intercept_service(self, continuation, handler_call_details):
        _tuple = handler_call_details.invocation_metadata
        _permisseion_check_result = False
        for i in range(len(_tuple)):
            _server_key = _tuple[i].key
            if _server_key == 'server-access':
                _server_access_value = _tuple[i].value
                _version, _uuid = self.paser_uuid(_server_access_value)
                if _version == 'xx':
                    _permisseion_check_result = True
                    break
                if SERVER_UUIDS.get(handler_call_details[0], None) == _uuid and _version == '01':
                    _permisseion_check_result = True
                    break

        if _permisseion_check_result:
            return continuation(handler_call_details)
        else:
            return self._terminator
