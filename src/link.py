__author__ = 'vincent'

import asyncio
import time
import re
import ssl
import platform
import random
import logging


@asyncio.coroutine
def watch_dog(ipsets, ips, result, ippool):
    logging.info("IPv4 total: %s, IPv6 total: %s" % (ippool.get_ipv4_num(), ippool.get_ipv6_num()))
    while True:
        yield from asyncio.sleep(1)
        logging.info("remain IPv4: %s, remain IPv6: %s" % (ippool.get_ipv4_num(), ippool.get_ipv6_num()))
        logging.info("IP pool status: IPv4 succed %s, IPv6 succed: %s"
                     % (ippool.result()))


@asyncio.coroutine
def unfold_ips(ipsets, ips, lock):
    while True:
        with (yield from lock):
            if lock.stop:
                return
        if ips.empty():
            ip_set = yield from ipsets.get()
            ip_s = [ip.strNormal() for ip in list(ip_set)]
            for ip in ip_s:
                yield from ips.put(ip)
        else:
            yield from asyncio.sleep(0.1)


@asyncio.coroutine
def test_socket(ips, result, lock):
    while True:
        try:
            with (yield from lock):
                if lock.stop:
                    return
            # ip地址不足够，从ipset中生成
            if ips.empty():
                yield from asyncio.sleep(0.1)
                continue
            # 连接
            ip = yield from ips.get()
            # logging.info("Socket: %s" % ip)
            connect = asyncio.open_connection(ip, 443)
            reader, writer = yield from asyncio.shield(asyncio.wait_for(connect, timeout=1))
            writer.close()
            connect.close()
            yield from result.put(ip)
        except (OSError,
                ConnectionRefusedError,
                asyncio.TimeoutError):
            continue


@asyncio.coroutine
def test_ssl(searched, result, limit, ssl_ctx, patterns, lock):
    while True:
        try:
            with (yield from lock):
                if lock.stop:
                    return
                if result.qsize() > limit:
                    lock.stop = True
                    return
            if searched.empty():
                yield from asyncio.sleep(0.1)
                continue
            ip = yield from searched.get()

            logging.info("SSL: %s" % ip)
            connect = asyncio.open_connection(ip, 443, ssl=ssl_ctx, server_hostname="")
            reader, writer = yield from asyncio.shield(asyncio.wait_for(connect, timeout=10))

            query = ("HEAD /search?q=g HTTP/1.1\r\nHost: www.google.com.hk\r\n\r\n"
                     "GET /%s HTTP/1.1\r\nHost: azzvxgoagent%s.appspot.com\r\n"
                     "Connection: close\r\n\r\n") % (platform.python_version(), random.randrange(7))
            writer.write(query.encode('latin1'))
            s = []
            n = []
            while True:
                line = yield from reader.readline()
                if not line:
                    break
                status = patterns[0].search(line.decode('latin1'))
                server_name = patterns[1].search(line.decode('latin1'))
                if status:
                    status = status.group(1)
                    s.append(status)
                if server_name:
                    server_name = server_name.group(1)
                    n.append(server_name[:-1])
            if "200" in s:
                print(ip)
                yield from result.put((ip, s, n))
            writer.close()
        except (OSError,
                ConnectionRefusedError,
                asyncio.TimeoutError,
                asyncio.InvalidStateError,
                ssl.SSLError,
                ssl.SSLEOFError):
            continue


if __name__ == "__main__":
    ssl_ctx = ssl.create_default_context(cafile="../cacert.pem")
    ssl_ctx.verify_mode = ssl.CERT_REQUIRED
    ssl_ctx.set_ciphers("ECDHE-RSA-AES128-SHA")
    ssl_ctx.check_hostname = False
    queue = asyncio.Queue()
    patterns = []
    patterns.append(re.compile("HTTP/1\.[0-1].+?([\d]{1,3})"))
    patterns.append(re.compile("Server: (.+)"))
    loop = asyncio.get_event_loop()
    ip_list = ["216.58.209.130",
               # "216.58.216.225",
               # "173.194.27.72",
               # "74.125.107.234",
               # "173.194.15.166",
               # "216.58.212.79",
               # "173.194.115.5",
               # "173.194.148.213",
               # "113.21.24.3",
               # "212.181.117.10",
               # "212.181.117.6",
               "87.244.198.10",
               "87.244.198.42",
               "87.244.198.98",
               "87.244.198.101",
               "31.7.160.9",
               "31.7.160.59",
               "31.7.160.65",
               "31.7.160.69",
               "31.7.160.149"
               "212.181.117.14"]

    ip_q = asyncio.Queue()
    for ip in ip_list:
        ip_q.put_nowait(ip)

    tasks = []
    for i in range(50):
        tasks.append(asyncio.async(test_ssl(ip_q, queue, 5, ssl_ctx, patterns)))
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()

    print(queue.qsize())

    while not queue.empty():
        print(queue.get_nowait())
