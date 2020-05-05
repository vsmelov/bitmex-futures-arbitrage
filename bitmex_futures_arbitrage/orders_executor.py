import math
from collections import defaultdict
from typing import Dict, DefaultDict, List
import logging

from bitmex_futures_arbitrage.const import XBTM20, XBTU20
from bitmex_futures_arbitrage.models import Quote, Direction, Order, OrderKind

logger = logging.getLogger()


class PaperOrdersExecutor:
    """ dealing with exchange pseudo-orders in paper-mode """
    def __init__(self):
        self.symbol2direction2order: DefaultDict[str, Dict[str, Order]] = defaultdict(dict)
        self.symbol2position: DefaultDict[str, float] = defaultdict(float)

    def orders_execution_on_quotes(
            self,
            quotes: Dict[str, Quote],
    ):
        """ Calculate order execution on quotes.
            Keep in mind that there are no partial fill for now since we use minimum possible size.
        """
        buy_order = self.symbol2direction2order[XBTM20].get(Direction.BUY)
        if buy_order and quotes[XBTM20].ask_price and buy_order.price >= quotes[XBTM20].ask_price:
            logger.info(f'BUY {XBTM20} price={quotes[XBTM20].ask_price} size={buy_order.size} {buy_order=}')
            del self.symbol2direction2order[XBTM20][Direction.BUY]
            self.symbol2position[XBTM20] += buy_order.size
            logger.info(f'{self.symbol2position=}')

        sell_order = self.symbol2direction2order[XBTM20].get(Direction.SELL)
        if sell_order and quotes[XBTM20].bid_price and sell_order.price <= quotes[XBTM20].bid_price:
            logger.info(f'SELL {XBTM20} price={quotes[XBTM20].bid_price} size={sell_order.size} {sell_order=}')
            del self.symbol2direction2order[XBTM20][Direction.SELL]
            self.symbol2position[XBTM20] -= sell_order.size
            logger.info(f'{self.symbol2position=}')

    def manage_orders(self, orders: List[Order], quotes: Dict[str, Quote]):
        """ place / amend / cancel orders """
        desired_limit_orders_symbol_direction = []
        for order in orders:
            if order.kind == OrderKind.MARKET:
                self.execute_market_order(order=order, quotes=quotes)
            elif order.kind == OrderKind.LIMIT:
                self.manage_limit_order(order)
                desired_limit_orders_symbol_direction.append((order.symbol, order.direction))
            else:
                raise ValueError(order.kind)

        for symbol, direction2order in self.symbol2direction2order.items():
            for direction, order in list(direction2order.items()):  # copy to avoid iteration over mutating structure
                if (symbol, direction) not in desired_limit_orders_symbol_direction:
                    logger.info(f'CANCEL limit order {order}')
                    del direction2order[direction]

    def execute_market_order(self, order: Order, quotes: Dict[str, Quote]):
        """ immediately execute market orders using best bid/ask """
        assert order.symbol == XBTU20
        if order.direction == Direction.BUY and quotes[order.symbol].ask_price:
            logger.info(
                f'BUY {order.symbol} '
                f'price={quotes[order.symbol].ask_price} size={order.size} {order=}')
            self.symbol2position[order.symbol] += order.size
            logger.info(f'{self.symbol2position=}')
        elif order.direction == Direction.SELL and quotes[order.symbol].bid_price:
            logger.info(
                f'SELL {order.symbol} '
                f'price={quotes[order.symbol].bid_price} size={order.size} {order=}')
            self.symbol2position[order.symbol] -= order.size
            logger.info(f'{self.symbol2position=}')
        else:
            raise ValueError(order.direction)

    @staticmethod
    def rounded_direction_price(direction: str, price: float) -> float:
        """ floor/ceil buy/sell price """
        if direction == Direction.BUY:
            return math.floor(price * 2) / 2
        elif direction == Direction.SELL:
            return math.ceil(price * 2) / 2
        else:
            raise ValueError(direction)

    def manage_limit_order(self, order: Order):
        """ place / amend limit order """
        order.price = self.rounded_direction_price(direction=order.direction, price=order.price)
        placed_order = self.symbol2direction2order[order.symbol].get(order.direction)
        if placed_order:
            if placed_order.price != order.price or placed_order.size != order.size:
                placed_order.price = order.price
                placed_order.size = order.size
                logger.info(f'EDIT order {placed_order}')
        else:
            logger.info(f'PLACE order {order}')
            self.symbol2direction2order[order.symbol][order.direction] = order
