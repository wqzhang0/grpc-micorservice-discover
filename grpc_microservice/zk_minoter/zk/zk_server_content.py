import datetime
import pprint

"""
存放服务节点上下文
"""


class ServerContent():
    SERVER_LIST = {}
    last_update_time = None

    @staticmethod
    def get_list():
        if ServerContent.last_update_time is None or (
                datetime.datetime.now() - ServerContent.last_update_time).total_seconds() > 30:
            ServerContent.last_update_time = datetime.datetime.now()
            print("ServerContent 刷新服务节点--------------------start")
            pprint.pprint(ServerContent.SERVER_LIST)
            print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
            from grpc_microservice.server.zk_minoter.service_inspection import ServerInspecte

            s = ServerInspecte()
            s.read_servers()
            print("ServerContent 刷新服务节点----------------------end")
            pprint.pprint(ServerContent.SERVER_LIST)
            print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")

        return ServerContent.SERVER_LIST

    @staticmethod
    def get_websocket_path(server_node):
        # 获取socket链接地址
        path = ServerContent.get_list().get(server_node, None)
        if path is None:
            from grpc_microservice.server.zk_minoter.service_inspection import ServerInspecte
            s = ServerInspecte()
            s.read_servers()
            print("ServerContent 刷新服务节点----------------------end")
            pprint.pprint(ServerContent.SERVER_LIST)
            path = ServerContent.get_list().get([server_node], None)
        return path['websocket_path']

    @staticmethod
    def get_mq_path(server_node):
        # 获取socket链接地址
        path = ServerContent.get_list().get(server_node, None)
        if path is None:
            from grpc_microservice.server.zk_minoter.service_inspection import ServerInspecte
            s = ServerInspecte()
            s.read_servers()
            print("ServerContent 刷新服务节点----------------------end")
            pprint.pprint(ServerContent.SERVER_LIST)
            path = ServerContent.get_list().get([server_node], None)
        return path['mq_path']
