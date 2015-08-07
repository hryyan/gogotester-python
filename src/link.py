__author__ = 'vincent'

import time
import socket
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


def test_ssl(ip, cacert, socket_timeout, ssl_timeout):
    try:
        s = build_socket(ip)
        s.settimeout(socket_timeout)
        c = ssl.wrap_socket(s, cert_reqs=ssl.CERT_REQUIRED, ca_certs=cacert, ciphers="ECDHE-RSA-AES127-SHA")
        c.settimeout(ssl_timeout)
        c.connect((ip, 443))
    except (socket.error, socket.timeout):
        return None
    except:
        s = build_socket(ip)
        s.settimeout(socket_timeout)
        c = ssl.wrap_socket(s, cert_reqs=ssl.CERT_REQUIRED, ca_certs=cacert)
        c.settimeout(ssl_timeout)
        c.connect((ip, 443))

    cert = c.getpeercert()
    c.write("""HEAD /search?q=g HTTP/1.1
    Host: www.google.com.hk

    GET /%s HTTP/1.1
    Host: azzvxgoagent%s.appspot.com
    Connection: close

    """ % (platform.python_version() , random.randrange(7)))
    res = c.read(2048)
    cer = [j for j in [i[0] for i in cert["subject"]] if j[0] == "commonName"][0][1]
    # status = parse_res(res)
    # except:
    return