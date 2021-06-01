""" Standard python init file for the main directory """
from .core.dvc_op import DVCOp

import logging
import sys

# Start logging session to sys.out - No FILELOG is being created!

root = logging.getLogger()
while root.hasHandlers():
    root.removeHandler(root.handlers[0])

root.setLevel(logging.DEBUG)  # <- seems to be the lowest possible loglevel so we set it to debug here!
# if we set it to info, we can not set the file oder stream to debug

# Logging to the stdout (Terminal, Jupyter, ...)
# NOTE never run matplotlib with level debug!
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.DEBUG)  # <- stdout loglevel ##### <- set here ####### <- set here

formatter = logging.Formatter('%(asctime)s - %(name)s (%(levelname)s) - %(message)s')
stream_handler.setFormatter(formatter)
# attaching the stdout handler to the configured logging
root.addHandler(stream_handler)

# get the file specific logger to get information where the log was written!
log = logging.getLogger(__name__)

log.info("Start logging!")