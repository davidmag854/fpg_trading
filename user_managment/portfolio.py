"""
Method that will contain all of the different strategy
objects, and will tick based on the given time
"""

from datetime import timedelta
from typing import Any

from lib.py.fpg.logger import (
    get_module_logger
)
from lib.py.fpg.portfolio_parent import (
    Portfolio
)
from lib.py.strategies.momentum_strategy.momentum_v2 import (
    Momentum_v2
)
from lib.py.strategies.mean_reversion.mean_reversion import (
    MeanReversion
)
logger = get_module_logger('portfolio')


class PortfolioManager(Portfolio):

    def __init__(
            self: Any
    ) -> None:
        """
        Will initialize the ticker and the data manager methods
        """
        super().__init__()

        # Portfolio preferences:
        self.tick_time = 0.95
        self.max_executed_strategies = None
        self.max_amount_traded = None
        self.risk_percentage = None
        self.leverage = 3  # Enter x leverage
        self.mandatory_fields = [
            'strategy_id',
            'strategy_name',
            'pair',
            'creation_time',
            'strategy_position',
            'amount',
            'is_expired',
            'live_position',
            'days_passed',
            'is_leverage'
        ]
        # Strategy dictionary - will store strategy options
        # keep on adding options
        self.strategy_dictionary = {
            'Momentum_v2':
                {
                    'object': Momentum_v2,
                    'last_object_created_time': None,
                    'active': True,
                    'creation_interval': timedelta(days=1),
                    'pairs': ['BTC/USD'],
                    'advanced_settings': True,
                    'short': {
                        'max_short_per_pair': 1,
                        'current_short': {
                            'BTC/USD': 0,
                            'ETH/BTC': 0
                        }
                    },
                    'long': {
                        'max_long_per_pair': 1,
                        'current_long': {
                            'BTC/USD': 0,
                            'ETH/BTC': 0
                        }
                    }
                },
            'MeanReversion':
                {
                    'object': MeanReversion,
                    'last_object_created_time': None,
                    'active': True,
                    'creation_interval': timedelta(days=1),
                    'pairs': ['BTC/USD', 'ETH/USD'],
                    'advanced_settings': False
                }

        }
        self.add_pairs_to_coins_portfolio()

    def tick(
            self: Any
    ) -> None:

        """
        This will fetch the current price and time
        and will go through the active strategy objects
        The ticker will handle any action needed after
        running the object
        :return: None -> will change default class values
        """
        logger.info("started fetching price and looping through strategies")
        # Fetch the current time and price
        self.current_time = self.data_manager.fetch_current_time()
        # Check if one of our strategies needs a
        # new object based on exchange open time
        # and interval
        self.check_for_new_object_creation()
        # Combining all of the strategies that we need to check
        expired_strategies = set()
        # If we are in backtesting mode:
        # Looping through our strategies
        for strategy_id, strategy_object in \
                self.active_strategy_objects.items():
            # Refreshing the objects
            response = strategy_object.refresh()
            # If we got some response
            if response:
                self.parse_response_and_execute(response, strategy_object)
                self.database.update_strategy(strategy_object)
            if strategy_object.is_expired:
                expired_strategies.add(strategy_id)
        for object_id in expired_strategies:
            del self.active_strategy_objects[object_id]
        if self.backtesting_mode:
            self.data_manager.current_index += 1

    def initialize_trading(
                self: Any
    ) -> None:
        """
        Will initiate create new objects method
        and will set the settings for the risk manager
        :return: None
        """
        print("Initializing active strategies")
        self.check_for_new_object_creation(True)
        if self.backtesting_mode:
            self.data_manager.current_index += 1
