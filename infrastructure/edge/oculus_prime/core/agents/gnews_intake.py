"""
Vitruvyan INTAKE — Google News Intake Agent

Media Scope: News article metadata and summaries (via GNews API / feedparser)
Constraints: NO semantic inference, NO relevance judgment

Compliance: ACCORDO-FONDATIVO-INTAKE-V1.1

Key Principles:
- Extract text literally (descriptive, not interpretative)
- Preserve raw reference + hash
- Emit Evidence Pack + event
- NO domain-specific logic
"""

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from infrastructure.edge.oculus_prime.core.guardrails import IntakeGuardrails

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False

logger = logging.getLogger(__name__)


class GNewsIntakeAgent:
    """
    Pre-epistemic Google News acquisition agent.

    Two modes:
    1. **GNews API** (preferred): REST API with JSON responses, requires API key.
       Endpoint: https://gnews.io/api/v4/
    2. **RSS Fallback**: Google News RSS feed via feedparser (no API key needed,
       less structured).

    Responsibilities:
    - Fetch news articles by query or topic
    - Generate normalized_text (headline + description, literal only)
    - Create immutable Evidence Pack per article
    - Emit oculus_prime.evidence.created event

    DOES NOT:
    - Interpret content semantically
    - Evaluate relevance or importance
    - Apply domain-specific rules
    """

    AGENT_ID = "gnews-intake-v1"
    AGENT_VERSION = "1.0.0"
    GNEWS_BASE_URL = "https://gnews.io/api/v4"
    GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"
    DEFAULT_LIMIT = 10
    DEFAULT_TIMEOUT = 15.0
    MAX_RETRIES = 3
    RETRY_BACKOFF = 1.5

    def __init__(
        self,
        event_emitter,
        postgres_agent=None,
        api_key: str = "",
    ):
        """
        Args:
            event_emitter: IntakeEventEmitter instance
            postgres_agent: PostgresAgent for Evidence Pack persistence
            api_key: GNews.io API key (leave empty for RSS fallback)
        """
        self.event_emitter = event_emitter
        self.postgres_agent = postgres_agent
        self._api_key = api_key
        self._mode = "api" if api_key else "rss"

        if self._mode == "rss" and not FEEDPARSER_AVAILABLE:
            logger.warning("feedparser not installed; RSS fallback unavailable")
        if self._mode == "api" and not HTTPX_AVAILABLE:
            logger.warning("httpx not installed; GNews API mode unavailable")

    # =========================================================================
    # Public API
    # =========================================================================

    def ingest_search(
        self,
        query: str,
        language: str = "en",
        country: str = "us",
        limit: int = DEFAULT_LIMIT,
        correlation_id: Optional[str] = None,
    ) -> List[str]:
        """
        Ingest news articles matching a search query.

        Args:
            query: Search query string
            language: Language code (en, it, de, fr, es, ...)
            country: Country code (us, it, de, gb, ...)
            limit: Max articles to fetch (GNews API max 100)
            correlation_id: Distributed tracing ID

        Returns:
            List of evidence_ids created
        """
        if self._mode == "api":
            articles = self._fetch_gnews_api(query, language, country, limit)
        else:
            articles = self._fetch_rss(query, language)

        evidence_ids: List[str] = []
        for article in articles[:limit]:
            try:
                eid = self._ingest_article(
                    article, query=query, correlation_id=correlation_id
                )
                evidence_ids.append(eid)
            except Exception as e:
                logger.error("Failed to ingest article: %s — %s", article.get("title", "?"), e)

        logger.info(
            "GNews intake complete: query='%s' mode=%s articles=%d evidence=%d",
            query, self._mode, len(articles), len(evidence_ids),
        )
        return evidence_ids

    def ingest_top_headlines(
        self,
        topic: str = "general",
        language: str = "en",
        country: str = "us",
        limit: int = DEFAULT_LIMIT,
        correlation_id: Optional[str] = None,
    ) -> List[str]:
        """
        Ingest top headlines by topic (GNews API only).

        Valid topics: general, world, nation, business, technology, entertainment,
                      sports, science, health.
        """
        if self._mode != "api":
            logger.warning("Top headlines requires GNews API key; falling back to RSS search")
            return self.ingest_search(topic, language, country, limit, correlation_id)

        articles = self._fetch_gnews_top(topic, language, country, limit)
        evidence_ids: List[str] = []
        for article in articles[:limit]:
            try:
                eid = self._ingest_article(
                    article, query=f"topic:{topic}", correlation_id=correlation_id
                )
                evidence_ids.append(eid)
            except Exception as e:
                logger.error("Failed to ingest headline: %s", e)

        return evidence_ids

    # =========================================================================
    # Fetch methods
    # =========================================================================

    def _fetch_gnews_api(
        self, query: str, language: str, country: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch articles from GNews.io API."""
        if not HTTPX_AVAILABLE:
            raise RuntimeError("httpx required for GNews API mode")

        import time
        url = f"{self.GNEWS_BASE_URL}/search"
        params = {
            "q": query,
            "lang": language,
            "country": country,
            "max": min(limit, 100),
            "apikey": self._api_key,
        }

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                with httpx.Client(timeout=self.DEFAULT_TIMEOUT) as client:
                    resp = client.get(url, params=params)

                    if resp.status_code == 429:
                        wait = float(resp.headers.get("Retry-After", self.RETRY_BACKOFF ** attempt))
                        logger.warning("GNews 429 rate-limit; waiting %.1fs (attempt %d)", wait, attempt)
                        time.sleep(wait)
                        continue

                    resp.raise_for_status()
                    data = resp.json()
                    return data.get("articles", [])

            except httpx.TimeoutException:
                logger.warning("GNews API timeout (attempt %d/%d)", attempt, self.MAX_RETRIES)
                time.sleep(self.RETRY_BACKOFF ** attempt)
            except Exception as e:
                logger.error("GNews API error: %s", e)
                break

        return []

    def _fetch_gnews_top(
        self, topic: str, language: str, country: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch top headlines by topic from GNews.io API."""
        if not HTTPX_AVAILABLE:
            raise RuntimeError("httpx required for GNews API mode")

        import time
        url = f"{self.GNEWS_BASE_URL}/top-headlines"
        params = {
            "topic": topic,
            "lang": language,
            "country": country,
            "max": min(limit, 100),
            "apikey": self._api_key,
        }

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                with httpx.Client(timeout=self.DEFAULT_TIMEOUT) as client:
                    resp = client.get(url, params=params)
                    if resp.status_code == 429:
                        wait = float(resp.headers.get("Retry-After", self.RETRY_BACKOFF ** attempt))
                        logger.warning("GNews 429; waiting %.1fs", wait)
                        time.sleep(wait)
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    return data.get("articles", [])
            except httpx.TimeoutException:
                logger.warning("GNews API timeout (attempt %d/%d)", attempt, self.MAX_RETRIES)
                time.sleep(self.RETRY_BACKOFF ** attempt)
            except Exception as e:
                logger.error("GNews top headlines error: %s", e)
                break

        return []

    def _fetch_rss(self, query: str, language: str) -> List[Dict[str, Any]]:
        """Fetch articles from Google News RSS (no API key needed)."""
        if not FEEDPARSER_AVAILABLE:
            raise RuntimeError("feedparser required for RSS mode — pip install feedparser>=6.0")

        url = f"{self.GOOGLE_NEWS_RSS}?q={quote_plus(query)}&hl={language}"
        feed = feedparser.parse(url)

        articles = []
        for entry in feed.entries:
            articles.append({
                "title": entry.get("title", ""),
                "description": entry.get("summary", ""),
                "url": entry.get("link", ""),
                "publishedAt": entry.get("published", ""),
                "source": {"name": entry.get("source", {}).get("title", "Google News RSS")},
                "content": entry.get("summary", ""),
            })
        return articles

    # =========================================================================
    # Ingestion
    # =========================================================================

    def _ingest_article(
        self,
        article: Dict[str, Any],
        query: str,
        correlation_id: Optional[str],
    ) -> str:
        """Create Evidence Pack from a news article."""
        evidence_id = self._generate_evidence_id()

        title = article.get("title", "")
        description = article.get("description", "") or article.get("content", "")
        source_name = (article.get("source") or {}).get("name", "unknown")
        url = article.get("url", "")
        published = article.get("publishedAt", "")
        image_url = article.get("image", "")

        # Build normalized text (literal, no interpretation)
        normalized_text = (
            f"Title: {title}\n"
            f"Source: {source_name}\n"
            f"Published: {published}\n"
            f"---\n{description[:4000]}"
        )
        source_hash = self._compute_hash(normalized_text)

        raw_data = {
            "title": title,
            "description": description[:4000],
            "url": url,
            "source_name": source_name,
            "published_at": published,
            "image_url": image_url,
            "query": query,
        }

        evidence_pack = {
            "evidence_id": evidence_id,
            "chunk_id": "CHK-0",
            "schema_version": "1.0.0",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "source_ref": {
                "source_type": "document",
                "source_uri": url or f"gnews://search/{quote_plus(query)}",
                "source_hash": source_hash,
                "mime_type": "text/plain",
                "byte_size": len(normalized_text.encode("utf-8")),
            },
            "normalized_text": normalized_text,
            "technical_metadata": {
                "extraction_method": f"gnews_{self._mode}",
                "extraction_version": self.AGENT_VERSION,
                "language_detected": None,
                "confidence_score": 0.9 if self._mode == "api" else 0.7,
                "chunk_position": {
                    "start_offset": 0,
                    "end_offset": len(normalized_text),
                    "total_chunks": 1,
                },
                "gnews_metadata": raw_data,
            },
            "integrity": {
                "evidence_hash": self._compute_evidence_hash(
                    evidence_id, "CHK-0", normalized_text, source_hash
                ),
                "immutable": True,
            },
            "sampling_policy_ref": None,
            "tags": ["gnews", f"source:{source_name}", f"query:{query[:50]}"],
        }

        # Guardrails
        IntakeGuardrails.validate_no_semantics(normalized_text, "document")
        IntakeGuardrails.validate_source_hash_required(evidence_pack["source_ref"])

        # Persist
        evidence_pack_ref = self._persist_evidence_pack(evidence_pack)

        # Emit event
        self.event_emitter.emit_evidence_created(
            evidence_id=evidence_id,
            chunk_id="CHK-0",
            source_type="document",
            source_uri=url or f"gnews://search/{quote_plus(query)}",
            evidence_pack_ref=evidence_pack_ref,
            source_hash=source_hash,
            intake_agent_id=self.AGENT_ID,
            intake_agent_version=self.AGENT_VERSION,
            byte_size=len(normalized_text.encode("utf-8")),
            language_detected=None,
            correlation_id=correlation_id,
        )

        return evidence_id

    # =========================================================================
    # Helpers
    # =========================================================================

    @staticmethod
    def _generate_evidence_id() -> str:
        return f"EVD-{str(uuid.uuid4()).upper()}"

    @staticmethod
    def _compute_hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _compute_evidence_hash(
        evidence_id: str, chunk_id: str, text: str, source_hash: str
    ) -> str:
        composite = f"{evidence_id}{chunk_id}{text[:500]}{source_hash}"
        return hashlib.sha256(composite.encode("utf-8")).hexdigest()

    def _persist_evidence_pack(self, pack: Dict[str, Any]) -> str:
        """Persist Evidence Pack to PostgreSQL (append-only)."""
        ref = f"evidence_packs/{pack['evidence_id']}"
        if self.postgres_agent:
            try:
                self.postgres_agent.execute(
                    """INSERT INTO oculus_evidence_packs (evidence_id, chunk_id, pack_json, created_at)
                       VALUES (%s, %s, %s, NOW())
                       ON CONFLICT (evidence_id, chunk_id) DO NOTHING""",
                    (pack["evidence_id"], pack["chunk_id"], json.dumps(pack)),
                )
            except Exception as e:
                logger.warning("Evidence pack persistence failed: %s", e)
        return ref
