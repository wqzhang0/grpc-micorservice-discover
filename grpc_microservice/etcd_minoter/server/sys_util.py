import os
import platform
import socket

SO_BINDTODEVICE = 25


def getIP():
    sysstr = platform.system()
    if (sysstr == "Windows"):
        ip = '127.0.0.1'
        # ip = [a for a in os.popen('route print').readlines() if ' 0.0.0.0 ' in a][0].split()[-2]
        print("Call Windows tasks")
    elif (sysstr == "Linux"):
        print("Call Linux tasks")
        ip = [a for a in os.popen('/sbin/route').readlines() if 'default' in a][0].split()[1]
    else:
        raise Exception('can\'t get ip addredd')
    return ip


# iface参数指Linux的网卡接口，如(eth0,wlan0)，这个参数只支持Linux并且需要root权限
def get_free_port(iface=None):
    s = socket.socket()

    if iface:
        s.setsockopt(socket.SOL_SOCKET, SO_BINDTODEVICE, bytes(iface, 'utf8'))

    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return str(port)
