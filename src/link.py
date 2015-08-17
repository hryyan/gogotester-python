__author__ = 'vincent'

import asyncio
import time
import re
import ssl
import platform
import random
import logging


@asyncio.coroutine
def unfold_ips(ipsets, socket_limit, ssl_limit, result_num, infos, family="IPv4"):
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
def test_socket(ip, result):
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
def test_ssl(ip, result, ssl_ctx, patterns, limit):
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
