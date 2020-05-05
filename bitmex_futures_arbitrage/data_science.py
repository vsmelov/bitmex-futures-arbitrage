from typing import Dict
import logging

from bitmex_futures_arbitrage.const import XBTU20, XBTM20
from bitmex_futures_arbitrage.models import Quote

logger = logging.getLogger()


class DataScienceEstimates:
    """ artificial intelligence to analyse trading data and update estimates using upcoming events

    Yeah, now sets the avg_futures_spread estimate once, but feel free to improve it :-)
    """
    def __init__(self):
        self.avg_futures_spread = None

    @staticmethod
    def get_avg_futures_spread(quotes: Dict[str, Quote]):
        xbtu = (quotes[XBTU20].ask_price + quotes[XBTU20].bid_price) / 2
        xbtm = (quotes[XBTM20].ask_price + quotes[XBTM20].bid_price) / 2
        return (xbtu - xbtm) / 2

    def on_quotes(self, quotes: Dict[str, Quote]):
        if self.avg_futures_spread is None:
            self.avg_futures_spread = self.get_avg_futures_spread(quotes)
            logger.info(f'{self.avg_futures_spread=}')
