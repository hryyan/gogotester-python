__author__ = 'vincent'

import asyncio
import time
import re
import ssl
import platform
import random
import logging

ssl_ctx = ssl.create_default_context(cafile="/home/vincent/Documents/not-about-work/gogotester-python/cacert.pem")
ssl_ctx.verify_mode = ssl.CERT_REQUIRED
ssl_ctx.set_ciphers("ECDHE-RSA-AES128-SHA")
ssl_ctx.check_hostname = False
patterns = []
patterns.append(re.compile("HTTP/1\.[0-1].+?([\d]{1,3})"))
patterns.append(re.compile("Server: (.+)"))


@asyncio.coroutine
def unfold_ips1(ipsets, socket_limit, ssl_limit, result_num, infos, family="IPv4"):
    infos["family"] = family
    infos["tested"] = 0
    infos["remain"] = infos["ip_num"]
    infos["found"] = 0
    logging.info("Search in %s", family)
    logging.info("%(family)s total: %(ip_num)s" % infos)

    ssl_ctx = ssl.create_default_context(cafile="/home/vincent/Documents/not-about-work/gogotester-python/cacert.pem")
    ssl_ctx.verify_mode = ssl.CERT_REQUIRED
    ssl_ctx.set_ciphers("ECDHE-RSA-AES128-SHA")
    ssl_ctx.check_hostname = False
    patterns = []
    patterns.append(re.compile("HTTP/1\.[0-1].+?([\d]{1,3})"))
    patterns.append(re.compile("Server: (.+)"))

    socket_result = asyncio.Queue()
    ssl_result = asyncio.Queue()
    index = 0

    while ssl_result.qsize() < result_num:
        ip_set = ipsets[index]
        index += 1
        ips = [ip.strNormal() for ip in list(ip_set)]
        ips_len = len(ips)
        tasks = []

        try:
            while len(ips) != 0:
                tasks.clear()
                for i in range(socket_limit):
                    try:
                        tasks.append(asyncio.async(test_socket(ips.pop(), socket_result)))
                    except IndexError:
                        continue
                yield from asyncio.wait(tasks)
        except:
            continue

        if socket_result.empty():
            continue
        socket_result_list = []
        while not socket_result.empty():
            socket_result_list.append(socket_result.get_nowait())

        try:
            while len(socket_result_list) != 0 and ssl_result.qsize() < result_num:
                tasks.clear()
                for i in range(ssl_limit):
                    try:
                        tasks.append(
                            asyncio.async(
                                test_ssl(socket_result_list.pop(), ssl_result, ssl_ctx, patterns, result_num)))
                    except IndexError:
                        continue
                yield from asyncio.wait(tasks)
        except:
            continue

        infos["tested"] += ips_len
        infos["remain"] -= ips_len
        infos["found"] = ssl_result.qsize()
        logging.info("%(family)s tested: %(tested)s, %(family)s remain: %(remain)s", infos)
        logging.info("%(family)s found: %(found)s", infos)

    result = []
    while not ssl_result.empty():
        result.append(ssl_result.get_nowait())

    infos["found"] = ssl_result.qsize()
    logging.info("%(family)s search quit, found %(found)s available ips", infos)
    for i in result[:result_num]:
        logging.info("ips: %s" % i)


@asyncio.coroutine
def test_socket1(ip, result):
    try:
        logging.debug("Socket: %s", ip)
        connect = asyncio.open_connection(ip, 443)
        reader, writer = yield from asyncio.wait_for(connect, timeout=1)
        yield from asyncio.sleep(0.0001)
        writer.close()
        connect.close()
        yield from result.put(ip)
    except:
        return


@asyncio.coroutine
def test_ssl1(ip, result, ssl_ctx, patterns, limit):
    try:
        if result.qsize() > limit:
            return
        logging.debug("SSL: %s", ip)
        connect = asyncio.open_connection(ip, 443, ssl=ssl_ctx, server_hostname="")
        reader, writer = yield from asyncio.wait_for(connect, timeout=10)
        yield from asyncio.sleep(0.0001)

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
            yield from result.put((ip, s, n))
        writer.close()
    except:
        return


import eventlet
from eventlet.green import socket
from eventlet.green import ssl

cert = "/home/vincent/Documents/not-about-work/gogotester-python/cacert.pem"
ciphers = "ECDHE-RSA-AES128-SHA"
query = ("HEAD /search?q=g HTTP/1.1\r\nHost: www.google.com.hk\r\n\r\n"
         "GET /%s HTTP/1.1\r\nHost: azzvxgoagent%s.appspot.com\r\n"
         "Connection: close\r\n\r\n") % (platform.python_version(), random.randrange(7))
ctx = ssl.create_default_context(cafile=cert)
ctx.verify_mode = ssl.CERT_REQUIRED
ctx.set_ciphers(ciphers)
ctx.check_hostname = False

def test_socket(ip_q, socket_q):
    while True:
        c = socket.socket()
        c.settimeout(1)
        try:
            ip = ip_q.get()
        except eventlet.queue.Empty:
            eventlet.sleep(0.1)
            continue
        try:
            # print("tested %s", ip)
            c.connect((ip, 443))
            socket_q.put(ip)
        except:
            continue

def test_ssl(socket_q, ssl_q):
    while True:
        try:
            ip = socket_q.get()
        except eventlet.queue.Empty:
            eventlet.sleep(0.1)
            continue
        if ssl_q.qsize() > 10:
            exit(1)
        c = socket.socket()
        c.settimeout(1)
        a = ctx.wrap_socket(c)
        a.settimeout(10)
        s = []
        n = []
        try:
            a.connect((ip, 443))
            a.send(query.encode('latin1'))
            r = a.recv(4096).decode('latin1')
            lines = r.split("\n")
            for line in lines:
                status = patterns[0].search(line)
                server_name = patterns[1].search(line)
                if status:
                    status = status.group[1]
                    s.append(status)
                if server_name:
                    server_name = server_name.group[1]
                    n.append(server_name[:-1])
            print(lines)
            if "200" in s:
                print(ip)
                ssl_q.put(ip)
        except:
            continue

def ip_producer(ipsets, ip_q):
    while True:
        if ip_q.qsize() < 100:
            ip_set = ipsets.pop()
            ips = [ip.strNormal() for ip in list(ip_set)]
            for ip in ips:
                ip_q.put(ip)
        else:
            eventlet.sleep(0.1)


def run(ipsets, socket_limit, ssl_limit, result_num, infos, family="IPv4"):
    pool = eventlet.GreenPool(socket_limit+ssl_limit+1)
    ip_q = eventlet.Queue()
    ssl_q = eventlet.Queue()
    socket_q = eventlet.Queue()

    while True:
        pool.spawn(ip_producer, ipsets, ip_q)

        for i in range(socket_limit):
            pool.spawn(test_socket, ip_q, socket_q)

        for i in range(ssl_limit):
            pool.spawn(test_ssl, socket_q, ssl_q)


if __name__ == "__main__":
    from eventlet.green import ssl
    from eventlet.green import socket
    a = socket.socket()
    ctx = ssl.create_default_context(cafile=cert)
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.set_ciphers(ciphers)
    ctx.check_hostname = False
    ctx.wrap_socket(a)

