import asyncio
import logging
from optparse import OptionParser

from bitmex_futures_arbitrage.manager import Manager

logger = logging.getLogger()


def parse_args():
    parser = OptionParser()
    parser.add_option(
        "--log-level",
        dest="log_level",
        help="log level",
        default='info',
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        metavar="LEVEL",
    )
    options, _args = parser.parse_args()
    return options


def main():
    options = parse_args()
    logging.basicConfig(level=options.log_level.upper())
    logging.getLogger('asyncio').setLevel(logging.ERROR)
    logging.getLogger('websockets').setLevel(logging.ERROR)
    manager = Manager()
    asyncio.get_event_loop().run_until_complete(manager.run_forever())


if __name__ == '__main__':
    main()
