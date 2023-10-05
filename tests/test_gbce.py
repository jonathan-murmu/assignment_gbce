import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

from gbce.gbce import Stock, CommonTypeStock, PreferredTypeStock, TradeType, Trade, StockExchange


class TestStock(unittest.TestCase):
    @patch.multiple(Stock, __abstractmethods__=set())
    def test_record_stock(self):
        stock = Stock('ALE', last_dividend=23, par_value=60)
        self.assertEqual('ALE', stock.symbol)
        self.assertEqual(23, stock.last_dividend)
        self.assertEqual(60, stock.par_value)
        self.assertIsNone(stock.fixed_dividend)

    @patch.multiple(Stock, __abstractmethods__=set())
    def test_record_stock_lowercase_sym(self):
        stock = Stock('ale', last_dividend=23, par_value=60)
        self.assertEqual('ALE', stock.symbol)

    @patch.multiple(Stock, __abstractmethods__=set())
    def test_dividend_yield_common(self):
        stock = CommonTypeStock('POP', last_dividend=8, par_value=100)
        self.assertEqual(0.08, stock.dividend_yield(price=100))

    @patch.multiple(Stock, __abstractmethods__=set())
    def test_dividend_yield_preferred(self):
        stock = PreferredTypeStock('GIN', last_dividend=8, fixed_dividend=0.02, par_value=100)
        self.assertEqual(0.02, stock.dividend_yield(price=100))

    @patch.multiple(Stock, __abstractmethods__=set())
    def test_pe_ratio_common(self):
        stock = CommonTypeStock('POP', last_dividend=8, par_value=100)
        self.assertEqual(12.5, stock.pe_ratio(price=100))

    @patch.multiple(Stock, __abstractmethods__=set())
    def test_pe_ratio_preferred(self):
        stock = PreferredTypeStock('GIN', last_dividend=8, fixed_dividend=0.02, par_value=100)
        self.assertEqual(50, stock.pe_ratio(price=100))


class TestTrade(unittest.TestCase):
    def test_buy_trade(self):
        stock = Mock()
        trade = Trade(stock=stock, quantity=20, trade_type=TradeType.buy, price=100)
        self.assertEqual(stock, trade.stock)
        self.assertEqual(20, trade.quantity)
        self.assertEqual(TradeType.buy, trade.trade_type)
        self.assertEqual(100, trade.price)
        
    def test_sell_trade(self):
        stock = Mock()
        trade = Trade(stock=stock, quantity=20, trade_type=TradeType.sell, price=100)
        self.assertEqual(TradeType.sell, trade.trade_type)


class TestStockExchange(unittest.TestCase):
    def test_create_exchange(self):
        exchange = StockExchange()
        self.assertEqual(0, len(exchange.trades))

    def test_record_trade(self):
        exchange = StockExchange()
        trade = Mock()
        exchange.record_trade(trade)
        # Test if the last trade is the trade just recorded
        self.assertEqual(trade, exchange.trades[-1])

    def test_volume_weight_stock_price(self):
        exchange = StockExchange()
        stock = Mock(symbol='POP')
        exchange.trades = [
            Trade(stock=stock, quantity=15, trade_type=TradeType.buy, price=100),
            Trade(stock=stock, quantity=25, trade_type=TradeType.buy, price=60)
        ]
        self.assertAlmostEqual(75.0, exchange.volume_weight_stock_price('POP', duration=5))

    def test_all_share_index(self):
        exchange = StockExchange()
        exchange.trades = [
            Trade(stock=Mock(symbol='TEA'), quantity=15, trade_type=TradeType.buy, price=100),
            Trade(stock=Mock(symbol='POP'), quantity=25, trade_type=TradeType.buy, price=10),
            Trade(stock=Mock(symbol='POP'), quantity=25, trade_type=TradeType.buy, price=60),
            Trade(stock=Mock(symbol='GIN'), quantity=25, trade_type=TradeType.buy, price=110),
            Trade(stock=Mock(symbol='JOE'), quantity=25, trade_type=TradeType.buy, price=250)
        ]
        self.assertAlmostEqual(99.05, round(exchange.all_share_index(), 2))


class TestSimpleStockMarket(unittest.TestCase):
    def test_exercise(self):
        gbce = StockExchange()
        stocks = {
            'TEA': CommonTypeStock('TEA', last_dividend=0, par_value=100),
            'POP': CommonTypeStock('POP', last_dividend=8, par_value=100),
            'ALE': CommonTypeStock('ALE', last_dividend=23, par_value=60),
            'GIN': PreferredTypeStock('GIN', last_dividend=8, fixed_dividend=0.02, par_value=100),
            'JOE': CommonTypeStock('JOE', last_dividend=13, par_value=250)
        }
        # Given any price of common stock as input, calculate the dividend yield.
        pop_dividend_yield = stocks['ALE'].dividend_yield(price=100)
        self.assertEqual(0.23, pop_dividend_yield)

        # Given any price of preferred stock as input, calculate the dividend yield.
        gin_dividend_yield = stocks['GIN'].dividend_yield(price=100)
        self.assertEqual(0.02, gin_dividend_yield)

        # Given any price as input, calculate the P/E Ratio
        pop_pe_ratio = stocks['ALE'].pe_ratio(price=100)
        self.assertEqual(4.35, round(pop_pe_ratio, 2))

        # Record a trade, with timestamp, quantity of shares, buy or sell indicator and traded price
        gbce.record_trade(Trade(stocks['TEA'], 100, TradeType.buy, 110))
        gbce.record_trade(Trade(stocks['TEA'], 200, TradeType.buy, 105))
        gbce.record_trade(Trade(stocks['GIN'],  200, TradeType.buy,  80))
        self.assertEqual(3, len(gbce.trades))
        self.assertTrue(all(t.timestamp >= datetime.utcnow() - timedelta(seconds=0.1)
                            for t in gbce.trades))

        # Calculate Volume Weighted Stock Price based on trades in past 15 minutes
        tea_price = gbce.volume_weight_stock_price('TEA', duration=15)
        self.assertAlmostEqual(106.67, round(tea_price, 2))

        # Calculate the GBCE All Share Index using the geometric mean of prices for all stocks
        gbce_index = gbce.all_share_index()
        self.assertAlmostEqual(92.38, round(gbce_index, 2))


if __name__ == '__main__':
    unittest.main()
