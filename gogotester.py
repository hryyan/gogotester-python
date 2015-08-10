__author__ = 'vincent'

Ver = "0.1.0"

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

        self.ipv4_pool = []
        self.ipv6_pool = []

    def search_ipv4(self):
        result = []
        found = 0
        for ip in self.ippool.get_ipv4_addresses():
            if link.test_socket(ip)[0]:
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
        for ip in self.ipv4_pool:
            status = link.test_ssl(ip)
            if status == 200:
                print("%s is avaliable" % ip)

    def gevent_ipv4(self, ip):
        res = link.test_socket(ip)
        if res[0]:
            return ip, res[1]
        return

    def gevent_ipv6(self, ip):
        res = link.test_socket(ip)
        if res[0]:
            return ip, res[1]
        return

    # def gevent_ssl(self, ip):
        # res = link.test_ssl(ip)
        # if link.test_ssl(ip)

    def run(self):
        ipv4s = self.ippool.get_ipv4_addresses()[:400]
        # ipv6s = self.ippool.get_ipv6_addresses()[40]
        jobs = [gevent.spawn(self.gevent_ipv4, ip) for ip in ipv4s]
        gevent.joinall(jobs, timeout=2)
        return jobs


if __name__ == "__main__":
    gogo = Gogotester("./ggc.txt", "config.ini")
    gogo.run()