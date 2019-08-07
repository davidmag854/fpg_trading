"""
Interface: manages all of the commands
from the user
"""
import threading
from typing import Any
from lib.py.fpg.initialization import (
    initialize_portfolio,
    initialize_trader
)
from lib.py.fpg.logger import (
    get_module_logger
)
from lib.py.fpg.utils import (
    create_datetime_object
)
logger = get_module_logger('interface')


class Interface:
    def __init__(self):
        self.trader = None
        self.portfolio = None
        self.start_trading_system_screen()

    def start_trading_system_screen(
            self:Any
    ) -> None:
        """
               This the first screen shown once the trader starts
               The following options are available:
               1. New trading -> will pull all not expired objects
                                 from the database. If there are any
                                 not expired objects, it will restore them until
                                 the point where it reached max objects from the
                                 strategy settings. If there are any live positions,
                                 it will ask the user for decision.
               2. Backtesting -> the user will have to provide a data file
                                 with historical data and it will run the portfolio
                                 for him.
        """
        print("Portfolio Manager System")
        print("------------------------")
        self.portfolio = initialize_portfolio()
        passed_first_screen = False
        while not passed_first_screen:
            arg = int(input("Please choose from the following:\n"
                            "1. For new trading enter 1\n"
                            "2. For back testing enter 2\n\n"
                            "Please enter: "))
            print("------------------------\n")
            if arg == 1:
                # We will initiate the live trading system
                passed_first_screen = True
                self.initiate_live_trading_screen()
            elif arg == 2:
                # We will initiate the backtesting system
                passed_first_screen = True
                self.initiate_backtesting_screen()

    def initiate_live_trading_screen(
            self: Any
    ) -> None:
        """
        - Initialize Trader
        - Setup portfolio for live trading
        - Restore old object from old trading sessions
        - Ask the user whether restore or not restore each
          old object
        - Initialize trading
        - Run the threads: ticking and information
        """
        self.trader = initialize_trader()
        self.portfolio.setup_live_trading(self.trader)
        self.restore_old_objects()
        self.portfolio.initialize_trading()
        self.initialize_threads()

    def initiate_backtesting_screen(
            self: Any
    ) -> None:
        """
        - Input:
                - Start date
                - End date
                - Backtesting Name
                - Portfolio amount for each pair
        - Setup portfolio for backtesting
        - Run backtesting
        :return:
        """
        passed_first_backtesting_screen = False
        while not passed_first_backtesting_screen:
            print("Please input start date for "
                  "backtesting (UTC time),\n"
                  "in the following format:"
                  " yyyy-mm-dd hh:mm:ss\n"
                  "Earliest date possible is "
                  "2017-01-01 00:00:00\n"
                  "For the above date enter 0")
            start_date = input("Start Date: ")
            if start_date == '0':
                start_date = '2017-01-01 00:00:00'
            try:
                start_date = create_datetime_object(start_date)
                passed_first_backtesting_screen = True
            except:
                print("You inserted incorrect format, "
                      "please try again")
        passed_second_backtesting_screen = False
        while not passed_second_backtesting_screen:
            print("Please input end date for "
                  "backtesting (UTC time),\n"
                  "in the following format: "
                  "yyyy-mm-dd hh:mm:ss\n"
                  "Latest date possible is "
                  "2019-07-01 00:00:00\n"
                  "For the above date enter 0")
            end_date = input("End Date: ")
            if end_date == '0':
                end_date = '2019-07-01 00:00:00'
            try:
                end_date = create_datetime_object(end_date)
                passed_second_backtesting_screen = True
            except:
                print("You inserted incorrect format, "
                      "please try again")
        # Third screen
        backtesting_name = input("Please input "
                                 "backtesting name: ")
        # Fourth screen
        for pair in self.portfolio.pairs:
            quote = pair.split("/")[1]
            amount = input(f"Please input initial "
                           f"amount for quote in {quote}: ")
            self.portfolio.portfolio_money[quote] = float(amount)
        # Initialize backtesting
        self.portfolio.setup_backtesting(
            start_date,
            end_date,
            backtesting_name
        )
        self.run_backtesting()

    def run_backtesting(
            self: Any
    ) -> None:
        """
        - Initialize Trading
        - Will run through all of the backtesting data
        - Liquidate last objects (if exist)
        - Export csv file with all of the strategy object created
        - Print portfolio amounts
        """
        print("Initializing Trading")
        self.portfolio.initialize_trading()
        print("Running...")
        prev_per = 0
        while not self.portfolio.data_manager.check_end_of_file():
            per = int(100.0*self.portfolio.data_manager.current_index / (1.0*self.portfolio.data_manager.minutes))
            if prev_per != per:
                print(f"{per} \r", end="")
                prev_per = per
            self.portfolio.tick()
        print("Finished Running!")
        self.portfolio.data_manager.current_index -= 1
        print("Liquidating last open positions")
        self.portfolio.liquidate(liquidate_all=True)
        print("Exporting data to file "
              "(find in backtesting results directory)")
        self.portfolio.export_strategies()
        self.portfolio.export_trades()
        print(f"current portfolio value: "
              f"{self.portfolio.portfolio_money}")

    def restore_old_objects(
            self: Any
    ) -> None:
        """
        Once the user chooses trading option,
        this will be the second screen. Basically,
        it fetches the non expired objects from the database
        and shows them to the user one by one. The user
        has to decide which objects he wants to:
        1. Push to live trading
        2. Liquidate
        3. Remove
        :return: None
        """
        latest_object_creation_date = {}
        old_strategies = \
            self.portfolio.database.restore_last_objects()
        if old_strategies is not None:
            old_strategies = \
                self.portfolio.restore_strategy_objects(
                    old_strategies
                )
            passed_restore_live_object_first_screen = False
            while not passed_restore_live_object_first_screen:
                print(f"You have {len(old_strategies)} "
                      f"non expired strategy objects from last session")
                answer = input("Would you like to restore them? (If "
                               "yes, you will approve one by one)\n"
                               "Please enter y/n: ")
                print("------------------------\n")
                if answer == 'y':
                    passed_restore_live_object_first_screen = True
                    for old_strategy in old_strategies:
                        passed_restore_live_object_second_screen = False
                        old_strategy.print_details()
                        while not passed_restore_live_object_second_screen:
                            if old_strategy.live_position:
                                print("$$$ This is an executed position $$$")
                            answer = int(input("For adding this strategy object to live"
                                               "trading, enter 1\n"
                                               "For liquidating this position, enter 2\n"
                                               "For removing this position enter 3\n"
                                               "Please enter: "))
                            if answer == 1:
                                passed_restore_live_object_second_screen = True
                                if self.portfolio.strategy_dictionary[
                                        old_strategy.strategy_name]['advanced_settings']:
                                    if old_strategy.short_allowed or \
                                            old_strategy.strategy_position == 'short':
                                        short = \
                                            self.portfolio.check_if_allowed_to_create_position(
                                                'short',
                                                old_strategy.strategy_name,
                                                old_strategy.pair
                                            )
                                    if old_strategy.long_allowed or \
                                            old_strategy.strategy_position == 'long':
                                        long = \
                                                self.portfolio.check_if_allowed_to_create_position(
                                                    'long',
                                                    old_strategy.strategy_name,
                                                    old_strategy.pair
                                                )
                                    if short and long:
                                        self.portfolio.active_strategy_objects[
                                            old_strategy.strategy_id] = old_strategy
                                        self.portfolio.check_strategy_current_short_long_positions()
                                        try:
                                            if latest_object_creation_date[
                                                    old_strategy.strategy_name] < \
                                                    old_strategy.creation_time:
                                                latest_object_creation_date[
                                                    old_strategy.strategy_name] = \
                                                    old_strategy.creation_time
                                        except KeyError:
                                            latest_object_creation_date[
                                                old_strategy.strategy_name] = \
                                                old_strategy.creation_time
                                    else:
                                        print("Reached max allowed short/ long")
                                        answer = input("Do you want to force input this object?\n"
                                                       "Enter y/n (if not object will be set to expired): ")
                                        if answer == 'y':
                                            self.portfolio.active_strategy_objects[
                                                old_strategy.strategy_id] = old_strategy
                                            self.portfolio.check_strategy_current_short_long_positions()
                                            try:
                                                if latest_object_creation_date[
                                                        old_strategy.strategy_name] < \
                                                        old_strategy.creation_time:
                                                    latest_object_creation_date[
                                                        old_strategy.strategy_name] = \
                                                        old_strategy.creation_time
                                            except KeyError:
                                                latest_object_creation_date[
                                                    old_strategy.strategy_name] = \
                                                    old_strategy.creation_time
                                        if answer == 'n':
                                            self.portfolio.database.set_object_to_expired(
                                                old_strategy.strategy_id
                                            )
                                else:
                                    self.portfolio.active_strategy_objects[
                                        old_strategy.strategy_id] = \
                                        old_strategy
                            elif answer == 2:
                                passed_restore_live_object_second_screen = True
                                self.portfolio.liquidate(
                                    strategy_object=old_strategy
                                )
                            elif answer == 3:
                                passed_restore_live_object_second_screen = True
                                self.portfolio.database.set_object_to_expired(
                                    old_strategy.strategy_id
                                )
                elif answer == 'n':
                    passed_restore_live_object_first_screen = True
                    for old_strategy in old_strategies:
                        self.portfolio.database.set_object_to_expired(
                            old_strategy.strategy_id
                        )
        for strategy_name, strategy_creation_time in \
                latest_object_creation_date.items():
            self.portfolio.strategy_dictionary[
                strategy_name]['last_object_created_time'] = \
                strategy_creation_time

    def information_thread(
            self: Any
    ):
        """
        This will print out details based on user's input
        :return:
        """
        while self.portfolio.Trade:
            print(f"1. For active object enter 1. "
                  f"Total active objects "
                  f"{len(self.portfolio.active_strategy_objects)} \n"
                  "2. For liquidation enter 2\n"
                  "3. For Strategy details enter 3\n"
                  "4. For shutdown enter 4\n"
                  "5. For fetching balance enter 5\n"
                  "6. For exporting all strategy history enter 6\n"
                  "7. For exporting all trades history enter 7\n"
                  f"Data shown is for {self.portfolio.current_time}, "
                  f"for refresh enter 9")
            print("-----------------")
            arg = input("Please enter number: ")
            print("-----------------")
            if arg == '1':
                for strategy_id, strategy_object in \
                        self.portfolio.active_strategy_objects.items():
                    print(f"{strategy_object.strategy_name} "
                          f"- id: {strategy_id}")
            elif arg == "2":
                id = int(input("Please enter id to "
                               "liquidate or 0 for all positions: "))
                if id == 0:
                    self.portfolio.liquidate(liquidate_all=True)
                else:
                    self.portfolio.liquidate(id=id)
            elif arg == '3':
                id = input("For all objects enter 0, else enter\n"
                           "strategy id: ")
                if id == '0':
                    for strategy_object in \
                            self.portfolio.active_strategy_objects.values():
                        strategy_object.print_details()
                elif id in self.portfolio.active_strategy_objects:
                    self.portfolio.active_strategy_objects[id].print_details()
                else:
                    print("Incorrect id")
            elif arg == '4':
                if len(self.portfolio.executed_strategy_ids) > 0:
                    last_chance = input(f"You have \
                                        {len(self.portfolio.executed_strategy_ids)} \
                                        live trades\n"
                                        f"Do you want to liquidate them \
                                        before shutting down?\n"
                                        f"Please enter y/n: ")
                    if last_chance == 'y':
                        self.portfolio.liquidate(liquidate_all=True)
                self.portfolio.Trade = False
            elif arg == '5':
                coin = input("For all coins in portfolio enter 0\n"
                             "For specific coin please enter\n"
                             "coin (for example BTC): ")
                if coin == '0':
                    print(self.portfolio.trader.balance(
                        list(self.portfolio.coins)))
                else:
                    print(self.portfolio.trader.balance([coin]))
            elif arg == '6':
                self.portfolio.export_strategies(backtesting=False)
                print("Exported Strategies file")
            elif arg == '7':
                self.portfolio.export_trades(backtesting=False)
                print("Exported History file")
            print("===========================")

    def initialize_threads(
            self:  Any
    ):
        """
        This will initalize our threads:
        1. Ticking thread -> fetch the price and run strat
        2. Info thread -> user information
        :return:
        """
        print("Start ticking")
        ticking_thread = threading.Thread(
            target=self.portfolio.ticking_thread, args=()
        )
        info_thread = threading.Thread(
            target=self.information_thread, args=()
        )
        ticking_thread.start()
        info_thread.start()


if __name__ == "__main__":
    pass
