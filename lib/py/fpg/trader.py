"""
    Actual method that handles the trades and transactions.
"""
import time
from typing import Any

# from constants import (
#     Environment
# )
from lib.py.fpg.fpg_library import (
    FPGConnector
)

from lib.py.fpg.logger import (
    get_module_logger
)

logger = get_module_logger('trader')


class FPGTrader:

    def __init__(
            self: Any,
            public_key: str,
            private_key: str,
    ) -> None:

        self.public_key = public_key
        self.private_key = private_key
        self.fpg_connector = self.connect()
        self.data_manager = None

    def connect(
            self: Any
    ) -> None:

        """
            Tests connection to FPG.
            Connects to all the databases and files.
        """

        logger.info("Trader Connected")

        self.fpg_connector = FPGConnector(
            self.public_key,
            self.private_key
        )

    def trade(
            self: Any,
            base_quote: str,
            amount: float,
            side: str,
            leverage: int
    ) -> float:
        """
        :param base_quote: str -> pair
        :param amount: float -> amount we want to transact
        :param side: str -> 'buy'/ 'sell'
        :return: float -> price the trade was executed at

        The function will fetch the most recent price and
        will execute a trade with the given values.
        """
        completed = False
        logger.info(f"Trading {amount} of {base_quote}, side: {side}")
        pair = base_quote
        while not completed:
            order_price = self.fpg_connector.fetch_price(pair)
            response = self.fpg_connector.execute_trade(
                pair,
                side,
                amount,
                leverage,
                order_price)
            completed = response['succeeded']
            if not completed:
                time.sleep(0.4)
        return order_price, completed['trade_id']

    def balance(
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
        if isinstance(coins, set):
            coins = list(coins)
        logger.info("fetching balance for account")
        return self.fpg_connector.fetch_balance(coins)
