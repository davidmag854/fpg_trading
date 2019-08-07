"""
Functions for initializing trader
and portfolio
"""
from lib.py.fpg.constants import (
    Environment
)
from lib.py.fpg.logger import (
    get_module_logger
)
from lib.py.fpg.trader import (
    FPGTrader
)
from lib.py.fpg.utils import (
    fetch_keys
)

from user_managment.portfolio import(
    PortfolioManager
)

logger = get_module_logger('core')


def initialize_trader():
    # Pull the keys
    env: Environment = Environment.DEBUG
    (public_key, private_key) = fetch_keys(env)
    trader = FPGTrader(
        public_key=public_key,
        private_key=private_key
    )
    trader.connect()
    logger.info("Trader has been constructed and connected. Starting.")
    return trader


def initialize_portfolio():
    portfolio = PortfolioManager()
    logger.info("Portfolio has been created. Initializing.")
    return portfolio