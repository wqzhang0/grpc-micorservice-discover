import time
import uuid
from functools import wraps

import grpc
from grpc_microservice.etcd_minoter.server.server_register import ServerInspecte
from grpc_microservice.server.common.server.key_pool import SERVER_POOL, SERVER_UUIDS


def server_monitor(server_name, force=False, dec="", weight=100, offline=False):
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
                                                      'ip': '127.0.0.1',
                                                      'port': '50002',
                                                      }
        SERVER_UUIDS[_server_name_uuid] = token

        @wraps(func)
        def wrapper(*args, **kwargs):
            ServerInspecte().update_active_index(_api_name, 1)
            start = time.time()
            print("{} {} invoke".format(_module, _server_name_uuid))
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                # ServerInspecte().update_active_index(_api_name, -1)
                raise e
            else:
            # ServerInspecte().update_active_index(_api_name, -1)
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
    for key, value in SERVER_POOL['servers'].items():
        ServerInspecte().register_server(key, value)
    print("[register server end]")


def choose_address(server_name):
    """
    选择所连接的服务地址 这里预留接口
    """
    # return ServerInspecte().choice_grpc_server(server_name)
    return '127.0.0.1:50002', 'token'


def proxy_grpc_func(stub, module_name):
    _stub = stub
    _module_name = module_name

    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _func = func.__name__
            _point, _token = choose_address('/{}/{}/'.format(_module_name, _func))
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
