__author__ = 'vincent'

import re
import platform
import random
import logging
import eventlet
from eventlet.green import socket
from eventlet.green import ssl

cert = "./cacert.pem"
ciphers = "ECDHE-RSA-AES128-SHA"
query = ("HEAD /search?q=g HTTP/1.1\r\nHost: www.google.com.hk\r\n\r\n"
         "GET /%s HTTP/1.1\r\nHost: azzvxgoagent%s.appspot.com\r\n"
         "Connection: close\r\n\r\n") % (platform.python_version(), random.randrange(7))
ctx = ssl.create_default_context(cafile=cert)
ctx.verify_mode = ssl.CERT_REQUIRED
ctx.set_ciphers(ciphers)
ctx.check_hostname = False
patterns = []
patterns.append(re.compile("HTTP/1\.[0-1].+?([\d]{1,3})"))
patterns.append(re.compile("Server: (.+)"))


def test_socket(ip_q, socket_q, ssl_q, socket_timeout):
    while True:
        if ssl_q.full():
            return
        c = socket.socket()
        c.settimeout(socket_timeout)
        try:
            ip = ip_q.get(timeout=2)
        except eventlet.queue.Empty:
            eventlet.sleep(0.1)
            continue
        try:
            c.connect((ip, 443))
            socket_q.put(ip, timeout=2)
        except:
            continue


def test_ssl(socket_q, ssl_q, socket_timeout, ssl_timeout):
    while True:
        if ssl_q.full():
            return
        try:
            ip = socket_q.get(timeout=2)
        except eventlet.queue.Empty:
            eventlet.sleep(0.1)
            continue
        c = socket.socket()
        c.settimeout(socket_timeout)
        a = ctx.wrap_socket(c)
        a.settimeout(ssl_timeout)
        s = []
        n = []
        try:
            a.connect((ip, 443))
            a.send(query.encode('latin1'))
            r = a.recv(4096).decode('latin1')
            if "Alternate-Protocol" in r or "Alt-Svc" in r:
                continue
            lines = r.split("\n")
            for line in lines:
                status = patterns[0].search(line)
                server_name = patterns[1].search(line)
                if status:
                    status = status.groups()[0]
                    s.append(status)
                if server_name:
                    server_name = server_name.groups()[0]
                    n.append(server_name[:-1])
            if "200" in s and ("gws" in n or "Google Frontend" in n):
                ssl_q.put(ip, timeout=2)
                logging.info("Found Ip: %s" % ip)
        except:
            continue


def ip_producer(ipsets, ip_q, ssl_q):
    tested_socket = 0
    last = 0
    first, end = "", ""
    while True:
        found = ssl_q.qsize()
        logging.info("Testing socket: %d-%d, Found %d" % (last, tested_socket, found))
        # logging.info("First: %s, End: %s" % (first, end))
        if ssl_q.full():
            return
        elif ip_q.qsize() < 100:
            try:
                ip_set = ipsets.pop()
            except:
                return
            ips = [ip.strNormal() for ip in list(ip_set)]
            first, end = ips[0], ips[-1]
            last = tested_socket
            tested_socket += len(ips)
            for ip in ips:
                ip_q.put(ip, timeout=2)
        else:
            eventlet.sleep(1)


def terminator(ssl_q, limit, threads):
    while True:
        if ssl_q.full():
            res = []
            while not ssl_q.empty():
                res.append(ssl_q.get())
            logging.info("Avalialbe IPs: %s" % "|".join(res[:limit]))
            exit(0)
        eventlet.sleep(2)


def run(ipsets, params):
    socket_limit = params["socket_num"]
    ssl_limit = params["ssl_num"]
    limit = params["limit"]
    socket_timeout = params["socket_timeout"]
    ssl_timeout = params["ssl_timeout"]

    pool = eventlet.GreenPool(socket_limit+ssl_limit+2)
    ip_q = eventlet.Queue()
    ssl_q = eventlet.Queue(limit)
    socket_q = eventlet.Queue()

    threads = []

    t = pool.spawn(ip_producer, ipsets, ip_q, ssl_q)
    threads.append(t)

    for i in range(socket_limit):
        t = pool.spawn(test_socket, ip_q, socket_q, ssl_q, socket_timeout)
        threads.append(t)

    for i in range(ssl_limit):
        t = pool.spawn(test_ssl, socket_q, ssl_q, socket_limit, ssl_timeout)
        threads.append(t)

    pool.spawn_n(terminator, ssl_q, limit, threads)
    pool.waitall()


if __name__ == "__main__":
    from eventlet.green import ssl
    from eventlet.green import socket
    a = socket.socket()
    ctx = ssl.create_default_context(cafile=cert)
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.set_ciphers(ciphers)
    ctx.check_hostname = False
    ctx.wrap_socket(a)

