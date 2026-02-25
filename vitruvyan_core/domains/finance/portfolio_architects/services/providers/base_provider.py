"""
Base Provider Interface
Defines abstract interface for all price providers.

Timeout / Retry / Rate-limit defaults live here so every concrete
provider inherits a safe baseline.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)

# ── Resilience defaults ────────────────────────────────────────────
DEFAULT_TIMEOUT_SECONDS: int = 15
DEFAULT_MAX_RETRIES: int = 3
DEFAULT_RETRY_BACKOFF: float = 1.5  # exponential backoff multiplier


@dataclass
class PriceResult:
    """Price data with metadata"""
    ticker: str
    price: float
    timestamp: datetime
    source: str
    delay_seconds: int  # 0 = real-time, 900 = 15 min delay
    currency: str = "USD"
    volume: Optional[int] = None
    
    def is_realtime(self) -> bool:
        """Check if price is real-time (< 60 seconds delay)"""
        return self.delay_seconds < 60


class BaseProvider(ABC):
    """Abstract base class for price providers with built-in resilience."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff: float = DEFAULT_RETRY_BACKOFF,
    ):
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.name = self.__class__.__name__.replace("Provider", "")
    
    # ── retry helper (used by concrete providers) ──────────────────
    def _retry(self, fn, label: str = ""):
        """
        Call *fn* up to self.max_retries times with exponential backoff.
        Returns the result on first success, or None after exhausting retries.
        """
        last_exc = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return fn()
            except Exception as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    wait = self.retry_backoff ** attempt
                    logger.warning(
                        f"[{self.name}] {label} attempt {attempt}/{self.max_retries} "
                        f"failed ({exc}), retrying in {wait:.1f}s…"
                    )
                    time.sleep(wait)
                else:
                    logger.error(
                        f"[{self.name}] {label} exhausted {self.max_retries} retries: {last_exc}"
                    )
        return None
    
    @abstractmethod
    def get_price(self, ticker: str) -> Optional[PriceResult]:
        """
        Get current price for a single ticker
        
        Args:
            ticker: Stock symbol (e.g., "AAPL")
        
        Returns:
            PriceResult or None if fetch failed
        """
        pass
    
    def get_bulk_prices(self, tickers: List[str]) -> dict[str, Optional[PriceResult]]:
        """
        Get prices for multiple tickers (default: sequential calls)
        Override for providers with batch API support
        
        Args:
            tickers: List of stock symbols
        
        Returns:
            Dict mapping ticker to PriceResult (or None if failed)
        """
        results = {}
        for ticker in tickers:
            try:
                results[ticker] = self.get_price(ticker)
            except Exception as e:
                logger.warning(f"[{self.name}] Failed to fetch {ticker}: {e}")
                results[ticker] = None
        
        return results
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is properly configured and reachable"""
        pass
    
    def __repr__(self) -> str:
        return f"<{self.name}Provider>"
