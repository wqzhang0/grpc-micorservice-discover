import random

from grpc_microservice.common.exceptions import NoServerNodeException


class BalanceStrategy():
    """负载均衡策略"""

    @classmethod
    def choice(self, server_list, **kwargs):
        raise Exception('不能用父类')


class LeastActiveLoadBalance(BalanceStrategy):
    # 最少活跃调用数，相同活跃数的随机。活跃数指调用前后计数差。
    # 使慢的 Provider 收到更少请求，因为越慢的 Provider  的调用前后计数差会越大。
    @classmethod
    def choice(self, server_list, **kwargs):
        # server_list :[{'uuid':_server_info['uuid'],'active_index':_server_info['active_index'],'weight':_server_info['weight']}]
        server_list = server_list.copy()
        server_list.sort(key=lambda x: x['active_index'], reverse=True)
        # 迭代相同的
        _min_server = server_list.pop(0)
        _min_active_index = _min_server['active_index']
        _min_servers = []
        _min_servers.append(_min_server)
        for _server in server_list:
            if _server['active_index'] == _min_active_index:
                _min_servers.append(_server)
            break
        if len(_min_servers) == 1:
            return _min_servers[0]
        else:
            return RandomLoadBalance.choice(_min_servers)


class RandomLoadBalance(BalanceStrategy):
    """随机负载均衡。随机的选择一个。是的默认负载均衡策略。"""

    @classmethod
    def choice(self, server_list, **kwargs):
        # 根据权重 随机取一个节点做匹配
        # server_list :[{'uuid':_server_info['uuid'],'active_index':_server_info['active_index'],'weight':_server_info['weight']}]
        if server_list is None or len(server_list) == 0:
            raise NoServerNodeException()
        total_weight = 0
        same_weight = True
        for index, _server in enumerate(server_list):
            _weight = int(_server['weight'])
            total_weight += _weight
            if (same_weight and index > 0) and (_weight != server_list[index - 1]['weight']):
                same_weight = False
        if total_weight > 0 and not same_weight:
            # 如果不是所有的 Invoker 权重都相同，那么基于权重来随机选择。权重越大的，被选中的概率越大
            offset = random.randrange(total_weight)
            for index, _server in enumerate(server_list):
                offset -= int(_server['weight'])
                if offset < 0:
                    return _server
        return random.choice(server_list)
