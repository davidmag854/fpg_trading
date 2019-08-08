from typing import Any
from lib.py.fpg.AbstractStrategies import (
    StrategiesAbstract
)
from lib.py.fpg.utils import (
    generate_id
)


class EmptyStrategy(StrategiesAbstract):
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
        self.strategy_name = 'Sample'
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

    def create_dictionary_for_db(self):
        pass

    def print_details(self):
        pass

    def initialize(self):
        pass

    def check_execution(self):
        pass

    def refresh(self):
        pass
