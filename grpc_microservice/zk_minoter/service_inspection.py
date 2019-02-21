import datetime
import json
import random

from grpc_microservice.server.common.meta_cls import Singleton
from grpc_microservice.server.zk_minoter.zk.drama_zk_client import IKazooClient
from grpc_microservice.server.zk_minoter.zk.zk_persistent_lock import zkPersistentLock
from grpc_microservice.server.zk_minoter.zk.zk_server_content import ServerContent

"""
基于zk的服务 监听 和选取节点
"""


class BalanceStrategy():
    """负载均衡策略"""

    @classmethod
    def choice(self, server_list):
        # 随便获取一个节点做匹配
        node = random.choice(list(server_list.keys()))
        if node is None:
            return BalanceStrategy.choice(server_list)
        else:
            return node


class ProcssBalanceStrategy(BalanceStrategy):
    """过程负载均衡策略"""


class FinalBalanceStrategy():
    """最终负载均衡策略"""

    @classmethod
    def choice(self, server_list):
        # 优先获取少的
        online_player = [{'websocket_path': v['websocket_path'], 'online_num': v['online_num'], 'server_node': k} for
                         k, v in
                         server_list.items() if v is not None]
        online_player.sort(key=lambda x: x['online_num'])
        if len(online_player) == 0:
            print("没有服务节点 重新选择")
            return self.choice(server_list)
        node = online_player[0]
        if node is None:
            return self.choice(server_list)
        else:
            return node['server_node']


def get_server(way=1):
    if way == 1:
        return ProcssBalanceStrategy.choice(ServerContent.get_list())
    elif way == 2:
        return FinalBalanceStrategy.choice(ServerContent.get_list())


class ServerInspecte(metaclass=Singleton):
    is_master = False

    BIZ_PATH = "websocket"
    WEBSOCKET = "server"

    def __init__(self, balance_strategy=None):
        if balance_strategy == "ProcssBalanceStrategy":
            self.balance_strategy_cls = ProcssBalanceStrategy()
        elif balance_strategy == "FinalBalanceStrategy":
            self.balance_strategy_cls = FinalBalanceStrategy()
        else:
            self.balance_strategy = BalanceStrategy()

    def get_server(self):
        return self.balance_strategy_cls.choice(ServerContent.get_list())

    def server_transfer(self):
        """服务转移"""
        if self.is_master:
            print("----------------触发服务转移----------------")
            pass

    def start(self, ip, port):
        """开始服务调用接口"""
        self.read_servers()
        self.create_master_node()
        print("zk_minoter 注册中心启动成功")

    def read_state(self):
        for node_name in ServerContent.get_list().keys():
            data = IKazooClient().get_kazoo_client().get("/".join([self.BIZ_PATH, self.WEBSOCKET, node_name]))[
                0].decode(
                "utf-8")
            server_node = json.loads(data)
            ServerContent.get_list()[node_name] = server_node
        print(datetime.datetime.now())

    def read_servers(self):
        """获取服务列表"""
        node_list = IKazooClient().get_kazoo_client().get_children("/".join([self.BIZ_PATH, self.WEBSOCKET]),
                                                                   watch=self.server_change_listener)

        tmp_server_list = {}
        for node_name in node_list:
            tmp_server_list[node_name] = None
        ServerContent.SERVER_LIST = tmp_server_list
        self.read_state()

    def server_change_listener(self, event):
        # 服务检测  服务注册,节点状态存在延迟
        IKazooClient().get_kazoo_client().get_children("/".join([self.BIZ_PATH, self.WEBSOCKET]),
                                                       watch=self.server_change_listener)
        self.read_servers()
        self.server_transfer()

    def set_master(self, data):
        self.is_master = True

    def create_master_node(self):
        zkPersistentLock().zk_async(IKazooClient().get_kazoo_client(), "api_server", self.set_master, {},
                                    app_path="websocket")

    def choice_grpc_server(self, server_name):
        _server_root = '/GRPC'
        server_name = _server_root + server_name
        _children = IKazooClient().get_kazoo_client().get_children(server_name)
        server_node = None
        for i in _children:
            v = IKazooClient().get_kazoo_client().get("/".join([server_name, i]))
            server_node = json.loads(str(v[0], encoding='utf-8'))
            break
        if server_node is None:
            raise Exception("没有可用的服务")
        return ":".join([server_node['ip'], server_node['port']]), server_node['uuid']

    def register_server(self, point, doc):
        zk = IKazooClient().get_kazoo_client()
        _server_root = '/GRPC'
        point = point + "/"
        zk.create('/'.join([_server_root, point]),
                  value=bytes((json.dumps(doc, ensure_ascii=False)), encoding="utf8"), makepath=True, ephemeral=True,
                  sequence=True)


if __name__ == '__main__':
    server_inspecte = ServerInspecte(balance_strategy="ProcssBalanceStrategy")
    server_inspecte.start()
    print("启动成功")
