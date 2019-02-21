import threading

from grpc_microservice.etcd_minoter.client.client_discovery import ServerDiscovery
from grpc_microservice.example.reg_etcdv3.room_proto import room_server_pb2
from grpc_microservice.example.reg_etcdv3.room_proto.room_server_pb2_grpc import RoomServerStubProxy

"""
1000次api调用  2196.0017681121826 ms
"""


def req():
    while True:
        response = RoomServerStubProxy().RandomJoinRoom(room_server_pb2.RandomJoinRoomRequest(player_id=1112, type=3))
    print(response)


def run():
    server_inspecte = ServerDiscovery(balance_strategy="LeastActiveLoadBalance")
    server_inspecte.start()
    server_inspecte.tran_s()

    # _history = {}
    for x in range(1):
        t = threading.Thread(target=req, name='LoopThread')
        t.start()

    # print(iid)
    #     response = RoomServerStubProxy().RandomJoinRoom(room_server_pb2.RandomJoinRoomRequest(player_id=1112, type=3))
    #
    # print(response)
    # print(_history)
    # time.sleep(5)


if __name__ == '__main__':
    run()
