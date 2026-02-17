"""Placeholder listener for Edge Oculus Prime service.

Oculus Prime is producer-first (HTTP ingest -> Redis Streams emit).
This module is reserved for future backpressure/DLQ maintenance jobs.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Edge Oculus Prime listener is not required in MVP (producer-only service).")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    main()
