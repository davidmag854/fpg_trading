from enum import Enum, IntEnum


class Environment(IntEnum):
    DEBUG = 0
    PROD = 1


class Constants:

    backtesting_results = "data/backtesting_results"
    config_link = "data/config/debug.env"
    data_bundle_link = "data/data_bundles"
    database_link = "data/database/user_database.db"
    endpoint_link = "https://testing.api.floating.group/v0"
    realtime_results = "data/strategies_csv"
