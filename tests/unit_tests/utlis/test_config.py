import logging

from zntrack import config


def test_config_log_level():
    log = logging.getLogger("zntrack")

    config.log_level = logging.DEBUG
    assert log.level == logging.DEBUG
    config.log_level = logging.ERROR
    assert log.level == logging.ERROR
