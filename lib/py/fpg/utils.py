"""
Holds general functions used across the system
"""
import datetime
from dotenv import load_dotenv
import os
import pytz
import random
from typing import Any
from lib.py.fpg.constants import (
    Constants,
    Environment

)


def fetch_keys(
        env: Environment
) -> tuple:
    """
    Function to fetch the api keys from the
    path
    :param env: Enviorment object
    :return: tuple -> public key, private key
    """
    # dotenv_path = "config/debug.env" if
    # env == Environment.DEBUG else "config/prod.env" #changed for testing
    if env == Environment.DEBUG:
        dotenv_path = Constants.config_link
    else:
        dotenv_path = Constants.config_link
    load_dotenv(dotenv_path, verbose=True)
    public_key = os.environ.get("PUBLIC_KEY")
    private_key = os.environ.get("PRIVATE_KEY")
    return public_key, private_key


def get_timestamp(
        datetime_object: Any
) -> int:
    """
    :param datetime_object: date we want to convert to epoch
    :return: int since epoch
    """
    return int(datetime_object.replace(
        tzinfo=datetime.timezone.utc).timestamp() * 1000)


def create_datetime_object(
        date_string: str
) -> Any:
    """
    :param date_string: actual date string
    :return: returns datetime object aware in utc
    """
    return pytz.utc.localize(
        datetime.datetime.strptime(
            date_string, '%Y-%m-%d %H:%M:%S'
        )
    )


def get_datetime_from_epoch(
        epoch: int,
        est_time: bool = False
) -> Any:
    """
    :param epoch: int -> second from epoch
    :param est_time: bool -> if the epoch is in est time
    :return: returns datetime object aware in utc
    """
    if epoch != 'nan' and epoch is not None:
        if not est_time:
            return pytz.utc.localize(
                datetime.datetime.fromtimestamp(epoch)
            )
        else:
            orig = datetime.datetime.fromtimestamp(
                epoch, pytz.timezone('America/New_York')
            )
            return orig.astimezone(
                pytz.timezone('UTC')
            )
    return None


def get_epoch_from_datetime(
        datetime_object: Any
) -> float or None:
    """
    :param datetime_object: object in utc
    :return: int -> time since epoch utc
    """
    if datetime_object is not None:
        return datetime.datetime.timestamp(datetime_object)
    else:
        return None


def exchange_open_time_hours_shift(
        open_time: str
) -> Any:
    """
    Returns the exact time needed to shift
    for changing the data to midnight
    :param open_time: str -> "18:00:00"
    :return: returns datetime object specifying how
             the time left until midnight
    """
    split_open_time = open_time.split(':')
    seconds = 60 - int(split_open_time[2])
    if seconds < 60:
        minutes = -1
    else:
        minutes = 0
        seconds = 0
    minutes += 60 - int(split_open_time[1])
    if minutes < 59:
        hours = -1
    else:
        hours = 0
        minutes = 0
    hours += 24 - int(split_open_time[0])
    return datetime.timedelta(hours=hours,
                              minutes=minutes,
                              seconds=seconds)


def generate_id():
    """
    Generates the ID for strategy
    :return: random id
    """
    return str(random.randrange(10000, 100000000))


def set_backtesting_datetime_object(
        date: str
) -> Any:
    """
    :param date: str -> date in the format of our
                        backtesting file
    :return: returns datetime object aware in utc
    """
    a = date.split('+')
    return pytz.utc.localize(
        datetime.datetime.strptime(a[0], '%Y-%m-%d %H:%M:%S')
    )
