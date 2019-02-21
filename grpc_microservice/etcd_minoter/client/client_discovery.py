import json
import logging
import threading
from functools import wraps

import grpc
from etcd3.events import PutEvent, DeleteEvent
from grpc_microservice.common.client import header_manipulator_client_interceptor
from grpc_microservice.common.exceptions import NoServerNodeException
from grpc_microservice.common.meta_cls import Singleton, time_this
from grpc_microservice.etcd_minoter.client.load_balance import LeastActiveLoadBalance, RandomLoadBalance
from grpc_microservice.etcd_minoter.etcd_manager import EtcdServer


def choose_address(server_name, **kwargs):
    """
    选择所连接的服务地址 这里预留接口
    """
    return ServerDiscovery().choice_grpc_server(server_name, **kwargs)


def proxy_grpc_func(stub, module_name):
    _stub = stub
    _module_name = module_name

    def decorate(func):
        @time_this
        @wraps(func)
        def wrapper(*args, **kwargs):
            _func = func.__name__
            _point, _token = choose_address('/{}/{}'.format(_module_name, _func), **kwargs)
            #
            header_adder_interceptor = header_manipulator_client_interceptor.server_access_interceptor(_token)
            with grpc.insecure_channel(_point) as channel:
                intercept_channel = grpc.intercept_channel(channel, header_adder_interceptor)
                __stub = _stub(intercept_channel)
                _func_stub = getattr(__stub, _func)
                ret = _func_stub(args[1])
                return ret

        return wrapper

    return decorate


