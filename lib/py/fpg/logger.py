from time import gmtime

import logging
import os

from lib.py.fpg.constants import Environment


PACKAGE_NAME = 'asp'
LOGGING_FORMAT = (
    '[%(asctime)s]{optional_header}[%(levelname)s][%(filename)s]'
    '[%(threadName)s][%(funcName)s][%(lineno)d]: %(message)s'
)


def _setup_logger(
        logger: logging.Logger,
        env: Environment,
        optional_header: str,
        file_name=None,
) -> None:
    if env == Environment.PROD:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        LOGGING_FORMAT.format(optional_header=optional_header)
    )
    formatter.converter = gmtime  # type: ignore

    streamhandler = logging.StreamHandler()
    if env == Environment.PROD:
        streamhandler.setLevel(logging.INFO)
    else:
        streamhandler.setLevel(logging.DEBUG)
    streamhandler.setFormatter(formatter)
    logger.addHandler(streamhandler)

    if file_name:
        os.makedirs('logs/', exist_ok=True)
        filehandler = logging.FileHandler(
            f'logs/{file_name}.log')
        filehandler.setLevel(logging.INFO)
        filehandler.setFormatter(formatter)
        logger.addHandler(filehandler)


def setup_service_logger(
        service_name: str,
        env: Environment,
        optional_header: str = '',
        to_file: bool = False
) -> logging.Logger:
    """Set up and return a logger for this service."""
    logger = logging.getLogger(PACKAGE_NAME)
    if to_file:
        file_name = service_name
    else:
        None
    _setup_logger(logger, env, optional_header, file_name)
    return logger


def get_module_logger(module_name: str) -> logging.Logger:
    """Return a logger for the given module_name."""
    logger = logging.getLogger(f'{PACKAGE_NAME}.{module_name}')
    return logger
