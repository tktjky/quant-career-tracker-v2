import time
import logging
import threading
from datetime import datetime
from agent.crawl_agent import CrawlAgent

logger = logging.getLogger("Scheduler")

class CrawlScheduler:
    """
    Recurring daemon that triggers CrawlAgent on an interval (e.g., every 6 hours or 24 hours),
    logging delta updates and ensuring Kevin always has the latest openings.
    """

    def __init__(self, interval_hours: float = 6.0):
        self.interval_seconds = int(interval_hours * 3600)
        self.agent = CrawlAgent()
        self._running = False
        self._thread = None

    def _loop(self):
        logger.info(f"Scheduler daemon started. Crawl interval: {self.interval_seconds} seconds.")
        while self._running:
            try:
                logger.info(f"Scheduled crawl triggered at {datetime.now().isoformat()}...")
                result = self.agent.run_crawl()
                stats = result.get("stats", {})
                logger.info(
                    f"Crawl completed successfully: {stats.get('total_live_openings')} live openings "
                    f"({stats.get('new_openings_this_crawl')} new, {stats.get('active_openings')} active)."
                )
            except Exception as e:
                logger.error(f"Error during scheduled crawl: {e}")
            
            # Sleep in 1-second chunks to allow graceful shutdown
            for _ in range(self.interval_seconds):
                if not self._running:
                    break
                time.sleep(1)

    def start_background(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def run_blocking(self):
        self._running = True
        try:
            self._loop()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        logger.info("Scheduler daemon stopped.")
