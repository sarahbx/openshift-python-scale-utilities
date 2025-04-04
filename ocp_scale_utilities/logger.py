from __future__ import annotations

import logging
from multiprocessing import Queue
from logging import StreamHandler
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from typing import Optional

from simple_logger.logger import WrapperLogFormatter, DuplicateFilter


def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    log_file_max_bytes: int = 2**27,
    log_file_backup_count: int = 10,
) -> QueueListener:
    """
    Setup basic/root logging using QueueHandler/QueueListener
    to consolidate log messages into a single stream to be written to multiple outputs.

    Args:
        log_level (int): log level
        log_file (str, optional): logging output file
        log_file_max_bytes (int, optional): Max bytes per log file before rotation
        log_file_backup_count (int, optional): Max log files to rotate

    Returns:
        QueueListener: Process monitoring the log Queue

    Eg:
       root QueueHandler ┐                         ┌> StreamHandler
                         ├> Queue -> QueueListener ┤
      basic QueueHandler ┘                         └> FileHandler
    """
    basic_log_formatter = logging.Formatter(fmt="%(message)s")
    root_log_formatter = WrapperLogFormatter(
        fmt="%(asctime)s %(name)s %(log_color)s%(levelname)s%(reset)s %(message)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
        secondary_log_colors={},
    )

    log_queue: Queue = Queue(maxsize=-1)
    console_handler = StreamHandler()

    if log_file:
        log_file_handler = RotatingFileHandler(
            filename=log_file, maxBytes=log_file_max_bytes, backupCount=log_file_backup_count
        )
        log_listener = QueueListener(log_queue, log_file_handler, console_handler)
    else:
        log_listener = QueueListener(log_queue, console_handler)

    basic_log_queue_handler = QueueHandler(queue=log_queue)
    basic_log_queue_handler.set_name(name="basic")
    basic_log_queue_handler.setFormatter(fmt=basic_log_formatter)

    basic_logger = logging.getLogger("basic")
    basic_logger.setLevel(level=log_level)
    basic_logger.addHandler(hdlr=basic_log_queue_handler)

    root_log_queue_handler = QueueHandler(queue=log_queue)
    root_log_queue_handler.set_name(name="root")
    root_log_queue_handler.setFormatter(fmt=root_log_formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level=log_level)
    root_logger.addHandler(hdlr=root_log_queue_handler)
    root_logger.addFilter(filter=DuplicateFilter())

    root_logger.propagate = False
    basic_logger.propagate = False

    log_listener.start()
    return log_listener
