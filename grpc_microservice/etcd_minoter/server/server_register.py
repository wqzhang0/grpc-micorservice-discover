import json
import logging
import threading
import time
import uuid
from functools import wraps

from etcd3.exceptions import Etcd3Exception

from grpc_microservice.common.meta_cls import Singleton

from grpc_microservice.common.server.key_pool import SERVER_POOL, SERVER_UUIDS
from grpc_microservice.etcd_minoter.etcd_manager import EtcdServer



def server_monitor(server_name, force=False, dec="", weight=100, offline=False, port=''):
    """
    初始化服务名称,并且在被调用时监听
    """
    _module = server_name

    def decorate(func):
        _api_name = func.__name__
        _server_name_uuid = '/' + '/'.join([_module, _api_name])
        if not SERVER_POOL.get('per_info', None):
            SERVER_POOL['per_info'] = {}
        token = str(uuid.uuid1())
        SERVER_POOL['per_info'][_server_name_uuid] = {'doc': func.__doc__,
                                                      'force': force,
                                                      'dec': dec,
                                                      'weight': weight,
                                                      'offline': offline,
                                                      'uuid': token,
                                                      'ip': '',
                                                      'port': port,
                                                      'pro': True,
                                                      'invoker_count': 0,
                                                      'active_index': 0,
                                                      }
        SERVER_UUIDS[_server_name_uuid] = token

        @wraps(func)
        def wrapper(*args, **kwargs):
            ServerInspecte().update_active_index(_server_name_uuid, 1)
            start = time.time()
            print("{} {} invoke".format(_module, _server_name_uuid))
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                ServerInspecte().update_active_index(_server_name_uuid, -1)
                raise e
            else:
                # pass
                ServerInspecte().update_active_index(_server_name_uuid, -1)
            end = time.time()
            print(func.__name__, end - start)
            return result

        return wrapper

    return decorate


def register_module(generic_handler):
    """
    与自定义服务名进行校验，成功注入到服务中心中去
    """
    _name = generic_handler._name
    SERVER_POOL['MODULE'] = _name
    _method_handlers = generic_handler._method_handlers
    keys = [_key[0] for _key in _method_handlers.items()]
    check_servers = {}

    print('[scan server start]')
    for server_key in keys:
        if server_key in SERVER_POOL['per_info'].keys():
            check_servers[server_key] = SERVER_POOL['per_info'][server_key]
            print('{}--->>{}'.format(server_key, SERVER_POOL['per_info'][server_key]))
        else:
            raise Exception(
                'Server bind fails ,please check @server_monitor(>>server_name<<)  param is correct ,lack point : {}'.format(
                    server_key))
    SERVER_POOL['servers'] = check_servers
    SERVER_POOL.pop('per_info')
    print('[scan server end]')

    print("[register server start")
    ServerInspecte().add_provide_server(check_servers)
    print("[register server end]")


class LeaseInvide(Exception):
    """
    节点无效
    """
    pass


class ServerInspecte(EtcdServer, metaclass=Singleton):
    log = logging.getLogger(__name__)

    def __init__(self, logger=None, env='production'):
        super().__init__(logger)
        self._lease = None
        self.provide_server = None
        self.logger = logger or self.log
        self.env = env  # debug

    def start(self, ip, port):
        """开始服务调用接口"""
        self.logger.info("etcd_minoter 注册中心启动成功")
        self.update_port(ip, port)
        self.register_server()

        t = threading.Thread(target=self.loop, name='LoopThread')
        t.start()

    def loop(self):
        while True:
            self.logger.info("刷新服务开始")
            try:
                granted_ttl, remaining_ttl = self.fresh_lease()
                next_flush_time = int(granted_ttl / 3 * 2)
                for k, v in self.provide_server.items():
                    if v.get('need_flush', False):
                        key = '{}{}/{}'.format(self.ROOT, k, v['uuid'])
                        _v, _meta = self.etcd_client.get(key)
                        if _v:
                            _v = _v.decode("utf-8")
                            context = json.loads(_v, encoding='utf-8')
                            context['active_index'] = v['active_index']
                            context['invoker_count'] = v['invoker_count']
                            self.etcd_client.put(key, json.dumps(context, ensure_ascii=False), lease=_meta.lease_id)
                        self.provide_server[k]['need_flush'] = False
                time.sleep(next_flush_time)

            except LeaseInvide:
                self.logger.info("lease 过期")
                self.register_server()

            except Etcd3Exception as e:
                self.logger.info("刷新服务 异常", e)
                time.sleep(3)

    def update_active_index(self, server_name, num):
        self.provide_server[server_name]['active_index'] += num
        if num == 1:
            self.provide_server[server_name]['invoker_count'] += num
        self.provide_server[server_name]['need_flush'] = True

    def register_server(self):
        """
        注册服务
        """

        self._lease = self.etcd_client.lease(3)
        if (not self.provide_server) or (not isinstance(self.provide_server, dict)):
            self.logger.info('没有服务可以进行注册，请检查。如果是初始化阶段请忽略')
        else:
            for k, v in self.provide_server.items():
                self.etcd_client.put('{}{}/{}'.format(self.ROOT, k, v['uuid']), json.dumps(v, ensure_ascii=False),
                                     self._lease)

    def update_port(self, ip, port):
        # 设置服務端口號
        _dict = self.provide_server
        for k in _dict.keys():
            self.provide_server[k]['ip'] = ip
            self.provide_server[k]['port'] = port

    def add_provide_server(self, _server):
        """
        增加要注册的服务
        """
        assert isinstance(_server, dict)
        self.provide_server = _server

    def fresh_lease(self):
        """
        检查lease 是否活跃
        """
        if self._lease is None:
            raise LeaseInvide("无lease")
        else:
            self._lease.refresh()
            self.logger.info('刷新节点')

            remaining_ttl = self._lease.remaining_ttl
            granted_ttl = self._lease.granted_ttl
            if remaining_ttl == -1:
                raise LeaseInvide("lease invalid")

            return granted_ttl, remaining_ttl
