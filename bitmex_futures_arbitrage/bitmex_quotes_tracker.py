import datetime
import json
import websockets
from typing import Dict, Callable, List
import logging

from websockets import WebSocketClientProtocol

from bitmex_futures_arbitrage.is_running import is_running
from bitmex_futures_arbitrage.models import Quote

logger = logging.getLogger()


class BitmexQuotesTracker:
    """
    Track Bitmex quotes and call `on_quotes` handler on any change
    """
    URL = 'wss://www.bitmex.com/realtime'

    def __init__(self, symbols: List[str]):
        self._symbols = symbols
        self._topics = [f'quote:{symbol}' for symbol in self._symbols]
        self.symbol2quote: Dict[str, Quote] = {}

    def _url(self):
        topics = ",".join(self._topics)
        return f'{self.URL}?subscribe={topics}'

    @staticmethod
    async def _ensure_first_message(ws: WebSocketClientProtocol):
        """ ensure receiving correct first message """
        # e.g.
        # {'docs': 'https://www.bitmex.com/app/wsAPI',
        #  'info': 'Welcome to the BitMEX Realtime API.',
        #  'limit': {'remaining': 36},
        #  'timestamp': '2020-05-04T15:37:55.326Z',
        #  'version': '2020-04-30T00:58:37.000Z'}
        msg_raw = await ws.recv()
        first_msg = json.loads(msg_raw)
        assert first_msg['info'] == "Welcome to the BitMEX Realtime API.", 'unexpected first message'

    async def _ensure_subscribed_to_topics(self, ws: WebSocketClientProtocol):
        subscribed_topics = []
        for _ in range(len(self._topics)):
            msg_raw = await ws.recv()
            subscribed_topics.append(json.loads(msg_raw)['subscribe'])
        assert set(subscribed_topics) == set(self._topics), 'something wrong with subscriptions'

    @staticmethod
    def _record2quote(record: Dict) -> Quote:
        return Quote(
            symbol=record['symbol'],
            timestamp=datetime.datetime.strptime(record['timestamp'], '%Y-%m-%dT%H:%M:%S.%f%z').timestamp(),
            bid_price=record['bidPrice'],
            ask_price=record['askPrice'],
            bid_size=record['bidSize'],
            ask_size=record['askSize'],
        )

    def _on_quote_msg(self, msg):
        assert msg['action'] in ['partial', 'insert'], 'incorrect quote message'
        for record in msg['data']:
            quote = self._record2quote(record)
            # it happens that record timestamp == previous quote timestamp (because of millisecond rounding)
            assert quote.symbol not in self.symbol2quote or quote.timestamp >= self.symbol2quote[quote.symbol].timestamp
            self.symbol2quote[quote.symbol] = quote

    async def handle_events_forever(self, on_quotes_callback: Callable[[Dict[str, Quote]], None]):
        url = self._url()
        logger.info(f'connect to WS {url}')
        async with websockets.connect(url) as ws:
            await self._ensure_first_message(ws)
            await self._ensure_subscribed_to_topics(ws)
            while is_running:
                msg_raw = await ws.recv()
                msg = json.loads(msg_raw)
                if msg['table'] == 'quote':
                    self._on_quote_msg(msg)
                    on_quotes_callback(self.symbol2quote)
                else:
                    raise ValueError(f'unknown table {msg["table"]}')
