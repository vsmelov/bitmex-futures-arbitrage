import random
import dataclasses
from typing import Dict, Optional


class Direction:
    BUY = 'buy'
    SELL = 'sell'
    ALL = [BUY, SELL]

    @classmethod
    def inverse(cls, value):
        if value == cls.BUY:
            return cls.SELL
        elif value == cls.SELL:
            return cls.BUY
        else:
            raise ValueError(value)


class OrderKind:
    LIMIT = 'limit'
    MARKET = 'market'


@dataclasses.dataclass
class Order:
    symbol: str
    size: float
    kind: str
    direction: str
    price: Optional[float] = None  # not used for market orders
    uid: int = dataclasses.field(default_factory=lambda: random.randrange(10**9))


@dataclasses.dataclass
class Quote:
    timestamp: float
    symbol: str
    bid_price: float
    bid_size: float
    ask_price: float
    ask_size: float


@dataclasses.dataclass
class State:
    avg_spread: float
    symbol2quote: Dict[str, Quote]
    symbol2position: Dict[str, float]


@dataclasses.dataclass
class MyTrade:
    symbol: float
    price: float
    size: float
    my_direction: str  # independent from taker or maker
