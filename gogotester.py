__author__ = 'vincent'

Ver = "0.1.0"

import asyncio
import ssl
import re
import logging
import math

from src import config
from src import ippool
from src import link

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s - [%(asctime)s] %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')


class GogoLock(asyncio.Lock):
    stop = False


class Gogotester(object):
    """Main Class"""
    def __init__(self, pool_path, config_path=None):
        """Init class"""
        cfg = config.read_config(config_path)["DEFAULT"]
        self.ippool = ippool.Ippool(pool_path)

        self.ipv4_limit = cfg["ipv4_limit"]
        self.ipv6_limit = cfg["ipv6_limit"]
        self.socket_per_thread = cfg["socket_per_thread"]
        self.ssl_per_thread = cfg["ssl_per_thread"]
        self.timeout = cfg["timeout"]
        self.socket_timeout = cfg["socket_timeout"]
        self.ssl_timeout = cfg["ssl_timeout"]

        self.ipv4_pool = []
        self.ipv6_pool = []

        self.lock = GogoLock()

    # 对指定部分ip进行查找
    def search_ip(self, ip_sets, thread_num):
        result = asyncio.Queue()
        ipsets = asyncio.Queue()
        ips = asyncio.Queue()

        for ip in ip_sets:
            ipsets.put_nowait(ip)

        tasks = []
        for i in range(thread_num):
            tasks.append(asyncio.async(link.test_socket(ips, result, self.lock)))
        tasks.append(asyncio.async(link.unfold_ips(ipsets, ips, self.lock)))
        return tasks, result

    def test_ssl(self, search_result, family, thread_num):
        result = asyncio.Queue()
        limit = int(self.ipv4_limit) if family == "IPv4" else int(self.ipv6_limit)

        ssl_ctx = ssl.create_default_context(cafile="/home/vincent/Documents/not-about-work/gogotester-python/cacert.pem")
        ssl_ctx.verify_mode = ssl.CERT_REQUIRED
        ssl_ctx.set_ciphers("ECDHE-RSA-AES128-SHA")
        ssl_ctx.check_hostname = False
        patterns = []
        patterns.append(re.compile("HTTP/1\.[0-1].+?([\d]{1,3})"))
        patterns.append(re.compile("Server: (.+)"))

        tasks = []
        for i in range(thread_num):
            tasks.append(asyncio.async(link.test_ssl(search_result, result, limit,
                                                     ssl_ctx, patterns, self.lock)))
        return tasks, result

    def run(self, ipv4=True, ipv6=False):
        results = []
        tasks = []
        if ipv4 and ipv6:
            thread_num = math.ceil(int(self.socket_per_thread) / 2)
            ssl_num = math.ceil(int(self.ssl_per_thread) / 2)
        else:
            thread_num = math.ceil(int(self.socket_per_thread) / 2)
            ssl_num = math.ceil(int(self.ssl_per_thread))

        if ipv4:
            ipv4_sets = self.ippool.get_ipv4_sets()
            search_v4_tasks, search_v4_result = self.search_ip(ipv4_sets, thread_num)
            ssl_v4_tasks, ssl_v4_result = self.test_ssl(search_v4_result, "IPv4", ssl_num)
            results.append(ssl_v4_result)
            tasks.extend(search_v4_tasks)
            tasks.extend(ssl_v4_tasks)

        if ipv6:
            ipv6_sets = self.ippool.get_ipv6_sets()
            search_v6_tasks, search_v6_result = self.search_ip(ipv6_sets, thread_num)
            ssl_v6_tasks, ssl_v6_result = self.test_ssl(search_v6_result, "IPv6", ssl_num)
            results.append(ssl_v6_result)
            tasks.extend(search_v6_tasks)
            tasks.extend(ssl_v6_tasks)

        loop = asyncio.get_event_loop()
        loop.set_debug(True)
        loop.run_until_complete(asyncio.wait(tasks))
        loop.close()

        for r in results:
            while not r.empty():
                print(r.get_nowait())


if __name__ == "__main__":
    gogo = Gogotester("./ggc.txt", "config.ini")
    gogo.run()