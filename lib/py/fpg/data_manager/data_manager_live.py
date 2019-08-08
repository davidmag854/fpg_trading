"""
Actual method that fetches data for the client
"""
import ccxt
import datetime
import pandas as pd
import pytz
from typing import Any

from lib.py.fpg.data_manager.data_manager_parent import (
    DataHandlerSuper
)
from lib.py.fpg.logger import (
    get_module_logger
)
from lib.py.fpg.utils import (
    get_datetime_from_epoch,
    exchange_open_time_hours_shift
)
logger = get_module_logger('data')


class LiveDataManager(DataHandlerSuper):
    def __init__(
            self: Any,
            fpg_connector: Any,
            database: Any
    ) -> None:
        """
        This class will handle the following connections:
        1. Interaction with FPG's api:
            - mid_price - > get current mid price
        2. Connecting to ccxt based on a given exchange
           and fetching ohlcv
        :param fpg_connector: FPG_Connector class object
        """
        super().__init__(fpg_connector, database)

    def fetch_current_time(
            self: Any
    ) -> Any:
        """
        :return: Returns the current time
        """
        self.current_time = pytz.utc.localize(datetime.datetime.utcnow())
        return self.current_time

    def fetch_mid_price(
            self: Any,
            pair: str
    ) -> float:
        """
        :param pair: str -> pair to fetch mid price for
        :return: float -> the current mid price for the pair given
        """
        logger.info(f'fetched mid price for {pair}')
        self.current_price = self.fpg_connector.fetch_price(pair)
        self.database.insert_coin_data(
            pair, self.current_price, self.current_time
        )
        return self.current_price

    def fetch_custom_ohlcv(
            self: Any,
            exchange_id: str,
            pair: str,
            exchange_open_time: str,
            since: Any,
            days_back: int
    ) -> Any:
        """
        This function will fetch the:
        Open, High, Low, Close, Volume
        in a daily aggregation with custom exchange open time.

        :param exchange_id: str -> exchange id
                                to view the exchange id for ccxt
                                print (ccxt.exchanges) or please
                                view the ids under Exchanges:
                                https://github.com/ccxt/ccxt/wiki/Manual
        :param pair:  str -> pair requested, for example: BTC/USD
        :param exchange_open_time: str -> "18:00:00:
        :param since: str -> Unix epoch time in millisecond format,
                             if not specified, will return last 12 hours
        :param days_back: int -> how many days back from today
        :return: returns pandas data frame with the following columns:
                 - 'datetime' - datetime object of day
                 - 'h: high price (float)
                 - 'l': close price (float)
                 The data frame will have daily data based
                 on the exchange open time. The exchange open time
                 specified will be set to midnight (all of the data
                 will shift).
        """
        # Generating exchange object
        exchange_call = getattr(ccxt, exchange_id)
        exchange_object = exchange_call()

        # Calculating how many hours we need to shift
        # the data
        time_to_shift = exchange_open_time_hours_shift(
            exchange_open_time
        )
        # Fetching the high low data
        high_low_data = exchange_object.fetch_ohlcv(
                pair,
                since=since,
                timeframe='1h'
        )
        logger.info(f'fetched ohlcv for '
                    f'{pair} in exchange {exchange_id}')
        high_low_df = pd.DataFrame.from_records(
            high_low_data, columns=["timestamp", "o", "h", "l", "c", "v"])
        high_low_df['exchange_shift_time'] = high_low_df['timestamp'].apply(
            lambda time: (
                    get_datetime_from_epoch(time/1000, True) + time_to_shift)
        )
        # high_low_df['exchange_shift_time'] = high_low_df['datetime'].apply(
        #     lambda date: date + time_to_shift
        # )
        high = high_low_df.groupby(
            high_low_df.exchange_shift_time.dt.date)[['h']].max()
        low = high_low_df.groupby(
            high_low_df.exchange_shift_time.dt.date)[['l']].min()
        opens = high_low_df.groupby(
            high_low_df.exchange_shift_time.dt.date)[['o']].first()
        close = high_low_df.groupby(
            high_low_df.exchange_shift_time.dt.date)[['c']].last()
        volume = high_low_df.groupby(
            high_low_df.exchange_shift_time.dt.date)[['v']].sum()
        custom_high_low_df = high.join([low, opens, close, volume])
        custom_high_low_df = custom_high_low_df.reset_index()
        custom_high_low_df = custom_high_low_df.sort_values(
            by='exchange_shift_time')
        custom_high_low_df['exchange_shift_time'] = \
            custom_high_low_df['exchange_shift_time'].apply(
            lambda date: datetime.datetime.combine(
                date, datetime.time(0, 0))
        )
        return custom_high_low_df

    def fetch_balance(
            self: Any,
            coins: list
    ) -> dict:
        """
        Will return the FPG's account balance in every coin
        :param coins: list of coins trading for example ['BTC','ETH']
        :return: dict -> balance in every coin.
                         keys: str -> coin name
                         value: float -> amount in balance

                         additional key named 'succeeded' will return and will
                         indicate if the request was successful
        """
        logger.info("fetching balance for account")
        balance = self.fpg_connector.fetch_balance(coins)
        return balance

    def fetch_orderbook(
            self: Any,
            pair: str
    ) -> dict:
        """
        This will fetch the most current order book
        from FPG's endpoint.
        :param pair: str -> orderbook pair
        :return: dictionary -> keys (str): 'asks', 'bids
                               values (list): ordered list of price
                                              and amount
        """
        logger.info(f'fetched orderbook for {pair}')
        return self.fpg_connector.fetch_orderbook(pair)
