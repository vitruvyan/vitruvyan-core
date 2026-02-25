"""
Price Aggregator - Multi-Provider Intelligent Routing
Portfolio Architects - Task 9

Architecture:
- Tier-based routing (real-time vs delayed)
- Automatic fallback cascade
- Redis caching with TTL
- Quota management
"""

import os
import redis
import json
from typing import Optional, List, Literal
from datetime import datetime, timedelta
import logging

from .providers import BaseProvider, PriceResult, FinnhubProvider, YFinanceProvider

logger = logging.getLogger(__name__)

UseCaseType = Literal["autopilot", "construction", "ui"]


class PriceAggregator:
    """
    Multi-provider price aggregator with intelligent routing
    
    Use Cases:
    - autopilot: Real-time prices critical (Finnhub)
    - construction: Delayed OK (yfinance bulk)
    - ui: Cached delayed (yfinance with 5 min cache)
    """
    
    # Provider tier configuration
    PROVIDER_TIERS = {
        "realtime": ["finnhub"],     # For Autopilot
        "delayed": ["yfinance"]       # For UI/construction
    }
    
    # Cache TTL by use case (seconds)
    CACHE_TTL = {
        "autopilot": 60,        # 1 minute (real-time critical)
        "construction": 300,    # 5 minutes (daily operation)
        "ui": 300               # 5 minutes (display)
    }
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize aggregator with available providers
        
        Args:
            redis_client: Redis client for caching (optional)
        """
        self.redis = redis_client
        
        # Initialize available providers
        self.providers = {
            "finnhub": FinnhubProvider(),
            "yfinance": YFinanceProvider()
        }
        
        # Check provider availability
        self.available_providers = {
            name: provider 
            for name, provider in self.providers.items() 
            if provider.is_available()
        }
        
        if not self.available_providers:
            logger.error("[PriceAggregator] NO PROVIDERS AVAILABLE!")
        else:
            logger.info(
                f"[PriceAggregator] Initialized with providers: "
                f"{', '.join(self.available_providers.keys())}"
            )
    
    def get_price(
        self, 
        ticker: str, 
        use_case: UseCaseType = "ui"
    ) -> Optional[PriceResult]:
        """
        Get price with intelligent provider selection
        
        Args:
            ticker: Stock symbol (e.g., "AAPL")
            use_case: "autopilot" (real-time), "construction", or "ui"
        
        Returns:
            PriceResult or None if all providers failed
        """
        # Step 1: Check Redis cache
        cached = self._get_cached_price(ticker, use_case)
        if cached:
            logger.debug(f"[PriceAggregator] Cache HIT for {ticker} ({use_case})")
            return cached
        
        # Step 2: Select provider tier
        if use_case == "autopilot":
            tier = "realtime"
        else:
            tier = "delayed"
        
        # Step 3: Try providers in tier order
        provider_names = self.PROVIDER_TIERS[tier]
        
        for provider_name in provider_names:
            provider = self.available_providers.get(provider_name)
            if not provider:
                logger.debug(f"[PriceAggregator] Provider {provider_name} not available")
                continue
            
            try:
                result = provider.get_price(ticker)
                
                if result:
                    logger.info(
                        f"[PriceAggregator] {ticker} fetched from {provider_name} "
                        f"(${result.price:.2f}, delay={result.delay_seconds}s)"
                    )
                    
                    # Cache the result
                    self._cache_price(ticker, result, use_case)
                    
                    return result
                
            except Exception as e:
                logger.warning(f"[PriceAggregator] {provider_name} failed for {ticker}: {e}")
                continue
        
        # Step 4: All providers failed - try fallback to opposite tier
        logger.warning(f"[PriceAggregator] Primary tier failed for {ticker}, trying fallback")
        
        fallback_tier = "delayed" if tier == "realtime" else "realtime"
        for provider_name in self.PROVIDER_TIERS[fallback_tier]:
            provider = self.available_providers.get(provider_name)
            if provider:
                try:
                    result = provider.get_price(ticker)
                    if result:
                        logger.info(f"[PriceAggregator] Fallback success: {provider_name}")
                        self._cache_price(ticker, result, use_case)
                        return result
                except Exception:
                    continue
        
        logger.error(f"[PriceAggregator] ALL PROVIDERS FAILED for {ticker}")
        return None
    
    def get_bulk_prices(
        self,
        tickers: List[str],
        use_case: UseCaseType = "construction"
    ) -> dict[str, Optional[PriceResult]]:
        """
        Get prices for multiple tickers efficiently
        
        Args:
            tickers: List of stock symbols
            use_case: Routing strategy
        
        Returns:
            Dict mapping ticker to PriceResult
        """
        results = {}
        uncached_tickers = []
        
        # Step 1: Check cache for all tickers
        for ticker in tickers:
            cached = self._get_cached_price(ticker, use_case)
            if cached:
                results[ticker] = cached
            else:
                uncached_tickers.append(ticker)
        
        if not uncached_tickers:
            logger.info(f"[PriceAggregator] All {len(tickers)} tickers from cache")
            return results
        
        logger.info(
            f"[PriceAggregator] Bulk fetch: {len(uncached_tickers)}/{len(tickers)} "
            f"not cached"
        )
        
        # Step 2: Use yfinance for efficient bulk fetch
        yfinance_provider = self.available_providers.get("yfinance")
        
        if yfinance_provider:
            bulk_results = yfinance_provider.get_bulk_prices(uncached_tickers)
            
            for ticker, result in bulk_results.items():
                if result:
                    results[ticker] = result
                    self._cache_price(ticker, result, use_case)
                else:
                    results[ticker] = None
        else:
            # Fallback: Sequential fetch with available providers
            logger.warning("[PriceAggregator] yfinance unavailable, sequential fetch")
            for ticker in uncached_tickers:
                results[ticker] = self.get_price(ticker, use_case)
        
        return results
    
    def _get_cached_price(
        self, 
        ticker: str, 
        use_case: UseCaseType
    ) -> Optional[PriceResult]:
        """Retrieve price from Redis cache if valid"""
        if not self.redis:
            return None
        
        try:
            cache_key = f"price:{ticker}:{use_case}"
            cached_data = self.redis.get(cache_key)
            
            if not cached_data:
                return None
            
            data = json.loads(cached_data)
            
            # Reconstruct PriceResult
            return PriceResult(
                ticker=data["ticker"],
                price=data["price"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
                source=data["source"],
                delay_seconds=data["delay_seconds"],
                volume=data.get("volume")
            )
        
        except Exception as e:
            logger.debug(f"[PriceAggregator] Cache read error: {e}")
            return None
    
    def _cache_price(
        self, 
        ticker: str, 
        result: PriceResult, 
        use_case: UseCaseType
    ):
        """Store price in Redis cache with TTL"""
        if not self.redis:
            return
        
        try:
            cache_key = f"price:{ticker}:{use_case}"
            ttl = self.CACHE_TTL[use_case]
            
            data = {
                "ticker": result.ticker,
                "price": result.price,
                "timestamp": result.timestamp.isoformat(),
                "source": result.source,
                "delay_seconds": result.delay_seconds,
                "volume": result.volume
            }
            
            self.redis.setex(cache_key, ttl, json.dumps(data))
            logger.debug(f"[PriceAggregator] Cached {ticker} (TTL={ttl}s)")
        
        except Exception as e:
            logger.warning(f"[PriceAggregator] Cache write error: {e}")
    
    def clear_cache(self, ticker: Optional[str] = None):
        """Clear Redis cache (all tickers or specific)"""
        if not self.redis:
            return
        
        try:
            if ticker:
                pattern = f"price:{ticker}:*"
            else:
                pattern = "price:*"
            
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
                logger.info(f"[PriceAggregator] Cleared {len(keys)} cache entries")
        
        except Exception as e:
            logger.error(f"[PriceAggregator] Cache clear error: {e}")
