import time
from concurrent.futures import ThreadPoolExecutor

import grpc
from grpc_microservice.common.server.request_header_validator_interceptor import RequestHeaderValidatorInterceptor
from grpc_microservice.example.reg_zk.room_proto import room_server_pb2_grpc
from grpc_microservice.example.reg_zk.room_proto.room_server_pb2 import JoinRoomReply
from grpc_microservice.zk_minoter.grpc_decorate import server_monitor
from grpc_microservice.zk_minoter.service_inspection import ServerInspecte

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


class RoomServer(room_server_pb2_grpc.RoomServerServicer):
    server_name = "RoomServer"

    @server_monitor(server_name)
    def RandomJoinRoom(self, request, context):
        """
        随机加入房间
        """
        return JoinRoomReply(common={'code': 400, 'error_msg': "sdf"})

    @server_monitor(server_name)
    def JoinRoom(self, request, context):
        pass

    @server_monitor(server_name)
    def CreateRoom(self, request, context):
        pass

    @server_monitor(server_name)
    def RollOutRoom(self, request, context):
        pass

    @server_monitor(server_name)
    def KicksPlayer(self, request, context):
        pass

    @server_monitor(server_name)
    def PlayerSocketLoss(self, request, context):
        pass


def serve(ip, port):
    server_inspecte = ServerInspecte(balance_strategy="ProcssBalanceStrategy")
    server_inspecte.start()

    header_validator = RequestHeaderValidatorInterceptor(
        'server-uuid', grpc.StatusCode.UNAUTHENTICATED,
        'Access denied!,please connect from zookeeper register')

    server = grpc.server(ThreadPoolExecutor(max_workers=10), interceptors=(header_validator,))
    room_server_pb2_grpc.add_RoomServerServicer_to_server(RoomServer(), server)
    server.add_insecure_port(":".join([ip, port]))
    server.start()
    print("启动成功")

    # 这里进行注册
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve('127.0.0.1', '50002')
