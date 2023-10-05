from _operator import mul, attrgetter
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from functools import reduce
from itertools import groupby


class Stock(ABC):
    """A Stock in Global Beverage Corporation Exchange."""
    def __init__(self, symbol, par_value, last_dividend=None, fixed_dividend=None):
        self.symbol = symbol.upper()
        self.last_dividend = last_dividend
        self.par_value = par_value
        self.fixed_dividend = fixed_dividend

    @abstractmethod
    def dividend_yield(self, price):
        """Calculate the dividend yield for a given stock price.

        :param price: stock price
        :type price: float
        :return: dividend yield of a stock
        :rtype: float
        """
        pass

    def pe_ratio(self, price):
        """Calculate PE Ratio of a given stock.

        PE Ratio = Price/Dividend

        :param price:
        :type
        :return PE Ratio
        """
        return 1 / self.dividend_yield(price)


class CommonTypeStock(Stock):
    """A common type stock"""

    def dividend_yield(self, price):
        """
        Calculate the dividend yield for a given stock price

        :param price: stock price, in pence
        :type price: float
        :return: dividend yield of common type stock
        :rtype: float
        """
        return self.last_dividend / price


class PreferredTypeStock(Stock):
    """A preferred type stock"""

    def dividend_yield(self, price):
        """
        Calculate the dividend yield for a given stock price

        :param price: stock price, in pence
        :type price: float
        :return: dividend yield
        :rtype: float
        """
        return self.fixed_dividend * self.par_value / price


class TradeType(Enum):
    """Buy or Sell Trade."""
    buy = 1
    sell = 2


class Trade(object):
    """A trade of a stock"""

    def __init__(self, stock: Stock, quantity, trade_type: TradeType, price):
        self.stock = stock
        self.quantity = quantity
        self.trade_type = trade_type  # buy or sell
        self.price = price
        self.timestamp = datetime.utcnow()


class StockExchange(object):
    """Global Beverage Corporation Exchange"""
    def __init__(self):
        self.trades = []

    def record_trade(self, trade: Trade):
        """
        Record a trade on the stock exchange

        :param trade: a single trade (buy or sell) of stocks
        :type trade: :class: Trade
        """
        self.trades.append(trade)

    def volume_weight_stock_price(self, symbol, duration):
        """
        Calculate the volume weighted average price of a stock over a certain duration

        :param symbol: stock symbol
        :type symbol: str
        :param duration: in minutes
        :type duration: int
        :return: volume weighted average trading price
        :rtype: float
        """
        # get trades in the last 'n' minutes
        trades = [trade for trade in self.trades
                  if trade.stock.symbol == symbol.upper()
                  and trade.timestamp >= datetime.utcnow() - timedelta(minutes=duration)]
        if not trades:
            return None

        return self.vwap(trades)

    def vwap(self, trades):
        """Calculate volume weighted average price of a stock"""
        return (sum(trade.price * trade.quantity for trade in trades) / sum(trade.quantity for trade in trades))

    def all_share_index(self):
        """
        Calculate the exchange's All Share Index over a certain duration

        :param duration: duration in minutes
        :type duration: int
        :return: the All Share Index
        :rtype: float or None
        """
        if not self.trades:
            return None

        # get the trades for all stocks
        stock_groups = groupby(self.trades, key=attrgetter('stock.symbol'))
        # get weighted price of all the stocks
        prices = [self.vwap(list(trades)) for symbol, trades in stock_groups]
        # apply formula for all share index
        return reduce(mul, prices) ** (1 / len(prices))



