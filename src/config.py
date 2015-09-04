__author__ = 'vincent'

import configparser
import logging


def read_config(cfg_file=None):
    cfg = configparser.ConfigParser()

    if cfg_file is None:
        cfg["DEFAULT"] = {"limit" : 20,
                          "socket_num": 50,
                          "ssl_num": 50,
                          "socket_timeout": 1,
                          "ssl_timeout": 10}
        logging.info("Don't assign config, use default.")
    else:
        cfg.read(cfg_file)
        logging.info("Use custom config.")

    c = cfg["DEFAULT"]

    logging.info("limit = %s" % c["limit"])
    logging.info("socket_num = %s, ssl_num = %s"
                 % (c["socket_num"], c["ssl_num"]))
    logging.info("socket_timeout = %s, ssl_timeout = %s"
                 % (c["socket_timeout"], c["ssl_timeout"]))

    return cfg

if __name__ == "__main__":
    read_config("../config.ini")