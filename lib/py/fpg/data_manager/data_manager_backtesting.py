"""
Data Manager class for backtesting
"""
import datetime
import pandas as pd
from typing import Any

from lib.py.fpg.data_manager.data_manager_parent import DataHandlerSuper
from lib.py.fpg.logger import (
    get_module_logger
)
from lib.py.fpg.utils import (
    exchange_open_time_hours_shift,
    set_backtesting_datetime_object,
    get_datetime_from_epoch
)

from lib.py.fpg.constants import (
    Constants
)

logger = get_module_logger('data')


class BacktestingDataManager(DataHandlerSuper):
    def __init__(
            self: Any,
            start_date,
            end_date,
            pairs
    ) -> None:
        super().__init__()
        self.start_date = start_date
        self.current_time = self.start_date
        self.end_date = end_date
        self.general_dfs = {}
        self.ticking_dfs = {}
        self.pairs = pairs
        self.current_index = 0
        self.shifted_general_dfs = {}
        self.minutes = None
        self.initialize_backtesting()

    def initialize_backtesting(
            self: Any
    ) -> None:
        """
        Will initialize backtesting:
        - Import the necessary files
        - Create the time window for backtesting
        - Create the ticking and general DFs
        :return: None -> sets default class values
        """
        for pair in self.pairs:
            print('----------------------------------')
            print(f"- Loading file for pair {pair}")
            file_name = pair.replace('/', '')
            pair_df = pd.read_csv(f'{Constants.data_bundle_link}/{file_name}.csv')
            print(f"- Making modifications (might take up to 1 minute)")
            pair_df['datetime'] = pair_df['datetime'].apply(
                lambda date: set_backtesting_datetime_object(date)
            )
            general_df_start_date = self.start_date - \
                datetime.timedelta(days=50)
            pair_general_df = pair_df[
                (pair_df['datetime'] >= general_df_start_date) &
                (pair_df['datetime'] <= self.end_date)
            ]
            pair_general_df = pair_general_df.copy(deep=True)
            pair_general_df.reset_index()
            self.general_dfs[pair] = pair_general_df
            pair_ticking_df = pair_general_df[
                pair_general_df['datetime'] >= self.start_date]
            pair_ticking_df = pair_ticking_df.copy(deep=True)
            pair_ticking_df.reset_index()
            self.ticking_dfs[pair] = pair_ticking_df
            print("-----Finished processing file-----")
        self.minutes = pair_ticking_df.shape[0]

    def check_end_of_file(
            self: Any
    ) -> bool:
        """
        Will check if we finished the
        backtesting process
        :return: Bool -> finished (True)
        """
        if self.minutes == self.current_index:
            return True
        return False

    def fetch_current_time(
            self: Any
    ) -> Any:
        """
        Returns the current time from the first
        DF in the ticking DFs dictionary.
        Since we are supposed to have same index
        and time throughout all of the DFs, it doesn't matter
        from which one it pulls the date
        :return:
        """
        for pair, df in self.ticking_dfs.items():
            self.current_time = df.iloc[self.current_index]['datetime']
            return self.current_time

    def fetch_mid_price(
            self: Any,
            pair: str
    ) -> float:
        """
        Returns the current price based on the
        pair and current index
        :param pair: str -> pair for current price
        :return: float -> current price
        """
        return self.ticking_dfs[pair].iloc[self.current_index]['price']

    def fetch_custom_ohlcv(
            self: Any,
            exchange_id: str,
            pair: str,
            exchange_open_time: str,
            since: Any,
            days_back: int
    ) -> Any:
        """
        :param exchange_id: Not necessary here
        :param pair: str -> pair trading
        :param exchange_open_time: str -> 18:00:00
        :param since: int -> epoch initial date
        :param days_back: int -> days back to pull date
        :return: pandas DF with the corresponding values of
                 high low
        """
        since = get_datetime_from_epoch(
            since/1000, True) + datetime.timedelta(days=2)
        try:
            general_df = self.shifted_general_dfs[
                pair][exchange_open_time]
        except KeyError:
            time_to_shift = exchange_open_time_hours_shift(
                exchange_open_time
            )
            general_df = self.general_dfs[pair].copy(deep=True)
            general_df['datetime'] = general_df[
                'datetime'].apply(lambda date: date + time_to_shift)
            shifted_dict = {exchange_open_time: general_df}
            self.shifted_general_dfs[pair] = shifted_dict
        to = since + datetime.timedelta(days=days_back)
        while to > self.current_time:
            to -= datetime.timedelta(days=1)
            since -= datetime.timedelta(days=1)
        current_df = general_df[
            (general_df['datetime'] >= since) &
            (general_df['datetime'] <= to)
        ]
        current_df = current_df.copy(deep=True)
        high = current_df.groupby(
            current_df.datetime.dt.date)[['high']].max()
        low = current_df.groupby(
            current_df.datetime.dt.date)[['low']].min()
        opens = current_df.groupby(
            current_df.datetime.dt.date)[['open']].first()
        close = current_df.groupby(
            current_df.datetime.dt.date)[['close']].last()
        volume = current_df.groupby(
            current_df.datetime.dt.date)[['volume']].sum()
        custom_high_low_df = \
            high.join([low, opens, close, volume])
        custom_high_low_df = \
            custom_high_low_df.reset_index()
        custom_high_low_df = \
            custom_high_low_df.sort_values(by='datetime')
        custom_high_low_df = custom_high_low_df.rename(columns={
            'datetime': 'exchange_shift_time',
            'high': 'h',
            'low': 'l',
            'close': 'c',
            'open': 'o',
            'volume': 'v'
        })
        custom_high_low_df['exchange_shift_time'] = \
            custom_high_low_df['exchange_shift_time'].apply(
            lambda date: datetime.datetime.combine(date, datetime.time(0, 0))
        )
        return custom_high_low_df
