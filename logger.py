"""
Utility logger to write structured logs in Cloud Logging

Usage:

import logger

logger.debug('test debug')
logger.info('test info')
logger.warning('test warning')
logger.error('test error')
try:
    this_is_an_error
except Exception as exc:
    logger.exception('test exception')

logger.info("Process completed", {"records_updated": 1984, "records_failed": 42})
"""

import json
import os
import traceback


LEVELS: dict = {"ERROR": 40, "WARNING": 30, "INFO": 20, "DEBUG": 10}
MINIMUM_LOGGING_LEVEL: int = LEVELS.get(
    os.environ.get("LOGGING_LEVEL", "DEBUG"), LEVELS["DEBUG"]
)


def debug(message: str, extra: dict = None) -> None:
    """
    Log a message with severity 'DEBUG'

    :param message: Message to be logged
    :param extra:  Extra params to write in the log as JSON payload
    """
    _log_json_message(message, extra, "DEBUG")


def info(message: str, extra: dict = None) -> None:
    """
    Log a message with severity 'INFO'

    :param message: Message to be logged
    :param extra:  Extra params to write in the log as JSON payload
    """
    _log_json_message(message, extra, "INFO")


def warning(message: str, extra: dict = None) -> None:
    """
    Log a message with severity 'WARNING'

    :param message: Message to be logged
    :param extra:  Extra params to write in the log as JSON payload
    """
    _log_json_message(message, extra, "WARNING")


def error(message: str, extra: dict = None) -> None:
    """
    Log a message with severity 'ERROR'

    :param message: Message to be logged
    :param extra:  Extra params to write in the log as JSON payload
    """
    _log_json_message(message, extra, "ERROR")


def exception(message: str, extra: dict = None) -> None:
    """
    Log a message with severity 'ERROR' and stacktrace

    Including @type the exception is also shown in Error Reporting
    https://cloud.google.com/error-reporting/docs/formatting-error-messages

    :param message: Message to be logged
    :param extra:  Extra params to write in the log as JSON payload
    """
    exception_info: dict = {
        "exception": traceback.format_exc(),
        "@type": "type.googleapis.com/google.devtools.clouderrorreporting.v1beta1.ReportedErrorEvent",
    }
    if extra:
        exception_info.update(extra)
    _log_json_message(message, exception_info, "ERROR")


def _log_json_message(message: str, extra: dict = None, severity: str = "INFO") -> None:
    """
    Python logger doesn't allow structured logging
    https://github.com/googleapis/python-logging/issues/13

    Using print because Google cloud logging library does an API call and it's slower than print

    Test writing 100 entries from a Cloud Function:
        Cloud logging : 7.1 secs.
        Python logging: 4.7 msecs
        Print         : 1.2 msecs

    :param message: Message to be logged
    :param extra:  Extra params to write in the log as JSON payload
    :param severity: Log level
    """
    if LEVELS.get(severity, LEVELS["DEBUG"]) >= MINIMUM_LOGGING_LEVEL:
        log_entry: dict = {"message": message, "severity": severity}
        if extra:
            log_entry.update(extra)
        print(json.dumps(log_entry))
