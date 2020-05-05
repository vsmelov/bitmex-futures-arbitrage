from typing import Dict
import logging

from bitmex_futures_arbitrage.bitmex_quotes_tracker import BitmexQuotesTracker
from bitmex_futures_arbitrage.const import XBTU20, XBTM20
from bitmex_futures_arbitrage.data_science import DataScienceEstimates
from bitmex_futures_arbitrage.models import State, Quote
from bitmex_futures_arbitrage.orders_executor import PaperOrdersExecutor
from bitmex_futures_arbitrage.futures_arbitrage_algorithm import FuturesArbitrageAlgorithm

logger = logging.getLogger()


class Manager:
    """ track quotes with `quotes_tracker`,
        recalculate parameters estimates with `estimates`,
        find desired orders by an `algorithm` and execute them in `orders_executor` """
    def __init__(self):
        self.quotes_tracker = BitmexQuotesTracker([XBTU20, XBTM20])
        self.estimates = DataScienceEstimates()
        self.algorithm = FuturesArbitrageAlgorithm
        self.orders_executor = PaperOrdersExecutor()

    async def run_forever(self):
        await self.quotes_tracker.handle_events_forever(self.on_quotes)

    def on_quotes(self, quotes: Dict[str, Quote]):
        if not self.check_ok(quotes):
            return
        self.estimates.on_quotes(quotes)
        self.orders_executor.orders_execution_on_quotes(quotes)
        state = State(
            symbol2position=self.orders_executor.symbol2position,
            symbol2quote=quotes,
            avg_spread=self.estimates.avg_futures_spread,
        )
        logger.debug(f'{state=}')
        orders = self.algorithm.desired_orders(state)
        self.orders_executor.manage_orders(orders=orders, quotes=quotes)
        # It is possible that we executed limit order and
        # in paper-mode our delta-position will not be hedged until the next tick
        # keep in mind that in real-world-mode execution of our order cause orderbook tick (because of size), so
        # handler and hedging will be called short.
        # Also we cannot be sure if order will be executed for the price we expect in quote,
        # in general, in paper-mode we assume that ticks are often enough.

    @staticmethod
    def check_ok(quotes) -> bool:
        """ checks that we have all necessary data and ready to quote """
        return set(quotes) == {XBTU20, XBTM20}
