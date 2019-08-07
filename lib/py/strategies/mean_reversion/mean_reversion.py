import datetime
import numpy
from typing import Any

from lib.py.fpg.AbstractStrategies import (
    StrategiesAbstract
)
from lib.py.fpg.utils import (
    get_timestamp,
    create_datetime_object,
    generate_id
)


class MeanReversion(StrategiesAbstract):
    """
    """
    def __init__(
            self: Any,
            current_time: Any,
            data_manager: Any,
            pair: str = None
     ) -> None:
        # Mandatory settings:
        # General settings:
        self.data_manager = data_manager
        # Strategy definitions:
        self.strategy_id = generate_id()
        self.strategy_name = 'MeanReversion'
        self.pair = pair
        self.exchange = 'kraken'
        # Strategy time related settings:
        self.exchange_daily_open_time = '13:00:00'
        self.expiration_period = 3
        self.creation_time = current_time
        self.last_exchange_open_time = None
        self.last_price_fetch_time = None
        self.days_passed = 0
        # Strategy execution related settings:
        self.is_leverage = None
        self.current_price = None
        self.is_executed = False
        self.is_expired = False
        self.amount = None
        self.strategy_position = None
        self.live_position = False

        # All other specific strategy related settings:
        self.days_back = 20  # For data fetching
        self.close_df = None
        self.high_band = None
        self.low_band = None
        self.mean_band = None
        self.std = None
        self.passed_high_band_counter = 0
        self.passed_low_band_counter = 0
        # ....
        # ....
        self.initialize()

    def create_dictionary_for_db(
            self: Any
    ) -> dict:
        """
        The data saved in specific columns under the db
        is the mandatory columns specified in the portfolio.
        Please insert here all of the unique strategy related
        settings you would like to save and restore
        :return: dict -> dictionary for db with all of the
                         extra data the user wants to save.
                         The keys must be in the same name as the attributes
                         of the object.
        """
        return {
            'expiration_period': self.expiration_period,
            'is_executed': self.is_executed,
            'exchange': self.exchange
        }

    def calculate_bands(
            self,
            since
    ) -> None:
        self.close_df = self.data_manager.fetch_custom_ohlcv(
            exchange_id=self.exchange,  # Must
            pair=self.pair,  # Must
            exchange_open_time=self.exchange_daily_open_time,  # Must
            since=since,  # Must
            days_back=self.days_back  # Must, will return until the time of the request
        )
        close_numpy_array = self.close_df['c'].to_numpy()
        self.std = numpy.nanstd(close_numpy_array)
        self.mean_band = numpy.nanmean(close_numpy_array)
        self.high_band = self.mean_band + self.std*2
        self.low_band = self.mean_band - self.std*2

    def print_details(
            self: Any
    ) -> Any:
        """
        Will print our strategy object detalis
        Please insert here print statement you would
        like to see when viewing the strategy on the interface
        """
        print(f"Strategy name: {self.strategy_name}")
        print(f"Strategy id: {self.strategy_id}")
        print(f"Strategy Position: {self.strategy_position}")
        print(f"Amount: {self.amount}")
        print(f"Current Price: {self.current_price}")
        print(f"Mean Band: {self.mean_band}")
        print(f"Low Band: {self.low_band}")
        print(f"High Band: {self.high_band}")
        print(f"Creation time: {self.creation_time}")

    def initialize(
            self: Any
    ) -> None:

        """
        This is the first run of the object, put here
        all of the necessary actions to first run each strategy objects
        This will initialize the strategy object.
        - Fetch the price
        - Fetch the days back ohlcv
        - Calculate the boundaries
        :return: None -> changes default class values
        """

        # Fetch current price
        self.current_price = self.data_manager.fetch_mid_price(self.pair)
        # Convert dates for fetching High Low
        str_date_today = self.creation_time.strftime('%Y-%m-%d')
        self.last_exchange_open_time = create_datetime_object(
            str_date_today + ' ' + self.exchange_daily_open_time)
        # not available in backtesting
        if self.data_manager.fetch_current_time() - self.last_exchange_open_time < \
                datetime.timedelta(seconds=-1):
            self.last_exchange_open_time -= datetime.timedelta(days=1)
        data_initialization_datetime_object = \
            self.last_exchange_open_time - \
            datetime.timedelta(days=self.days_back)
        # Fetch high lowse
        self.calculate_bands(
            get_timestamp(
                data_initialization_datetime_object)
        )

    def check_execution(
            self: Any
    ) -> None or dict:
        """
        This will check whether we need to execute what
        If this is an entrance position and you are using the risk
        manager to decide on the amount for investment, please enter
        amount = None
        :return:
        """
        execution_list = []
        if self.live_position:
            if self.mean_band-20 <= \
                    self.current_price <= \
                    self.mean_band+20:
                self.live_position = False
                self.is_expired = True
                execution_dict = {
                    'amount': self.amount,
                    'type': self.strategy_position,
                    'pair': self.pair,
                    'action': 'exit'
                }
                self.strategy_position = None
                execution_list.append(execution_dict)
        elif self.current_price >= self.high_band:
            self.passed_high_band_counter += 1
            if self.passed_high_band_counter >= 60:
                self.strategy_position = 'short'
                execution_dict = {
                    'amount': None,
                    'type': self.strategy_position,
                    'stop_price': self.mean_band,
                    'pair': self.pair,
                    'action': 'enter'
                }
                execution_list.append(execution_dict)
                self.live_position = True
        elif self.current_price <= self.low_band:
            self.passed_low_band_counter += 1
            if self.passed_low_band_counter >= 60:
                self.strategy_position = 'long'
                execution_dict = {
                    'amount': None,
                    'type': self.strategy_position,
                    'stop_price': self.mean_band,
                    'pair': self.pair,
                    'action': 'enter'
                }
                execution_list.append(execution_dict)
                self.live_position = True
        else:
            self.passed_low_band_counter = 0
            self.passed_high_band_counter = 0
        return execution_list

    def check_if_expired(
            self: Any
    ) -> None:
        if self.last_price_fetch_time + \
                datetime.timedelta(minutes=2) - \
                self.last_exchange_open_time >= \
                datetime.timedelta(days=1):
            self.days_passed += 1
            self.last_exchange_open_time += datetime.timedelta(days=1)
            if self.days_passed == \
                    self.expiration_period \
                    or not self.live_position:
                self.is_expired = True

    def refresh(
            self: Any
    ) -> None or dict or str:

        """
        This function handles the entire execution
        process of the object.
        - Fetch the last price
        - Update the last fetch time
        - Check if object expiration period has reached,
          if so, will return:
          * If the object has an open position, it will
            return a dictionary with details for liquidation
          * If the object doesnt have an open position, it
            will return str -> 'remove' which will remove
            the object from the active strategy objects
            from the portfolio to the expired ones
        - If object is still live and running:
          * Will modify the boundaries
          * Will check for execution indicators
            If execution is needed it will return -> dict
            with the necessary values. If nothing is need to
            be done, it will return -> None
        """
        # Fetching current price
        self.last_price_fetch_time = self.data_manager.fetch_current_time()
        self.current_price = self.data_manager.fetch_mid_price(self.pair)
        # Checking if object has reached expiration
        self.check_if_expired()
        if self.is_expired:
            # Is expired = True
            # Checking if the object has open an position
            if self.live_position:
                execution_dict = {
                    'pair': self.pair,
                    'amount': self.amount,
                    'type': self.position,
                    'action': 'exit'
                }
                self.live_position = False
                self.strategy_position = None
                return [execution_dict]
            else:
                # If object hit expiration but doesn't
                # have any open position
                return []

        else:
            # If object didn't hit expiration ->
            # Modify its boundaries and check for
            # execution
            return self.check_execution()
