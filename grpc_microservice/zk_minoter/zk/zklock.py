import threading


class zkLock(object):

    def __init__(self):
        self._call_back_data = None

    def get_call_back_data(self):
        return self._call_back_data

    def zk_async(self, zk, room_id, callback, _data, app_path="/ROOM"):

        self.cv = None
        self.zk = zk
        self.app_path = app_path
        self.biz_path = "/".join([self.app_path, str(room_id)])
        self.handler = callback
        self._data = _data
        self.room_id = room_id
        self.zk_acquire()

    def zk_acquire(self):
        """
        这里设置节点 并且监听
        """
        # 创建子节点
        self.node_path = self.zk.create("/".join([self.biz_path, ""]), sequence=True, ephemeral=True, makepath=True)
        self.node_number = int(self.node_path.split("/")[-1])

        self.zk_handler_event()

    def zk_handler_event(self):
        # 判断是否是最小节点
        is_min, pre_node = self.zk_get_min_node()
        if is_min:
            try:
                self._call_back_data = self.handler(self._data)

                if self.cv:
                    self.cv.acquire()
                    self.cv.notifyAll()
                    self.cv.release()
            finally:
                self.zk_release()
        else:
            # 监听节点
            self.zk_watch_node(pre_node)

    def zk_watch_pre_node(self, event):
        # event
        self.zk_handler_event()

    def zk_watch_node(self, pre_node):
        """
        监听上一个节点
        """
        _watch_node = self.zk.exists(pre_node, watch=self.zk_watch_pre_node)
        if _watch_node == None:
            self.zk_handler_event()
        else:
            self.cv = threading.Condition()
            self.cv.acquire()
            self.cv.wait()

    def zk_release(self):
        """
        释放节点
        """
        self.zk.delete(self.node_path)

    def zk_get_min_node(self):
        node_list = self.zk.get_children(self.biz_path, )
        sort_list = []
        for node_child in node_list:
            sort_list.append(int(node_child))
        sort_list.sort()
        if self.node_number == sort_list[0]:
            # 获得锁
            # print("获得锁")
            return True, ""
        else:
            sort_list.reverse()
            for index, value in enumerate(sort_list):
                if value < self.node_number:
                    pre = value
                    pre = str(pre).zfill(10)
                    return False, "/".join([self.biz_path, pre])
            raise NoPreNodeException("room_id:[%s],this_node:[%s]" % (self.room_id, self.node_number))


class NoPreNodeException(Exception):
    pass
