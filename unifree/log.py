#!/usr/bin/env python3

# Copyright (c) Unifree
# This code is licensed under MIT license (see LICENSE.txt for details)

import logging
import sys
import traceback

import unifree

py_logger = logging.getLogger("lion")


def debug(message: str) -> None:
    if unifree.log_level == "debug":
        print(message, file=sys.stdout)

    py_logger.debug(message)


def info(message: str) -> None:
    if unifree.log_level in ["debug", "info"]:
        print(message, file=sys.stdout)

    py_logger.info(message)


def warn(message: str, exc_info=False) -> None:
    if not unifree.supress_warnings:
        print(message, file=sys.stderr)
        if exc_info:
            traceback.print_exc(file=sys.stderr)

    py_logger.warning(message, exc_info=exc_info)


def error(message: str, exc_info=False) -> None:
    print(message, file=sys.stderr)
    if exc_info:
        traceback.print_exc(file=sys.stderr)

    py_logger.error(message, exc_info=exc_info)


def is_debug():
    return unifree.log_level == 'debug'
