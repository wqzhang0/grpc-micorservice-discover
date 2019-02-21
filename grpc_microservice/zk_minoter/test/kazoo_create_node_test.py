import datetime
import json
import random

from kazoo.client import KazooClient

# from icode.redis.redis_operation_test import redisOperation

"""
创建子节点数
自己笔记本 i7 1142 count/s
ecs 8核 21 个进程 cpu 60%
8w/s
"""
zk = KazooClient(hosts='127.0.0.1:2181')

ROOT = "/ROOM"
zk.start()

index = 0

room_list = list(range(100, 2050))
room_list = [str(x) for x in room_list]


def random_room():
    # return "/RC_NODE"
    return random.choice(room_list)


if zk.exists(random_room()) is None:
    zk.create(random_room())

print(datetime.datetime.now())
count = 0
_old = datetime.datetime.now()

_server_root = '/grpc'

# etcd_minoter = IKazooClient().get_kazoo_client()
server_name = 'server'
point = 'RandomJoinRoom/'
doc = {"a": "b", "c": "我的天呢"}
zk.create('/'.join([_server_root, server_name, point]),
          value=bytes((json.dumps(doc, ensure_ascii=False)), encoding="utf8"), makepath=True, ephemeral=True,
          sequence=True)

# while (True):
# etcd_minoter.create(random_room() + "/", ephemeral=True, sequence=True, makepath=True)
# count = count + 1
# if count % 8000 == 0:
#     now = datetime.datetime.now()
#     print((now - _old).total_seconds())
#     _old = now
