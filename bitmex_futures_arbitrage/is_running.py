import signal
import logging

logger = logging.getLogger(__name__)


class _IsRunning:
    """ Is process running or stopping.
    Set handlers on SIGINT and SIGTERM on init and set state False on graceful termination.
    Use it like `while is_running:` instead of `while True:`
    """
    def __init__(self):
        self._is_running = True
        signal.signal(signal.SIGINT, self.stop_by_signal)
        signal.signal(signal.SIGTERM, self.stop_by_signal)

    def stop_by_signal(self, signum, _frame):
        logger.info(f'stop_by_signal {signum}')
        self.stop()

    def stop(self):
        logger.info('is_running.stop()')
        self._is_running = False

    def __bool__(self):
        return self._is_running


is_running = _IsRunning()
