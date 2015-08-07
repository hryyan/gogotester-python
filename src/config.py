__author__ = 'vincent'

import configparser
import logging


def read_config(cfg_file=None):
    cfg = configparser.ConfigParser()

    if cfg_file is None:
        cfg["DEFAULT"] = {"ipv4_limit" : 20,
                          "ipv6_limit" : 20,
                          "socket_per_thread": 50,
                          "ssl_per_thread": 50,
                          "timeout": 1,
                          "socket_timeout": 10,
                          "ssl_timeout": 10}
        logging.info("Don't assign config, use default.")
    else:
        cfg.read(cfg_file)
        logging.info("Use custom config.")

    c = cfg["DEFAULT"]

    logging.info("ipv4_limit = %s, ipv6_limit = %s"
                 % (c["ipv4_limit"], c["ipv6_limit"]))
    logging.info("socket_per_thread = %s, ssl_per_thread = %s"
                 % (c["socket_per_thread"], c["ssl_per_thread"]))
    logging.info("socket_timeout = %s, ssl_timeout = %s"
                 % (c["socket_timeout"], c["ssl_timeout"]))
    logging.info("timeout = %s" % c["timeout"])

    return cfg

if __name__ == "__main__":
    read_config("../config.ini")