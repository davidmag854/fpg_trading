"""
Test file for FPG 

To run:
  > pytest test_fpg_library.py
"""
import unittest
from lib.py.fpg.constants import (
    Environment
)
from lib.py.fpg.fpg_library import (
    FPGConnector
)
from lib.py.fpg.utils import (
    fetch_keys
)


class TestFPGLibrary(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        (public_key, private_key) = fetch_keys(Environment.DEBUG)
        self.connector = FPGConnector(public_key, private_key)
        self.connector.verbose = True


    def test_fetch_price(self):
        '''Test Fetching Price from FPG API
        '''

        pair = "BTC/USD"
        cur_price = self.connector.fetch_price(pair)
        print(f"Current Price {cur_price}")
        assert cur_price > 0.0

    def test_fetch_balance(self):
        '''Test Fetching Balance from FPG API
        '''
        balances = self.connector.fetch_balance()
        print(f"Current balances {balances}")
        assert len(balances) > 0
        assert "BTC" in balances  

    def test_execute_buy(self):
        pair = "BTC/USD"
        amount = 0.002
        order_price = self.connector.fetch_price(pair)
        trade_result = self.connector.execute_trade(pair, "buy", amount, order_price)
        print(f"{self.connector.fetch_balance()}")

    def test_execute_sell(self):
        pair = "BTC/USD"
        amount = 0.002
        order_price = self.connector.fetch_price(pair)
        trade_result = self.connector.execute_trade(pair, "sell", amount, order_price)
        print(f"{self.connector.fetch_balance()}")

    def test_execute_trade(self):
        '''Test Executing trade through the FPG API
        This will buy, then immediately sell after. It will print balances along the way.
        '''
        pair = "BTC/USD"
        amount = 0.002
        order_price = self.connector.fetch_price(pair)

        # Fetch the balance before trading.
        pre_balance = self.connector.fetch_balance()
        
        trade_result = self.connector.execute_trade(pair, "sell", amount, order_price)
        print(f"Trade result {trade_result}")

        # Fetch the balance after trading.
        post_balance = self.connector.fetch_balance()

        assert pre_balance['BTC'] > post_balance['BTC']

        # Buy back to fix it.

        trade_result = self.connector.execute_trade(pair, "buy", amount, order_price)

        print(f"Final balance: {self.connector.fetch_balance()}")
