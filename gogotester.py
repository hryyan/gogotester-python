__author__ = 'vincent'

Ver = "0.1.0"

# import gevent
# from gevent import lock
# from gevent import monkey
# monkey.patch_os()
# monkey.patch_socket()
# monkey.patch_ssl()

import os
import socket
import time
import logging
import configparser

from src import config
from src import ippool
from src import link


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

    def search_ipv4(self):
        result = []
        found = 0
        for ip in self.ippool.get_ipv4_addresses():
            if link.test_socket(ip):
                result.append(link)
                found += 1
            if found == self.ipv4_limit:
                break
        return result

    def search_ipv6(self):
        result = []
        found = 0
        for ip in self.ippool.get_ipv6_addresses():
            if link.test_socket(ip):
                result.append(link)
                found += 1
            if found == self.ipv6_limit:
                break
        return result

    def test_ssl(self):
        pass

    def run(self):
        pass


if __name__ == "__main__":
    gogo = Gogotester("./ggc.txt", "config.ini")
    gogo.search_ipv4()