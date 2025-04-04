import logging
import os
import pytest
from ocp_scale_utilities.logger import setup_logging

LOG_LEVEL = logging.INFO

pytestmark = [
    pytest.mark.usefixtures("setup_log_queue_listener"),
    pytest.mark.parametrize(
        "setup_log_queue_listener",
        [
            pytest.param(
                {
                    "log_level": LOG_LEVEL,
                    "log_file": "/tmp/test_logger.log",
                },
            ),
            pytest.param(
                {
                    "log_level": LOG_LEVEL,
                },
            ),
        ],
        indirect=True,
    ),
]


@pytest.fixture(scope="module")
def setup_log_queue_listener(request):
    log_file = request.param.get("log_file")
    if log_file and os.path.exists(log_file):
        os.unlink(log_file)
    queue_listener = setup_logging(
        log_level=request.param["log_level"],
        log_file=log_file,
    )
    yield queue_listener, log_file
    if log_file:
        os.unlink(log_file)


@pytest.mark.parametrize(
    "test_params",
    [
        {
            "messages": [
                ("root", logging.INFO, "blah blah blah"),
                ("root", logging.INFO, "blah blah blah"),
                ("root", logging.INFO, "blah blah blah"),
                ("root", logging.INFO, "blah blah blah"),
                ("root", logging.INFO, "blah blah blah"),
                ("root", logging.INFO, "blah blah blah"),
                ("root", logging.INFO, "blah blah blah"),
                ("root", logging.INFO, "blah blah blah"),
                ("root", logging.INFO, "blah blah blah"),
                ("root", logging.INFO, "blah blah blah"),
                ("root", logging.ERROR, "wah wah wah wah"),
                ("root", logging.CRITICAL, "you should hear this"),
                ("basic", logging.WARNING, "hello world"),
                ("basic", logging.WARNING, "hello world"),
                ("basic", logging.WARNING, "hello world"),
            ],
            "caplog_expected": [
                ("root", logging.INFO, "blah blah blah"),
                (
                    "root",
                    logging.ERROR,
                    "wah wah wah wah --- [DuplicateFilter: Last log `blah blah blah` repeated 9 times]",
                ),
                ("root", logging.CRITICAL, "you should hear this"),
            ],
            "file_expected": [
                "root \x1b[32mINFO\x1b[0m blah blah blah",
                "root \x1b[31mERROR\x1b[0m wah wah wah wah --- [DuplicateFilter: Last log `blah blah blah` repeated 9 times]",
                "root \x1b[31m\x1b[47mCRITICAL\x1b[0m you should hear this",
                "hello world",
                "hello world",
                "hello world",
            ],
        },
    ],
)
def test_logger(test_params, setup_log_queue_listener, caplog):
    caplog.clear()
    loggers = {}
    for entry in test_params["messages"]:
        logger_name, log_level, message = entry
        if logger_name in loggers:
            logger = loggers[logger_name]
        else:
            logger = loggers[logger_name] = logging.getLogger(logger_name)
        logger.log(log_level, message)

    queue_listener, log_file = setup_log_queue_listener
    queue_listener.stop()
    for handler in queue_listener.handlers:
        handler.flush()

    assert test_params["caplog_expected"] == caplog.record_tuples

    if log_file:
        with open(log_file, "r") as file:
            log_data = file.readlines()
        for line_number, line in enumerate(test_params["file_expected"]):
            assert line in log_data[line_number]
