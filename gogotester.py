__author__ = 'vincent'

Ver = "0.1.0"

import logging

from src import config
from src import ippool
from src import link

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')


class Gogotester(object):
    """Main Class"""
    def __init__(self, pool_path, config_path=None):
        """Init class"""
        cfg = config.read_config(config_path)["DEFAULT"]
        self.ippool = ippool.Ippool(pool_path)

        self.params = dict()
        keys = ["limit", "socket_num", "ssl_num",
                "socket_timeout", "ssl_timeout"]
        for k in keys:
            self.params[k] = int(cfg[k])

    def run(self, family="IPv4"):
        if family == "IPv4":
            ipv4_sets = self.ippool.get_ipv4_sets()
            link.run(ipv4_sets, self.params)
        else:
            ipv6_sets = self.ippool.get_ipv6_sets()
            link.run(ipv6_sets, self.params)

if __name__ == "__main__":
    gogo = Gogotester("./ggc.txt", "config.ini")
    gogo.run(family="IPv4")
    # gogo.run(family="IPv6")
