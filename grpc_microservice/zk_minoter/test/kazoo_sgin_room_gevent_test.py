import datetime
import time

from icode.redis.redis_operation_test import redisOperation
from kazoo.client import KazooClient
from zk.zk_wrapper import zkWatch

zk = KazooClient(hosts='127.0.0.1:2181')

ROOT = "/ROOM"
zk.start()

ROOM_ID = "12354"

import gevent
from gevent import monkey

monkey.patch_socket()
"""
600 线程 120count/s
单个节点下数据 160 count/s
"""


# def get_children_watch(event):
#     print(event)

#
# class pre_node_delete(namedtuple("event", "type,state,path")):
#     # print(event)
#     pass


def w2(room_path, path):
    def decorator(func):
        # @functools.wrap(func)
        def wrapper(event):
            return func(room_path, path, event.path, event.state, event.type)

        return wrapper

    return decorator


#
# def watchmethod(func):
#     # def decorated(handler, atype, state, path):
#     def decorated(event):
#         # _evnet = namedtuple("event", ["type,state,path"])
#         # _evnet(event)
#         return func(event.path, event.state, event.type)
#
#     return decorated


# @watchmethod
def watch_pre_node(room_path, self_path, path, state, type):
    # 被唤醒，查看是否最小，最小执行，否则继续监听比自己小的
    check_or_process(self_path)
    # node_list = etcd_minoter.get_children(room_path)
    # sort_list = []
    # for node_child in node_list:
    #     sort_list.append("/".join([ROOT, ROOM_ID, node_child]))
    # sort_list.sort()
    # print('---------------------------节点排序-------------------------')
    # print(sort_list)
    # print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
    # if self_path == sort_list[0]:
    #     # 获得锁
    #     print("获得锁:%s" % self_path)
    # else:
    #     print("监听自己上一位node :%s" % sort_list[-2])
    #     etcd_minoter.exists(sort_list[-2], watch=w2(room_path, self_path)(watch_pre_node))


def check_or_process(tmp_node):
    suffix_num = int(tmp_node.split('/')[-1])
    room_path = "/".join([ROOT, ROOM_ID])
    node_list = zk.get_children(room_path)
    sort_list = []
    for node_child in node_list:
        # sort_list.append("/".join([ROOT, ROOM_ID, node_child]))
        sort_list.append(int(node_child))
    sort_list.sort()
    print('---------------------------节点排序-------------------------')
    print(sort_list)
    print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
    if suffix_num == sort_list[0]:
        # 获得锁
        print("获得锁")
        """执行任务 2s删除自己节点"""
    else:
        pre = None
        for index, value in enumerate(sort_list):
            if value >= suffix_num:
                pre = sort_list[index - 1]
                break
        if pre is None:
            pre = sort_list[-1]
        pre = str(pre).zfill(10)
        print("监听比自己小的上一位node :%s" % pre)
        zk.exists("/".join([ROOT, ROOM_ID, pre]), watch=w2(room_path, tmp_node)(watch_pre_node))
        print(node_list)
        # 创建房间
        if not zk.exists("/".join([ROOT, ROOM_ID])):
            zk.create("/".join([ROOT, ROOM_ID]))


def i_create():
    # 创建临时
    tmp_node = zk.create("/".join([ROOT, ROOM_ID, ""]), sequence=True, ephemeral=True)
    check_or_process(tmp_node)
    # node_list = etcd_minoter.get_children("/".join([ROOT, ROOM_ID]), watch=get_children_watch)


def getLockCallback(path):
    """
    获取锁 需要2秒释放自己
    """
    zk.delete(path)


rds = redisOperation.get_redis()
index = 0


def test_call(_data):
    # print("handler process .... start")
    # print(_data)
    # time.sleep(random.randint(0,3))
    # print("handler process .... end")
    # global  rds
    # room_incr = rds.incr("ROOM")
    global index
    index = index + 1
    if index % 1000 == 0:
        print(index)
        print(datetime.datetime.now())
    # print(index)
    # if 8000 == room_incr:
    #     print(datetime.datetime.now())
    # if room_incr % 200 == 0:
    #     for x in range(200):
    #         # self, etcd_minoter, biz_path, callback
    #         t = threading.Thread(target=zkWatch, args=(etcd_minoter, "/".join([ROOT, ROOM_ID]), test_call, "wolegecao"), name="")
    #         t.start()


# etcd_minoter.exists()
print(datetime.datetime.now())

gevent.joinall(
    [
        gevent.spawn(zkWatch, zk, "/".join([ROOT, ROOM_ID]), test_call, "wolegecao") for x in range(8000)
    ]
)

# for x in range(8000):
#     # self, etcd_minoter, biz_path, callback
#     zkWatch(etcd_minoter, "/".join([ROOT, ROOM_ID]),test_call,"wolegecao")
#     # t = threading.Thread(target=zkWatch, args=(etcd_minoter, "/".join([ROOT, ROOM_ID]), test_call, "wolegecao"), name="")
# t.start()
# t.join()

# i_create()

while (True):
    time.sleep(1000)
# etcd_minoter.create(join(ROOT, ROOM_ID))
# if etcd_minoter.exists(join(ROOT, ROOM_ID)):
#     print(etcd_minoter.get_children(join(ROOT, ROOM_ID)))
# else:
#     etcd_minoter.create(join(ROOT, ROOM_ID))