class ServerDiscovery(EtcdServer, metaclass=Singleton):
    log = logging.getLogger(__name__)

    def __init__(self, balance_strategy=None, logger=None):
        super().__init__(logger)
        if balance_strategy == "LeastActiveLoadBalance":
            self.balance_strategy = LeastActiveLoadBalance()
        else:
            self.balance_strategy = RandomLoadBalance()
        self.server_colletion = {}
        self.logger = logger or self.log
        self.pro = True  # debug False

    def set_balance_strategy(self, balance_strategy):
        if balance_strategy == "LeastActiveLoadBalance":
            self.balance_strategy = LeastActiveLoadBalance()
        else:
            self.balance_strategy = RandomLoadBalance()

    def start(self, read_once=False):
        """开始服务调用接口"""
        self.read_servers()
        self.logger.info("etcd_minoter 注册中心启动成功")
        if not read_once:
            t = threading.Thread(target=self.loop, name='LoopThread')
            t.start()

    def delete_filter(self, _server_name, _server_uuid):
        if self.server_colletion.get('{}/{}'.format(_server_name, _server_uuid), None):
            self.server_colletion.pop('{}/{}'.format(_server_name, _server_uuid))

        _tmp_force_server = self.__force_server.get(_server_name, [])
        if _server_uuid in _tmp_force_server:
            _tmp_force_server.remove(_server_uuid)
        if len(_tmp_force_server) == 0:
            if self.__force_server.get(_server_name, None):
                self.__force_server.pop(_server_name)
        else:
            self.__force_server[_server_name] = _tmp_force_server

        _tmp_normal_server = self.__normal_server.get(_server_name, [])
        if _server_uuid in _tmp_normal_server:
            _tmp_normal_server.remove(_server_uuid)
        if len(_tmp_normal_server) == 0:
            if self.__normal_server.get(_server_name, None):
                self.__normal_server.pop(_server_name)
        else:
            self.__normal_server[_server_name] = _tmp_normal_server

    def loop(self):
        # 进行监听
        events_iterator, cancel = self.etcd_client.watch_prefix(self.ROOT)
        for event in events_iterator:
            self.logger.info("刷新服务开始")
            if isinstance(event, PutEvent):
                _server_uuid, _server_name, _server_info = self.__read_node(event.key, event.value)
                # 如果只刷新active_index 择刷新 否则重新添加并转化
                _key = '{}/{}'.format(_server_name, _server_uuid)
                old = self.server_colletion.get(_key, None)
                if old:
                    if old['pro'] == _server_info['pro'] and old['force'] == _server_info['force'] and old['weight'] == \
                            _server_info['weight'] and old['offline'] == _server_info['offline'] and old['ip'] == \
                            _server_info['ip'] and old['port'] == _server_info['port']:
                        # 刷新index
                        self.server_colletion[_key]['active_index'] = _server_info['active_index']
                        print('刷新index  ')
                        continue
                print('节点更新  重置操作')
                self.delete_filter(_server_name, _server_uuid)
                # 可能是新增 ,可能是修改 默认覆盖
                self.server_colletion['{}/{}'.format(_server_name, _server_uuid)] = _server_info
                self.tran_s_once(_key, _server_info)
                # 默认新增
            elif isinstance(event, DeleteEvent):
                _server_uuid, _server_name, _ = self.__read_node(event.key, event.value)
                self.delete_filter(_server_name, _server_uuid)
            print(self.server_colletion)

    def tran_s_once(self, _server_name_uuid, _server_info):
        _server_name = "/".join(_server_name_uuid.split('/')[:-1])
        # 过滤下线接口
        if _server_info['pro'] != self.pro or _server_info['offline']:
            return
        # 如果有强制调用的接口
        if _server_info['force']:
            _force_server = self.__force_server.get(_server_name, [])
            _force_server.append(_server_info['uuid'])
            self.__force_server[_server_name] = _force_server
        _normal_server = self.__normal_server.get(_server_name, [])
        _normal_server.append(_server_info['uuid'])
        self.__normal_server[_server_name] = _normal_server

    def tran_s(self):
        self.__normal_server = {}
        self.__force_server = {}
        _server_colletion = self.server_colletion

        for _uuid, _server_info in _server_colletion.items():
            self.tran_s_once(_uuid, _server_info)

    def filter_foce(self, server_name):
        server_pool = self.__force_server.get(server_name, None)
        if server_pool and len(server_pool) > 0:
            return server_pool
        server_pool = self.__normal_server.get(server_name, None)
        if server_pool and len(server_pool) > 0:
            return server_pool
        raise NoServerNodeException('no server can user')

    def __read_node(self, path, value):
        _v = value.decode("utf-8")
        _path = path.decode("utf-8").replace('/GRPC', '').split('/')
        _module = _path[1]
        _api = _path[2]
        _server_uuid = _path[3]
        _server_info = json.loads(_v, encoding='utf-8')
        _server_name = '/{}/{}'.format(_module, _api)
        return _server_uuid, _server_name, _server_info

    def read_servers(self):
        """获取服务列表"""
        self.server_colletion = {}
        childrens = self.etcd_client.get_prefix(self.ROOT)
        for value, _meta in childrens:
            _uuid, _server_name, _server_info = self.__read_node(_meta.key, value)
            self.server_colletion['{}/{}'.format(_server_name, _uuid)] = _server_info

    def get_point(self, server_name, server_key):
        server_node = self.server_colletion[server_name + '/' + server_key['uuid']]
        return ":".join([server_node['ip'], server_node['port']]), server_node['uuid']

    def choice_grpc_server(self, server_name, **kwargs):
        # 根据相应负载策略进行筛选
        uuids = self.filter_foce(server_name)
        server_invokers = []
        for _key in uuids:
            server_invokers.append(self.server_colletion['{}/{}'.format(server_name, _key)])
        return self.get_point(server_name, self.balance_strategy.choice(server_invokers, **kwargs))

    def designation_point(self, ):
        """
        # TODO  指定服务端点调用
        指定服务端点
        """
        # 测试环境分为是否需要验证
        # force 被强制调用，选项 IP：port / uuid
        pass

    # 生产环境只开放生产环境的服务 offline

    # 如果无 唯一调用 选择时 根据规则 权重 进行分配 否则选择强制调用


if __name__ == '__main__':
    server_inspecte = ServerDiscovery(balance_strategy="LeastActiveLoadBalance")
    server_inspecte.start()
    server_inspecte.tran_s()
    for x in range(50):
        node_info = server_inspecte.choice_grpc_server('/RoomServer/CreateRoom')
        print(node_info)
        print("启动成功")
