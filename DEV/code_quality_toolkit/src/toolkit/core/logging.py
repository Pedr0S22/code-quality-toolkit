"""Simple structured logging utilities."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

SEND_LOGS_TO_TERMINAL = False  # appends logs to a log file

"""
Set up and configures a Python logger named "toolkit" using the standard logging library.
Its main purpose is to ensure the application has a working logger with a clean output format, 
avoiding the common issue of adding duplicate handlers if the code is executed multiple times
(e.g., during testing or module reloading).
"""
_LOGGER = logging.getLogger("toolkit")  # retrieves a logger instance named "toolkit".
# If a logger with this name already exists
# (e.g., if the module was previously imported), it returns
# the existing instance. If not, it creates a new one
# checks if the logger already has any handlers attached. Without this check, every time the module is imported,
# a new handler would be attached, resulting in every log message being printed multiple times to the console.
if not _LOGGER.handlers:
    # executes only if no handlers are currently attached
    if SEND_LOGS_TO_TERMINAL:
        handler = (
            logging.StreamHandler()
        )  # StreamHandler sends log messages to the standard output stream.
    else:
        log_file_path = "toolkit.log"
        handler = logging.FileHandler(
            log_file_path
        )  # Note: APPENDS the log messages to the log file.

    formatter = logging.Formatter(
        "%(message)s"
    )  # ensure that only the message content of the log record is printed,
    handler.setFormatter(
        formatter
    )  # applies the clean formatter to the console handler,
    _LOGGER.addHandler(handler)  # ...and attaches the configured handler to the logger.

# Only messages logged at the INFO level or higher (INFO, WARNING, ERROR, CRITICAL) will be passed to the handler
# and displayed. Messages logged at the DEBUG level will be ignored.
_LOGGER.setLevel(logging.INFO)


def log(event: str, **payload: Any) -> None:
    """
    This function is a simple wrapper around the standard Python logging mechanism designed to emit
    structured log entries in JSON format.

    -   'event:str' is a unique identifier for the type of activity or situation being logged
        (e.g., "plugin.loaded", "cli.error", "engine.files_discovered").
    -   '**payload:Any' captures any number of additional keyword arguments passed to the function.
    These arguments form the "payload," containing the information relevant to the event
    (e.g., count=10, plugin="StyleChecker").
    """

    # A dictionary named record is initialized, and is immediately populated with the required "event" field.
    # The special syntax **payload is used to unpack all the remaining keyword arguments directly into
    # the record dictionary.
    record: Dict[str, Any] = {"event": event, **payload}

    # json.dumps converts the entire Python dictionary (record) into a single JSON formatted string.
    # _LOGGER.info(...) sends the resulting JSON string as the message to the logger (thus print to the console)
    _LOGGER.info(json.dumps(record, ensure_ascii=False))
