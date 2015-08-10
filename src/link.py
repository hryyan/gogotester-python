__author__ = 'vincent'

import sys
import asyncio
import urllib.parse
import socket
import time
import re
import ssl
import platform
import random


def build_socket(ip):
    pattern_v4 = re.compile("\d{1,3}\.\d{1,3}")
    if pattern_v4.match(str(ip)):
        s = socket.socket()
    else:
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM, 0)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return s


def test_socket(ip, port=443, loop=1, timeout=1):
    try:
        start = time.time()
        for i in range(loop):
            s = build_socket(ip)
            s.settimeout(timeout)
            s.connect((ip, port))
            s.close()
        cost = time.time() - start
        return True, cost/loop
    except socket.error:
        s.close()
        return False, None


def parse_res(res):
    pattern = re.compile("""^(HTTP/... (\d+).*|Server:\s*(\w.*))$""", re.IGNORECASE|re.MULTILINE)

    attributes = pattern.findall(res)
    if attributes:
        status = "NN"
        for i in attributes:
            if i[1] == "200":
                for j in attributes:
                    if j[2] == "gws\r":
                        status = "GA"
                    elif j[2] == "Google Frontend\r":
                        status = "A"
                    else:
                        pass
    if status == "NN":
        return None
    else:
        return status


def test_ssl(ip, cacert=None, socket_timeout=10, ssl_timeout=10):



    # try:
    s = build_socket(ip)
    s.settimeout(socket_timeout)
    c = ssl.wrap_socket(s, cert_reqs=ssl.CERT_REQUIRED, ca_certs=cacert, ciphers="ECDHE-RSA-AES128-SHA")
    c.settimeout(ssl_timeout)
    c.connect((ip, 443))
    # except (socket.error, socket.timeout):
    #     return None
    # except:
    #     s = build_socket(ip)
    #     s.settimeout(socket_timeout)
    #     c = ssl.wrap_socket(s, cert_reqs=ssl.CERT_REQUIRED, ca_certs=cacert)
    #     c.settimeout(ssl_timeout)
    #     c.connect((ip, 443))

    cert = c.getpeercert()
    c.write("""HEAD /search?q=g HTTP/1.1
    Host: www.google.com.hk

    GET /%s HTTP/1.1
    Host: azzvxgoagent%s.appspot.com
    Connection: close

    """ % (platform.python_version(), random.randrange(7)))
    res = c.read(2048)
    print(res)
    cer = [j for j in [i[0] for i in cert["subject"]] if j[0] == "commonName"][0][1]
    status = parse_res(res)
    if status:
        return {"ip": ip, "cname": cer, "status": status}
    return None


if __name__ == "__main__":
    # test_ssl("216.58.209.127", "../cacert.pem")
    # test_socket("173.194.208.219")

    import asyncio
    import urllib.parse
    import sys

    @asyncio.coroutine
    def print_http_headers(url):
        ssl_ctx = ssl.create_default_context(cafile="../cacert.pem")
        ssl_ctx.verify_mode = ssl.CERT_REQUIRED
        ssl_ctx.set_ciphers("ECDHE-RSA-AES128-SHA")
        ssl_ctx.check_hostname = False
        url = urllib.parse.urlsplit(url)
        if url.scheme == 'https':
            connect = asyncio.open_connection(url.hostname, 443, ssl=ssl_ctx, server_hostname="")
        else:
            connect = asyncio.open_connection(url.hostname, 80)
        try:
            reader, writer = yield from connect
        except OSError as e:
            return
        query = ("HEAD /search?q=g HTTP/1.1\r\nHost: www.google.com.hk\r\n\r\n"
                 "GET /%s HTTP/1.1\r\nHost: azzvxgoagent%s.appspot.com\r\n"
                 "Connection: close\r\n\r\n") % (platform.python_version(), random.randrange(7))
        writer.write(query.encode('latin1'))
        while True:
            line = yield from reader.readline()
            if not line:
                break
            line = line.decode('latin1').rstrip()
            if line:
                print('HTTP header> %s' % line)

        # Ignore the body, close the socket
        writer.close()

    url = "https://113.21.24.3"
    # url = "https://216.58.209.130"
    loop = asyncio.get_event_loop()
    task = asyncio.async(print_http_headers(url))
    loop.run_until_complete(task)
    loop.close()
