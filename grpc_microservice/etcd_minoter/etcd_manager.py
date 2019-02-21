import logging

import etcd3
from grpc_microservice.common.meta_cls import Singleton

"""
基于etcd的服务监听
"""


class EtcdServer(metaclass=Singleton):
    log = logging.getLogger(__name__)

    def __init__(self, logger=None):
        self.logger = logger or self.log
        self.ROOT = '/GRPC'
        self.etcd_client = etcd3.client(host='127.0.0.1', port=2379)
        # self.etcd_client = etcd3.client(host='192.168.0.105', port=2379)
        # self.etcd_client = etcd3.client(host='wqzhangHost', port=2379)
        # self.etcd_client = etcd3.client()


if __name__ == '__main__':
    # log = logging.basicConfig(
    #     level=logging.DEBUG
    #     , stream=sys.stdout
    #     , format='%(asctime)s %(pathname)s %(funcName)s%(lineno)d %(levelname)s: %(message)s')

    # server_inspecte = ServerInspecte(log)
    # server_inspecte = ServerInspecte(log)
    # server_inspecte = ServerInspecte(log)
    # server_inspecte.start()
    print("启动成功")
