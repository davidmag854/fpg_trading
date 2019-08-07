"""
Risk manager defined by the user
"""
from typing import Any


class RiskManager:
    def __init__(
            self,
            data_manager
    ) -> None:
        self.data_manager = data_manager
        self.percentage_of_aum = 0.01

    def calculate_transaction_amount(
            self: Any,
            pair: str,
            stop_price: float,
            current_aum=None  # For backtesting
    ) -> tuple:
        """
        Will calculate the transaction amount
        based on the current aum and the stop price
        :param pair: str -> pair for transaction
        :param stop_price: float -> stop price for the current position
        :param current_aum: for backtesting reasons
        :return: float-> amount of base we need to sell/ buy
        """
        current_price = self.data_manager.fetch_mid_price(pair)
        if pair is not None:
            split_pair = pair.split("/")
            quote = split_pair[1]
        if current_aum is None:
            current_aum = self.data_manager.fetch_balance([quote])
        else:
            current_aum = current_aum[quote]
        quote_amount_at_risk = abs(current_aum) * self.percentage_of_aum
        difference = abs(current_price-stop_price)
        amount_for_trade = round(quote_amount_at_risk/difference, 6)
        return amount_for_trade, quote, current_price*amount_for_trade
