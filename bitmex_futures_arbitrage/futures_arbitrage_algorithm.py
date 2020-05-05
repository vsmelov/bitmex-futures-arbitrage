from typing import List
import logging

from bitmex_futures_arbitrage.const import XBTM20, XBTU20
from bitmex_futures_arbitrage.models import Direction, State, Order, OrderKind

logger = logging.getLogger()


class FuturesArbitrageAlgorithm:
    SPREAD_CREDIT = 5  # 5 USD
    MAX_SIZE = 5000
    ORDER_SIZE = 100

    @staticmethod
    def price(state: State, symbol: str, direction: str) -> float:
        """ Calculate price for a given state

        TODO: fees
        """
        assert symbol == XBTM20
        if direction == Direction.BUY:
            return state.symbol2quote[XBTU20].bid_price - state.avg_spread - FuturesArbitrageAlgorithm.SPREAD_CREDIT
        elif direction == Direction.SELL:
            return state.symbol2quote[XBTU20].ask_price + state.avg_spread + FuturesArbitrageAlgorithm.SPREAD_CREDIT
        else:
            raise ValueError(f'unknown {direction=}')

    @classmethod
    def desired_orders(cls, state: State) -> List[Order]:
        hedge_orders = cls.hedge_orders(state)
        desired_orders = cls.limit_orders(state=state)
        return hedge_orders + desired_orders

    @classmethod
    def limit_orders(cls, state: State) -> List[Order]:
        result: List[Order] = []
        symbol = XBTM20
        for direction in Direction.ALL:
            if direction == Direction.BUY and state.symbol2position[symbol] >= cls.MAX_SIZE:
                logger.debug(f'skip {direction} {symbol} to avoid position increase '
                             f'{state.symbol2position[symbol]=} >= {cls.MAX_SIZE=}')
                continue
            if direction == Direction.SELL and state.symbol2position[symbol] <= -cls.MAX_SIZE:
                logger.debug(f'skip {direction} {symbol} to avoid position decrease '
                             f'{state.symbol2position[symbol]=} <= {-cls.MAX_SIZE=}')
                continue
            price = cls.price(
                state=state,
                symbol=symbol,
                direction=direction,
            )
            result.append(Order(
                size=cls.ORDER_SIZE,
                direction=direction,
                symbol=symbol,
                kind=OrderKind.LIMIT,
                price=price,
            ))
        return result

    @staticmethod
    def hedge_orders(state: State) -> List[Order]:
        result: List[Order] = []
        delta_position = state.symbol2position[XBTM20] + state.symbol2position[XBTU20]
        if delta_position > 0:
            order = Order(
                direction=Direction.SELL,
                size=delta_position,
                symbol=XBTU20,
                kind=OrderKind.MARKET,
            )
            result.append(order)
        elif delta_position < 0:
            order = Order(
                direction=Direction.BUY,
                size=-delta_position,
                symbol=XBTU20,
                kind=OrderKind.MARKET,
            )
            result.append(order)
        return result
