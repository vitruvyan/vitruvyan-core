"""
yfinance Provider - Delayed quotes (15 minutes)
2000 requests/hour FREE, no API key required.

Resilience: timeout + exponential-backoff retries inherited from BaseProvider.
"""

from typing import Optional, List
from datetime import datetime
import logging
import signal
from contextlib import contextmanager

from .base_provider import BaseProvider, PriceResult, DEFAULT_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


# ── Timeout guard for blocking yfinance calls ──────────────────────
class _YFinanceTimeout(Exception):
    """Raised when a yfinance call exceeds the configured timeout."""

@contextmanager
def _timeout_ctx(seconds: int):
    """UNIX-only SIGALRM guard. Falls through silently on Windows."""
    def _handler(signum, frame):
        raise _YFinanceTimeout(f"yfinance call timed out after {seconds}s")
    try:
        old = signal.signal(signal.SIGALRM, _handler)
        signal.alarm(seconds)
        yield
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)
    except (AttributeError, ValueError):
        # Windows / threads — no SIGALRM available, skip
        yield


class YFinanceProvider(BaseProvider):
    """Yahoo Finance delayed price provider with timeout + retry."""
    
    def __init__(self, timeout: int = DEFAULT_TIMEOUT_SECONDS):
        super().__init__(api_key=None, timeout=timeout)
        self.available = False
        
        try:
            import yfinance
            self.yf = yfinance
            self.available = True
            logger.info("[yfinance] Initialized (no API key required)")
        except ImportError:
            logger.error("[yfinance] yfinance not installed")
    
    def get_price(self, ticker: str) -> Optional[PriceResult]:
        """
        Get delayed quote from Yahoo Finance.
        Guarded by SIGALRM timeout + exponential-backoff retries.
        """
        if not self.available:
            logger.warning("[yfinance] Library not available")
            return None
        
        def _fetch():
            with _timeout_ctx(self.timeout):
                ticker_obj = self.yf.Ticker(ticker)
                info = ticker_obj.info
                
                current_price = (
                    info.get("currentPrice") or
                    info.get("regularMarketPrice") or
                    info.get("previousClose")
                )
                
                if not current_price or current_price <= 0:
                    logger.warning(f"[yfinance] Invalid price for {ticker}: {current_price}")
                    return None
                
                volume = info.get("regularMarketVolume") or info.get("volume")
                
                return PriceResult(
                    ticker=ticker,
                    price=current_price,
                    timestamp=datetime.now(),
                    source="yfinance",
                    delay_seconds=900,
                    volume=volume,
                )
        
        return self._retry(_fetch, label=f"get_price({ticker})")
    
    def get_bulk_prices(self, tickers: List[str]) -> dict[str, Optional[PriceResult]]:
        """
        Efficient bulk fetch using yfinance.download().
        Guarded by timeout (2x single to allow for batch).
        """
        if not self.available:
            return {ticker: None for ticker in tickers}
        
        def _fetch():
            with _timeout_ctx(self.timeout * 2):
                data = self.yf.download(
                    tickers=" ".join(tickers),
                    period="1d",
                    progress=False,
                )
                
                results: dict[str, Optional[PriceResult]] = {}
                for t in tickers:
                    try:
                        if len(tickers) == 1:
                            price = data["Close"].iloc[-1]
                            volume = data["Volume"].iloc[-1] if "Volume" in data else None
                        else:
                            price = data["Close"][t].iloc[-1]
                            volume = data["Volume"][t].iloc[-1] if "Volume" in data.columns else None
                        
                        results[t] = PriceResult(
                            ticker=t,
                            price=float(price),
                            timestamp=datetime.now(),
                            source="yfinance",
                            delay_seconds=900,
                            volume=int(volume) if volume and volume > 0 else None,
                        )
                    except Exception as e:
                        logger.warning(f"[yfinance] Failed to parse {t}: {e}")
                        results[t] = None
                return results
        
        result = self._retry(_fetch, label="get_bulk_prices")
        return result if result is not None else {t: None for t in tickers}
    
    def is_available(self) -> bool:
        """Check if yfinance is ready (with timeout guard)."""
        if not self.available:
            return False
        
        def _check():
            with _timeout_ctx(self.timeout):
                ticker = self.yf.Ticker("AAPL")
                price = ticker.info.get("currentPrice") or ticker.info.get("regularMarketPrice")
                return price is not None and price > 0
        
        try:
            return bool(_check())
        except Exception as e:
            logger.debug(f"[yfinance] Availability check failed: {e}")
            return False
