__author__ = 'vincent'

import IPy
import re
import logging
import random


def trans_v4(line):
    pattern = re.compile("([\d-]{1,7})\.([\d-]{1,7})\.([\d-]{1,7})\.([\d-]{1,7})")
    pattern2 = re.compile("(\d{1,3})-(\d{1,3})")
    parts = pattern.match(line).groups()
    all_parts = ["0"] * 4
    idx = 0
    mask_len = 0
    for p in parts:
        r = pattern2.match(p)
        if r:
            low, high = [int(i) for i in r.groups()]
            mask_len += 10 - len(bin(high-low))
            all_parts[idx] = str(low)
            idx += 1
            break
        else:
            fix = int(p)
            mask_len += 8
            all_parts[idx] = str(fix)
            idx += 1

    ip = ".".join(all_parts) + "/%d" % mask_len
    return IPy.IP(ip)


def trans_v6(line):
    if line == "\n":
        return
    ips = IPy.IP(line.rstrip())
    return ips


class Ippool(object):
    """Google ip pools"""
    def __init__(self, ippool_path):
        self.ipv4 = []
        self.ipv6 = []
        self.ippool_path = ippool_path
        self.pools = None

        self.read_from_file()

    def read_from_file(self):
        ipv4_pattern = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}")
        ipv6_pattern = re.compile("[a-z0-9]{1,4}:")

        with open(self.ippool_path, "r") as f:
            for line in f.readlines():
                if line.startswith("#"):
                    continue
                else:
                    if ipv4_pattern.match(line):
                        self.ipv4.append(trans_v4(line))
                    elif ipv6_pattern.match(line):
                        self.ipv6.append(trans_v6(line))

        random.shuffle(self.ipv4)
        random.shuffle(self.ipv6)
        # self.ipv4 = sorted(self.ipv4)
        # self.ipv4 = list(reversed(self.ipv4))

        self.ipv4_count = 0
        self.ipv6_count = 0

        for ips in self.ipv4:
            self.ipv4_count += len(ips)
        for ips in self.ipv6:
            self.ipv6_count += len(ips)

        logging.info("IPv4 pool has %d addresses" % self.ipv4_count)
        logging.info("IPv6 pool has %d addresses" % self.ipv6_count)

    def get_ipv4_sets(self):
        return self.ipv4

    def get_ipv6_sets(self):
        return self.ipv6

    def get_ipv4_num(self):
        return self.ipv4_count

    def get_ipv6_num(self):
        return self.ipv6_count

if __name__ == "__main__":
    # ippool = Ippool("")
    print(trans_v4("118.174.24-27.0-255"))
