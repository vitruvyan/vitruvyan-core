"""
Finnhub Provider - Real-time quotes
60 requests/minute FREE tier.

Resilience: timeout + exponential-backoff retries inherited from BaseProvider.
"""

import os
from typing import Optional
from datetime import datetime
import logging

from .base_provider import BaseProvider, PriceResult, DEFAULT_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


class FinnhubProvider(BaseProvider):
    """Finnhub real-time price provider with timeout + retry."""
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT_SECONDS):
        super().__init__(api_key=api_key or os.getenv("FINNHUB_API_KEY"), timeout=timeout)
        self.client = None
        
        if self.api_key:
            try:
                import finnhub
                self.client = finnhub.Client(api_key=self.api_key)
                logger.info("[Finnhub] Initialized with API key")
            except ImportError:
                logger.error("[Finnhub] finnhub-python not installed — pip install finnhub-python")
            except Exception as e:
                logger.error(f"[Finnhub] Initialization failed: {e}")
    
    def get_price(self, ticker: str) -> Optional[PriceResult]:
        """
        Get real-time quote from Finnhub with retry + timeout.
        """
        if not self.client:
            logger.warning("[Finnhub] Client not initialized")
            return None
        
        def _fetch():
            quote = self.client.quote(ticker)
            
            current_price = quote.get('c')
            timestamp_unix = quote.get('t')
            
            if not current_price or current_price <= 0:
                logger.warning(f"[Finnhub] Invalid price for {ticker}: {current_price}")
                return None
            
            return PriceResult(
                ticker=ticker,
                price=current_price,
                timestamp=datetime.fromtimestamp(timestamp_unix) if timestamp_unix else datetime.now(),
                source="Finnhub",
                delay_seconds=0,
                volume=None,
            )
        
        return self._retry(_fetch, label=f"get_price({ticker})")
    
    def is_available(self) -> bool:
        """Check if Finnhub client is ready."""
        if not self.client:
            return False
        
        try:
            result = self.client.quote("AAPL")
            return result.get('c', 0) > 0
        except Exception as e:
            logger.debug(f"[Finnhub] Availability check failed: {e}")
            return False
