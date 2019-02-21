from grpc_microservice.etcd_minoter.client.client_discovery import ServerDiscovery
from microservice_invoke.room_proto import room_server_pb2
from microservice_invoke.room_proto.room_server_pb2_grpc import RoomServerStubProxy

"""
1000次api调用  2196.0017681121826 ms
"""


def run():
    server_inspecte = ServerDiscovery(balance_strategy="ProcssBalanceStrategy")
    server_inspecte.start()
    server_inspecte.tran_s()
    for x in range(50):
        node_info = server_inspecte.choice_grpc_server('/RoomServer/CreateRoom')
        print(node_info)
        response = RoomServerStubProxy().RandomJoinRoom(room_server_pb2.RandomJoinRoomRequest(player_id=1112, type=3))

        print(response)


if __name__ == '__main__':
    run()
