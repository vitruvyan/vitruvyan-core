#!/usr/bin/env python3
"""
Learning Profile Worker

Consumes captured feedback events and updates user_learning_profile periodically.
"""

import logging
import os
import signal
import time

from domains.finance.learning import LearningProfileUpdater


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RUNNING = True


def _handle_shutdown(signum, _frame):
    global RUNNING
    RUNNING = False
    logger.info("Learning profile worker received shutdown signal: %s", signum)


def main():
    enabled = os.getenv("LEARNING_PROFILE_UPDATER_ENABLED", "1").strip().lower() in {"1", "true", "yes", "on"}
    interval_seconds = int(os.getenv("LEARNING_PROFILE_UPDATE_INTERVAL_SECONDS", "60"))
    batch_size = int(os.getenv("LEARNING_PROFILE_BATCH_SIZE", "500"))

    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)

    if not enabled:
        logger.info("Learning profile updater disabled (LEARNING_PROFILE_UPDATER_ENABLED=0)")
        while RUNNING:
            time.sleep(60)
        return

    updater = LearningProfileUpdater(batch_size=batch_size)
    logger.info(
        "Learning profile updater started: interval=%ss batch_size=%s",
        interval_seconds,
        batch_size,
    )

    while RUNNING:
        try:
            summary = updater.run_once()
            logger.info("Learning profile update cycle completed: %s", summary)
        except Exception as exc:
            logger.error("Learning profile update cycle failed: %s", exc, exc_info=True)

        sleep_left = interval_seconds
        while RUNNING and sleep_left > 0:
            step = min(5, sleep_left)
            time.sleep(step)
            sleep_left -= step

    logger.info("Learning profile worker stopped")


if __name__ == "__main__":
    main()
