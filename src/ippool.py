__author__ = 'vincent'

import IPy
import re


def get_all_ips(all_parts):
    ips = []
    ip = ""
    len_i = 0
    for i in all_parts[0]:
        ip = ip[:len_i] + str(i) + '.'
        len_j = len(ip)
        for j in all_parts[1]:
            ip = ip[:len_j] + str(j) + '.'
            len_k = len(ip)
            for k in all_parts[2]:
                ip = ip[:len_k] + str(k) + '.'
                len_l = len(ip)
                for l in all_parts[3]:
                    ip = ip[:len_l] + str(l)
                    ips.append(ip)
    return ips


def trans_v4(line):
    pattern = re.compile("([\d-]{1,7})\.([\d-]{1,7})\.([\d-]{1,7})\.([\d-]{1,7})")
    pattern2 = re.compile("(\d{1,3})-(\d{1,3})")
    parts = pattern.match(line).groups()
    all_parts = []
    for p in parts:
        r = pattern2.match(p)
        if r:
            low, high = [int(i) for i in r.groups()]
            low = low + 1 if low == 0 else low
            high = high if high == 255 else high + 1
            all_parts.append(range(low, high))
        else:
            fix = int(p)
            all_parts.append(range(fix, fix+1))

    return get_all_ips(all_parts)


def trans_v6(line):
    if line == "\n":
        return
    ips = IPy.IP(line.rstrip())
    return [i.strNormal() for i in ips]


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
                        self.ipv4.extend(trans_v4(line))
                    elif ipv6_pattern.match(line):
                        self.ipv6.extend(trans_v6(line))

    def get_ipv4_addresses(self):
        return self.ipv4

    def get_ipv6_addresses(self):
        return self.ipv6


if __name__ == "__main__":
    # ippool = Ippool("")
    print(trans_v4("118.174.24-27.0-255"))
