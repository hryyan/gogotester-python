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


class Gogotester(object):
    """Main Class"""
    def __init__(self, pool_path, config_path=None):
        """Init class"""
        cfg = config.read_config(config_path)["DEFAULT"]
        self.ippool = ippool.Ippool(pool_path)

        self.params = dict()
        keys = ["ipv4_limit", "ipv6_limit",
                "socket_per_thread", "ssl_per_thread",
                "timeout", "socket_timeout", "ssl_timeout"]
        for k in keys:
            self.params[k] = int(cfg[k])

    def run(self):
        ipv4_sets = self.ippool.get_ipv4_sets()

        infos = dict()
        infos["ip_num"] = self.ippool.ipv4_count

        loop = asyncio.get_event_loop()
        loop.run_until_complete(link.unfold_ips(ipv4_sets,
                                                self.params["socket_per_thread"],
                                                self.params["ssl_per_thread"],
                                                self.params["ipv4_limit"],
                                                infos))

    def test(self):
        ipv4_sets = self.ippool.get_ipv4_sets()
        link.run(ipv4_sets, 900, 50, 10, dict())

if __name__ == "__main__":
    gogo = Gogotester("./ggc.txt", "config.ini")
    # gogo.run()
    gogo.test()