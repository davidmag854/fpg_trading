"""
This library connects to FPG's endpoint
"""
import requests
import random
from typing import Any

from lib.py.fpg.constants import (
    Constants
)


class FPGConnector:

    """
    This class will connect to fpg endpoint and will:
    1. fetch data
    2. execute orders
    using the class you are able to:
    1. fetch_price -> returns mid price given a pair
    2. fetch_orderbook -> returns an entire orderbook given a pair
    3. fetch_balance -> returns your fpg balance
    4. execute_trad-> executes a trade given:
                      pair, side (buy/sell), amount, order_price

    To initiate the class you must pass api_key
    and secret_key for your FPG account
    """

    def __init__(
            self: Any,
            api_key: str,
            secret_key: str
    ) -> None:
        self.api_key = api_key
        self.secret_key = secret_key

        self.base_url_1 = Constants.endpoint_link
        self.verbose = False

    def addKeys(
            self: Any,
            data: Any
    ) -> Any:
        """
        :param data: dictionary to add the keys to
        :return: dict -> containing the api keys
        """
        data['public_key'] = self.api_key
        data['private_key'] = self.secret_key
        return data

    def fetch_price(
            self: Any,
            pair: str
    ) -> float:
        """
        Connects to FPG's endpoint and retrieves the
        current price of the asset
        :param pair: str -> pair for price
        :return: float -> current price
        """
        url_endpoint = self.base_url_1+"/fetch_price"
        jsonData = {
            "currency_pair": pair
        }
        auth_data = self.addKeys(jsonData)
        if self.verbose:
            print(f"Endpoint: {url_endpoint} | {auth_data}")
        r = requests.get(url_endpoint, json=auth_data)
        return r.json()['mid']

    def fetch_orderbook(
            self: Any,
            pair: str
    ) -> dict:
        """
            Hits the FPG API and returns a consolidated level2 orderbook
        """
        url_endpoint = self.base_url_1+"/fetch_l2_book"
        jsonData = {
            "currency_pair": pair
        }
        auth_data = self.addKeys(jsonData)
        if self.verbose:
            print(f"Endpoint: {url_endpoint} | {auth_data}")
        r = requests.get(url_endpoint, json=auth_data)
        return r.json()

    def fetch_balance(
            self: Any,
            coins: list
    ) -> dict:
        """
        Hits FPG's endpoint and fetches the current balance
        of the coins
        :param coins: list -> coins to check balance for
        :return: dict -> coin:balance
        """
        url_endpoint = self.base_url_1+"/fetch_balance"
        jsonData = {
            "coins": coins
        }
        auth_data = self.addKeys(jsonData)
        if self.verbose:
            print(f"Endpoint: {url_endpoint} | {auth_data}")
        r = requests.get(url_endpoint, json=auth_data)
        r = r.json()
        del r['succeeded']
        return r

    def execute_trade(
            self: Any,
            pair: str,
            side: str,
            amount: float,
            leverage: int,
            order_price: float,
            trade_style: str = "active"
    ):
        """
        Executes trade
        :param pair: pair for trade
        :param side: side fore trade sell/ buy
        :param amount: amount for trade in float
        :param order_price: price to set trade for
        :param trade_style: set to active -> market taker
        :return: the price it was executed for
        """
        # Send in a trade.
        trade_id = int(random.random()*1000000)
        url_endpoint = self.base_url_1+"/execute_trade"
        jsonData = {
            "trade_info": {
                "action": side,
                "amount": amount,
                "ebq": pair,
                "order_price": order_price,
                "leverage": leverage
            },
            "trade_id": trade_id,
            "trade_style": trade_style
        }
        auth_data = self.addKeys(jsonData)
        if self.verbose:
            print(f"Endpoint: {url_endpoint} | {auth_data}")
        r = requests.post(url_endpoint, json=auth_data)
        r = r.json()
        r['trade_id'] = trade_id
        return r


if __name__ == "__main__":

    from constants import (
        Environment
    )
    from utils import (
        fetch_keys
    )

    (public_key, private_key) = fetch_keys(Environment.DEBUG)

    connector = FPGConnector(public_key, private_key)
    connector.verbose = True

    # Test Fetching Prices and balances

    pair = "BTC/USD"
    cur_price = connector.fetch_price(pair)
    print(f"Current Price {cur_price}")
    cur_balance = connector.fetch_balance(['USD', 'BTC'])
    print(f"Current balances {cur_balance}")

    # Test Trading

    side = "sell"
    amount = 0.002
    order_price = cur_price

    trade_result = connector.execute_trade(
        pair, side, amount, order_price, 2)
    print(f"Trade result {trade_result}")

    side = "buy"
    amount = 0.005
    order_price = cur_price

    trade_result = connector.execute_trade(pair, side, amount, order_price, 2)
    print(f"Trade result {trade_result}")

    cur_balance = connector.fetch_balance(['USD', 'BTC'])
    print(f"Current balances {cur_balance}")
    print("-----Done-----")
