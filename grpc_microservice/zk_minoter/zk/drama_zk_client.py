import time

from grpc_microservice.server.common.meta_cls import Singleton
from kazoo.client import KazooClient
from kazoo.protocol.states import KeeperState, KazooState

ZK_PATH = '127.0.0.1:2181'
"""
etcd_minoter 客户端集成类
"""


class IKazooClient(metaclass=Singleton):

    # zk_client = None

    def __init__(self) -> None:
        super().__init__()
        self.zk_client = KazooClient(hosts=ZK_PATH)
        self.zk_client.start()

    def get_kazoo_client(self):
        """这里加异常捕捉 防止本服务不可以用"""
        while self.zk_client is None or (
                self.zk_client.state in [KeeperState.CLOSED, KeeperState.AUTH_FAILED, KazooState.LOST]):
            try:
                if self.zk_client.state in [KeeperState.CLOSED, KeeperState.AUTH_FAILED, KazooState.LOST]:
                    print("ERROR : zookeeper  尝试重连")
                    self.zk_client.restart()
                    # 重新注册服务
                    # re_register()
                time.sleep(1)
            except Exception:
                print(self.zk_client)
                if self.zk_client is not None:
                    print(self.zk_client.state)
                print("ERROR : zookeeper  连接失败  socket 节点选取将不可以用!!!!!!!!!!!!!!!!!!!")
        return self.zk_client
