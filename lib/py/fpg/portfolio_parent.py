"""
Module that contains all of the functions
necessary to run trading
"""
import copy
import datetime
import json
import pandas as pd
from typing import Any
import time
import traceback
from lib.py.fpg.constants import (
    Constants
)
from lib.py.fpg.database import (
    Database
)
from lib.py.fpg.data_manager.data_manager_backtesting import (
    BacktestingDataManager
)
from lib.py.fpg.data_manager.data_manager_live import (
    LiveDataManager
)
from lib.py.fpg.logger import (
    get_module_logger
)
from user_managment.risk_manager import (
    RiskManager
)
from lib.py.fpg.utils import (
    get_datetime_from_epoch,
    generate_id,
    get_epoch_from_datetime
)

from lib.py.fpg.utils import (
    get_datetime_from_epoch
)

from user_managment.risk_manager import (
    RiskManager
)

logger = get_module_logger('portfolio')


class Portfolio:
    def __init__(
            self: Any
    ) -> None:
        self.database = Database()
        self.trader = None
        self.data_manager = None
        self.risk_manager = None
        self.current_time = None

        # Start and stop trading
        self.Trade = False
        self.backtesting_mode = False
        self.backtesting_index = 0
        self.portfolio_money = {}
        self.advanced_settings_counter = None
        self.strategy_dictionary = None  # Might cause a problem
        self.coins = set()
        self.pairs = set()
        self.active_strategy_objects = {}
        self.executed_strategy_ids = set()

    def setup_live_trading(
            self: Any,
            trader
    ) -> None:
        """
        Will setup methods for live trading
        :param trader:
        :return: None -> sets default values
        """
        self.Trade = True
        self.database.initialize_database()
        self.trader = trader
        self.data_manager = \
            LiveDataManager(self.trader.fpg_connector, self.database)
        self.risk_manager = \
            RiskManager(self.data_manager)
        self.current_time = self.data_manager.current_time

    def setup_backtesting(
            self: Any,
            start_date: Any,
            end_date: Any,
            backtesting_name: str
    ) -> None:
        """
        Will setup methods for backtesting
        :param start_date: datetime object -> start date for backtesting
        :param end_date: datetime object -> end date for backtesting
        :param backtesting_name: str -> name of the current backtesting
        :return: None -> sets default class values
        """
        self.backtesting_mode = True
        self.database.initialize_database(name=backtesting_name)
        # Setup all backtesting related stuff
        self.data_manager = \
            BacktestingDataManager(start_date, end_date, self.pairs)
        self.risk_manager = \
            RiskManager(self.data_manager)
        self.current_time = self.data_manager.current_time

    def ticking_thread(
            self: Any
    ) -> None:
        """
        This will create a thread for the ticking to run on the background
        :return: None -> will run the ticker
        """
        while self.Trade:
            try:
                self.tick()
            except:
                logger.error("Error; caught and moving on")
                traceback.print_exc()
                time.sleep(10)
                self.trader.connect()
                self.data_manager.fpg_connector = \
                    self.trader.fpg_connector
                logger.info("Remade trader and restarted.")
            time.sleep(self.tick_time)
        print("shutting trader")

    def add_pairs_to_coins_portfolio(
            self: Any
    ) -> None:
        """
        Will receieve a pair trading and will add the coins
        to the portfolio
        :param pair: str -> pair trading
        :return: None -> changes default values
        """
        for strategy_name, strategy_settings in \
                self.strategy_dictionary.items():
            for pair in strategy_settings['pairs']:
                self.pairs.add(pair)
                split_pair = pair.split("/")
                for coin in split_pair:
                    self.coins.add(coin)

    def create_liquidation_dict(
            self: Any,
            strategy_object
    ) -> dict:
        """
        If we have open position, this will
        create a liquidation dict to exit the position
        :param strategy_object:
        :return: dict -> execution dict with the corresponding
                         values for liquidation
        """
        execution_dict = {
            'pair': strategy_object.pair,
            'type': strategy_object.strategy_position,
            'amount': strategy_object.amount,
            'action': 'exit',
            'leverage': 1
        }
        if strategy_object.strategy_position == 'short':
            strategy_object.short_liquidation_time = \
                self.data_manager.fetch_current_time()
        elif strategy_object.strategy_position == 'long':
            strategy_object.long_liquidation_time = \
                self.data_manager.fetch_current_time()
        return execution_dict

    def parse_response_and_execute_backtesting(
            self: Any,
            action: dict,
            strategy_object: Any
    ) -> None:
        action['trade_id'] = generate_id()
        if action['action'] == 'enter':
            action['leverage'] = self.leverage
            execution_price = \
                self.risk_manager.calculate_transaction_amount(
                    pair=action['pair'],
                    stop_price=action['stop_price'],
                    current_aum=self.portfolio_money
                )
            self.portfolio_money[execution_price[1]] -= \
                execution_price[2]
            action['amount'] = execution_price[0]
            action['price'] = self.data_manager.fetch_mid_price(action['pair'])
            if action['type'] == 'short':
                strategy_object.short_entrance_price = action['price']
            elif action['type'] == 'long':
                strategy_object.long_entrance_price = action['price']
            strategy_object.amount = action['amount']
            strategy_object.is_leverage = action['leverage']
        elif action['action'] == 'exit':
            action['price'] = \
                self.data_manager.fetch_mid_price(action['pair'])
            if action['type'] == 'short':
                strategy_object.short_exit_price = action['price']
            elif action['type'] == 'long':
                strategy_object.long_exit_price = action['price']
            quote = action['pair'].split("/")[1]
            self.portfolio_money[quote] += \
                action['price'] * action['amount']
        self.database.save_trade(
            action,
            self.portfolio_money
        )

    def parse_response_and_execute(
            self,
            response: list,
            strategy_object: Any
    ) -> None:
        """
        Input a list of executions for one strategy
        goes through each of the execution resquests and
        executes them and saves the details in the object
        :param response: list of executions, each execution
                         contains:
                         type -> short/ long
                         action -> enter/ exit
                         amount -> if None, risk manager will handle
                         leverage -> if is set in portfolio level
                         stop_price -> if entering
        :param strategy_object: strategy object the execution is for
        :return: None
        """
        for action in response:
            action['trade_time'] = get_epoch_from_datetime(
                self.data_manager.fetch_current_time()
            )
            action['strategy_id'] = strategy_object.strategy_id
            action['strategy_name'] = strategy_object.strategy_name
            if not self.backtesting_mode:
                if action['action'] == 'enter':
                    execution_amount = \
                        self.risk_manager.calculate_transaction_amount(
                            pair=action['pair'],
                            stop_price=action['stop_price']
                        )
                    action['amount'] = execution_amount[0]
                    action['leverage'] = self.leverage
                    if action['type'] == 'short':  # Enter Short
                        action['side'] = 'sell'
                        execution_response = self.execute_trade(action)
                        strategy_object.short_entrance_price = \
                            execution_response['price']
                    elif action['type'] == 'long':  # Enter Long
                        action['side'] = 'buy'
                        execution_response = self.execute_trade(action)
                        strategy_object.long_entrance_price = \
                            execution_response['price']
                    strategy_object.amount = execution_response['amount']
                    strategy_object.is_leverage = execution_response['leverage']
                elif action['action'] == 'exit':
                    if action['type'] == 'short':  # Exit Short
                        action['side'] = 'buy'
                        execution_response = self.execute_trade(action)
                        strategy_object.short_exit_price = execution_response['price']
                    elif action['type'] == 'long':  # Exit Long
                        action['side'] = 'sell'
                        execution_response = self.execute_trade(action)
                        strategy_object.long_exit_price = execution_response['price']
                # Saving trade to DB
                self.database.save_trade(
                    execution_response,
                    self.data_manager.fetch_balance(self.coins)
                )
            elif self.backtesting_mode:
                self.parse_response_and_execute_backtesting(
                    action,
                    strategy_object
                )

    def execute_trade(
            self: Any,
            execution_dict: dict
    ) -> list:
        """
        Will connect to FPG's endpoint and will execute
        the trade
        :param execution_dict: dictionary containing the following:
                               'pair': str -> pair traded
                               'amount': float -> amount traded
                               'side': str -> 'sell'/ 'buy'
        :return: float -> the price the trade was executed for
        """
        pair = execution_dict['pair']
        side = execution_dict['side']
        amount = execution_dict['amount']
        leverage = execution_dict['leverage']
        execution_response = self.trader.trade(
            pair,
            amount,
            side,
            leverage
        )
        execution_dict['price'] = execution_response[0]
        execution_dict['trade_id'] = execution_response[1]
        return execution_dict

    def create_new_strategy_object(
            self: Any,
            strategy_name: str,
            pair: str,
            current_time=None
    ) -> Any:
        """
        Will return a new strategy object based on the strategy name
        :param pair: str -> the pair we want the strategy
                            to run on
        :param strategy_name: str -> strategy name
        :param creation_time: datetime object -> if we restoring
                              old objects
        :return: new strategy class object
        """
        if current_time is None:
            self.current_time = \
                self.data_manager.fetch_current_time()
            current_time = self.current_time
        return self.strategy_dictionary[strategy_name][
            'object'](current_time,
                      self.data_manager,
                      pair)

    def create_advanced_settings_counter(
            self: Any,
            strategy_dictionary: dict
    ) -> None:
        """
        Will create a clean dictionary just for
        counting the number of short/ long
        :param strategy_dictionary: the orig strategy dictionary
                                    in the the portfolio
        :return: None -> sets the advanced settings counter
        """
        advanced_settings_counter = {}
        for strategy_name, strategy_settings in \
                strategy_dictionary.items():
            if strategy_settings['advanced_settings']:
                strategy_dict = {}
                for pair in strategy_settings['pairs']:
                    strategy_dict[pair] = {
                        'long': 0,
                        'short': 0
                    }
                advanced_settings_counter[
                    strategy_name] = strategy_dict
        self.advanced_settings_counter = \
            advanced_settings_counter

    def restore_strategy_objects(
            self: Any,
            live_strategies: list
    ) -> list or None:
        """
        Will receive the query from the database,
        if the query is not empty, it will run through the
        rows and will create the objects, then it will send the
        new objects to set their old values.
        :param live_strategies: sqlite3 query
        :return: list of restores strategy objects or
                 None if there is nothing to restore
        """
        if live_strategies is not None:
            old_objects = []
            for old_strategy_object_settings in live_strategies:
                strategy_name = \
                    old_strategy_object_settings['strategy_name']
                strategy_pair = \
                    old_strategy_object_settings['pair']
                strategy_creation = get_datetime_from_epoch(
                            old_strategy_object_settings['creation_time'],
                            est_time=True
                )
                old_object = self.create_new_strategy_object(
                        strategy_name,
                        strategy_pair,
                        strategy_creation
                    )
                self.set_strategy_old_values(
                    old_object, old_strategy_object_settings
                )
                old_objects.append(old_object)
            return old_objects
        return None

    def check_if_allowed_to_create_position(
            self,
            position: str,
            strategy_name: str,
            pair: str
    ) -> bool:
        """
        Will receive position, pair and strategy name
        and will return True or False based on the current
        number of short/ long allowed
        :param position: str -> short/ long
        :param strategy_name: str -> strategy name, same as the
                                     strategy dictionary under portfolio
        :param pair: str -> pair trading 'BTC/USD' and etc.
        :return: True/ False
        """
        if self.strategy_dictionary[strategy_name][
            position]['current_' + position][pair] < \
                self.strategy_dictionary[strategy_name][position][
                    'max_' + position + '_per_pair']:
            return True
        return False

    def create_mandatory_fields_dictionary(
            self: Any,
            strategy_settings: Any
    ) -> dict:
        """
        Will the mandatory fields list from the
        portfolio and will create a dictionary for these
        values from the sqlite3 query row
        :param strategy_settings: sqlite3 query row
        :return: dict -> values of the mandatory fields old
                         object
        """
        settings_dictionary = {}
        for mandatory_field in self.mandatory_fields:
            if strategy_settings[mandatory_field] == '0':
                settings_dictionary[mandatory_field] = False
            elif strategy_settings[mandatory_field] == '1':
                settings_dictionary[mandatory_field] = True
            else:
                settings_dictionary[mandatory_field] = \
                    strategy_settings[mandatory_field]
        return settings_dictionary

    def set_strategy_old_values(
            self: Any,
            strategy_object: Any,
            strategy_settings: dict
    ) -> None:
        """
        Will receive the data from the db for
        an old object and will restore its settings
        to a new object
        :param strategy_object: new object
        :param strategy_settings: old object's setting
        :return: None -> changes the strategy object itself
        """
        user_settings = json.loads(
            strategy_settings[
                'additional_user_settings'])
        all_settings = \
            self.create_mandatory_fields_dictionary(strategy_settings)
        all_settings.update(user_settings)
        for settings_name, settings_value in all_settings.items():
            if "time" in settings_name and \
                    settings_value is not None:
                settings_value = get_datetime_from_epoch(
                    int(settings_value),
                    est_time=True)
            setattr(strategy_object, settings_name,
                    settings_value)

    def liquidate(
            self,
            id: str = None,
            strategy_object: Any = None,
            liquidate_all=False
    ) -> None:

        """
        Will liquidate based on the following conditions:
         - If id is passed -> find the id and liquidate if
                              object is not expired and executed
         - If strategy object is passed -> will liquidate if
                              object is not expired and executed
         - If liquidate_all True is passed -> will liquidate all current
                              executed positions which are not
                              expired

        :param strategy_object: default -> None
                                executed strategy object
        :param id: default -> None
                              pass the str id of the strategy object
        :param liquidate_all: default -> False
                              pass True to liquidate all objects
        :return: None -> will liquidate positions
        """
        if not liquidate_all:
            if id is not None:
                try:
                    strategy_object = self.active_strategy_objects[id]
                except KeyError:
                    print("Response: Strategy not found")
            if strategy_object.strategy_position is None:
                print("Strategy is not executed ->"
                      "Nothing to liquidate")
                answer = input("Do you want to remove to object?\n"
                               "Enter y/n:")
                if answer == 'y':
                    strategy_object.is_expired = True
                    try:
                        del self.active_strategy_objects[
                            strategy_object.strategy_id]
                    except KeyError:
                        pass
                    self.database.update_strategy(
                        strategy_object)

            else:
                self.parse_response_and_execute(
                    [self.create_liquidation_dict(strategy_object)],
                    strategy_object
                )
                try:
                    del self.active_strategy_objects[id]
                except KeyError:
                    pass
                self.database.update_strategy(strategy_object)
        elif liquidate_all:
            print("This operation will close all positions\n"
                  "Do you want to  continue?")
            answer = input("Enter y/n: ")
            if answer == 'y':
                for strategy_id, strategy_object in \
                        self.active_strategy_objects.items():
                    strategy_object.is_expired = True
                    if strategy_object.strategy_position is not None:
                        response = [self.create_liquidation_dict
                                    (strategy_object)]
                        self.parse_response_and_execute(
                            response, strategy_object)
                    self.database.update_strategy(
                        strategy_object)
                self.active_strategy_objects = {}

    def check_strategy_current_short_long_positions(
            self: Any
    ) -> None:
        """
        Will go through all of our active and executed objects
        and will check how many long/ short position we are
        currently running. Then it will update the settings
        for the current number of long/ short.
        Since we have limitations on number of long/ short allowed
        at a time, we have to check this process.
        :return: None
        """
        # Initiate counters
        if self.advanced_settings_counter is None:
            self.create_advanced_settings_counter(
                self.strategy_dictionary
            )
        advanced_settings_counter = copy.deepcopy(
            self.advanced_settings_counter
        )
        for strategy_object in \
                self.active_strategy_objects.values():
            if strategy_object.strategy_name in \
                    advanced_settings_counter:
                if strategy_object.strategy_position == 'long' \
                        or strategy_object.long_allowed:
                    advanced_settings_counter[
                        strategy_object.strategy_name][
                        strategy_object.pair][
                        'long'] += 1
                if strategy_object.strategy_position == 'short' \
                        or strategy_object.short_allowed:
                    advanced_settings_counter[
                        strategy_object.strategy_name][
                        strategy_object.pair][
                        'short'] += 1
        for strategy_name, strategy_counter in \
                advanced_settings_counter.items():
            for pair, counter in strategy_counter.items():
                self.strategy_dictionary[strategy_name][
                    'short']['current_short'][pair] = counter['short']
                self.strategy_dictionary[strategy_name][
                    'long']['current_long'][pair] = counter['long']

    def advanced_settings_strategies_creator(
            self: Any,
            strategy_name: str,
            strategy_settings: dict
    ) -> None:
        """
        This will check the settings of the input strategy
        if short/ long is still allowed, it will create
        an object and add it to the active dictionary
        :param strategy_name: str -> The name of the strategy
        :param strategy_settings: dict -> The settings of the strategy
        :return: None -> creates new objects
        """
        for pair in strategy_settings['pairs']:
            # if not maxed_out:
            self.check_strategy_current_short_long_positions()
            short = self.check_if_allowed_to_create_position(
                'short',
                strategy_name,
                pair
            )
            long = self.check_if_allowed_to_create_position(
                'long',
                strategy_name,
                pair
            )
            if short or long:
                new_object = self.create_new_strategy_object(
                    strategy_name,
                    pair
                )
                new_object.short_allowed = short
                new_object.long_allowed = long
                self.active_strategy_objects[
                    new_object.strategy_id] = new_object
                self.database.insert_new_strategy(new_object)
                self.strategy_dictionary[
                    strategy_name]['last_object_created_time'] = \
                    new_object.last_exchange_open_time

    def regular_strategies_creator(
            self: Any,
            strategy_name: str,
            strategy_settings: dict
    ) -> None:
        """
        If the strategy has no advanced settings,
        once we reached the creation interval, we are
        just creating a new object and adding it to the
        active dictionary
        :param strategy_name: str -> The name of the strategy
        :param strategy_settings: dict -> The settings of the strategy
        :return: None -> creates new objects
        """
        for pair in strategy_settings['pairs']:
            new_object = self.create_new_strategy_object(
                strategy_name,
                pair
            )
            self.active_strategy_objects[
                new_object.strategy_id] = new_object
            self.database.insert_new_strategy(new_object)
            self.strategy_dictionary[strategy_name][
                'last_object_created_time'] = \
                new_object.last_exchange_open_time

    def check_for_new_object_creation(
            self: Any,
            initial=False
    ) -> None:
        """
        This will loop through the strategy dictionary
        for every object that is active,
        it will check if we need a new object based on
        the strategy creation interval
        If we have any advanced settings, such as max short/ long
        it will check for their specifications as well
        :return: None -> changes default class variables
        """
        for strategy_name, strategy_settings in \
                self.strategy_dictionary.items():
            # We want to give two minutes break between each day
            if strategy_settings['active']:
                # If it is first run we can't use last object
                # created time that's why we have to write
                # this twice
                if initial:
                    # for pair in strategy_settings['pairs']:
                    #     self.add_pair_to_coins_portfolio(pair)
                    if strategy_settings['advanced_settings']:
                        self.advanced_settings_strategies_creator(
                            strategy_name,
                            strategy_settings)
                    else:
                        self.regular_strategies_creator(
                            strategy_name,
                            strategy_settings)
                elif self.current_time - datetime.timedelta(minutes=2) - \
                        strategy_settings['last_object_created_time'] >= \
                        strategy_settings['creation_interval']:
                    # Will create based on exchange time
                    strategy_settings['last_object_created_time'] += \
                        strategy_settings['creation_interval']
                    if strategy_settings['advanced_settings']:
                        self.advanced_settings_strategies_creator(
                            strategy_name,
                            strategy_settings)
                    else:
                        self.regular_strategies_creator(
                            strategy_name,
                            strategy_settings)

    def export_trades(
            self,
            backtesting: bool = True
    ) -> None:
        general_df = pd.DataFrame()
        trades = self.database.retrieve_all_trades()
        for trade in trades:
            trade_dict = {}
            for column in self.database.trade_history_columns:
                value = trade[column]
                if column == 'trade_time':
                    value = get_datetime_from_epoch(int(value), True)
                elif column == 'portfolio_balance':
                    value = json.loads(value)
                trade_dict[column] = value
            general_df = general_df.append(trade_dict, ignore_index=True)
        if backtesting:
            file_name = f"{Constants.backtesting_results}/{self.database.strategy_objects_table}_trades.csv"
        else:
            file_name = f"{Constants.realtime_results}/{self.database.strategy_objects_table}_trades.csv"
        save = general_df.to_csv(file_name)

    def export_strategies(
            self: Any,
            backtesting: bool = True
    ) -> None:
        """
        Will quesry the db for all of the strategies
        ever created in the current running table
        and will export all to csv with the same name as the
        table
        saves results backtesting results dir
        :return:
        """
        general_df = pd.DataFrame()
        strategies = self.database.retrieve_all_objects()
        for strategy_settings in strategies:
            user_settings = json.loads(
                strategy_settings[
                    'additional_user_settings'])
            all_settings = \
                self.create_mandatory_fields_dictionary(strategy_settings)
            all_settings.update(user_settings)
            for settings_name, settings_value in all_settings.items():
                if "time" in settings_name and settings_value is not None:
                    settings_value = \
                        get_datetime_from_epoch(int(settings_value), True)
                    all_settings[settings_name] = settings_value
            general_df = general_df.append(all_settings, ignore_index=True)
        if backtesting:
            file_name = f"{Constants.backtesting_results}/{self.database.strategy_objects_table}.csv"
        else:
            file_name = f"{Constants.realtime_results}/{self.database.strategy_objects_table}.csv"
        save = general_df.to_csv(file_name)
