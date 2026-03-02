"""
Vitruvyan INTAKE — FRED Intake Agent

⚠️  FINANCE DOMAIN ONLY — vitruvyan_core/domains/finance/intake/
    Non deve essere importato da infrastruttura condivisa (oculus_prime/core/agents/).
    Attivabile esclusivamente tramite il plugin della verticale finance.

Media Scope: Federal Reserve Economic Data (via FRED API)
Constraints: NO semantic inference, NO relevance judgment

Compliance: ACCORDO-FONDATIVO-INTAKE-V1.1

Key Principles:
- Extract economic time-series data literally
- Preserve raw reference + hash
- Emit Evidence Pack + event
- NO domain-specific logic (no interpretation of economic indicators)
"""

import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from infrastructure.edge.oculus_prime.core.guardrails import IntakeGuardrails

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

logger = logging.getLogger(__name__)


# Well-known FRED series for auto-discovery
POPULAR_SERIES = {
    "GDP": "Gross Domestic Product",
    "UNRATE": "Unemployment Rate",
    "CPIAUCSL": "Consumer Price Index (All Urban)",
    "FEDFUNDS": "Federal Funds Effective Rate",
    "DGS10": "10-Year Treasury Constant Maturity Rate",
    "DGS2": "2-Year Treasury Constant Maturity Rate",
    "T10Y2Y": "10Y-2Y Treasury Yield Spread",
    "VIXCLS": "CBOE Volatility Index (VIX)",
    "DEXUSEU": "USD/EUR Exchange Rate",
    "M2SL": "M2 Money Stock",
    "PAYEMS": "Total Nonfarm Payrolls",
    "HOUST": "Housing Starts",
    "RETAILSALES": "Advance Retail Sales",
    "INDPRO": "Industrial Production Index",
}


class FREDIntakeAgent:
    """
    Pre-epistemic FRED data acquisition agent.

    Fetches economic time-series from the Federal Reserve Economic Data (FRED)
    API and packages them as Evidence Packs.

    API docs: https://fred.stlouisfed.org/docs/api/fred/

    Responsibilities:
    - Fetch series observations (time-series data points)
    - Fetch series metadata (description, units, frequency)
    - Generate normalized_text with literal data description
    - Create immutable Evidence Pack per series fetch
    - Emit oculus_prime.evidence.created event

    DOES NOT:
    - Interpret economic trends or implications
    - Generate forecasts or analysis
    - Apply domain-specific rules
    """

    AGENT_ID = "fred-intake-v1"
    AGENT_VERSION = "1.0.0"
    FRED_BASE_URL = "https://api.stlouisfed.org/fred"
    DEFAULT_TIMEOUT = 15.0
    MAX_RETRIES = 3
    RETRY_BACKOFF = 1.5
    DEFAULT_OBS_LIMIT = 120  # ~10 years of monthly data

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
            api_key: FRED API key (get one at https://fred.stlouisfed.org/docs/api/api_key.html)
        """
        self.event_emitter = event_emitter
        self.postgres_agent = postgres_agent
        self._api_key = api_key

        if not api_key:
            logger.warning("No FRED API key provided — FREDIntakeAgent will be non-functional")
        if not HTTPX_AVAILABLE:
            logger.warning("httpx not installed — FREDIntakeAgent will be non-functional")

    # =========================================================================
    # Public API
    # =========================================================================

    def ingest_series(
        self,
        series_id: str,
        observation_start: Optional[str] = None,
        observation_end: Optional[str] = None,
        limit: int = DEFAULT_OBS_LIMIT,
        sort_order: str = "desc",
        correlation_id: Optional[str] = None,
    ) -> str:
        """
        Ingest a single FRED time series.

        Args:
            series_id: FRED series ID (e.g. "GDP", "UNRATE", "CPIAUCSL")
            observation_start: Start date (YYYY-MM-DD). Defaults to API default.
            observation_end: End date (YYYY-MM-DD). Defaults to today.
            limit: Maximum observations to fetch
            sort_order: "asc" or "desc"
            correlation_id: Distributed tracing ID

        Returns:
            evidence_id of the created Evidence Pack
        """
        if not self._api_key or not HTTPX_AVAILABLE:
            raise RuntimeError(
                "FRED API key and httpx required. "
                "Set FRED_API_KEY env var and install httpx."
            )

        # Fetch series metadata
        series_info = self._fetch_series_info(series_id)
        if not series_info:
            raise ValueError(f"FRED series '{series_id}' not found or inaccessible")

        # Fetch observations
        observations = self._fetch_observations(
            series_id,
            observation_start=observation_start,
            observation_end=observation_end,
            limit=limit,
            sort_order=sort_order,
        )

        return self._create_evidence_pack(
            series_id=series_id,
            series_info=series_info,
            observations=observations,
            correlation_id=correlation_id,
        )

    def ingest_multiple_series(
        self,
        series_ids: Optional[List[str]] = None,
        correlation_id: Optional[str] = None,
        limit: int = DEFAULT_OBS_LIMIT,
    ) -> List[str]:
        """
        Ingest multiple FRED series.

        Args:
            series_ids: List of FRED series IDs. If None, uses POPULAR_SERIES.
            correlation_id: Distributed tracing ID
            limit: Observations per series

        Returns:
            List of evidence_ids
        """
        if series_ids is None:
            series_ids = list(POPULAR_SERIES.keys())

        evidence_ids: List[str] = []
        for sid in series_ids:
            try:
                eid = self.ingest_series(
                    series_id=sid,
                    limit=limit,
                    correlation_id=correlation_id,
                )
                evidence_ids.append(eid)
            except Exception as e:
                logger.error("Failed to ingest FRED series %s: %s", sid, e)

        logger.info(
            "FRED intake complete: series=%d evidence=%d",
            len(series_ids), len(evidence_ids),
        )
        return evidence_ids

    def search_series(
        self,
        search_text: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search FRED for series matching text.

        Args:
            search_text: Keywords to search
            limit: Max results

        Returns:
            List of series metadata dicts
        """
        return self._fred_request(
            "/series/search",
            params={
                "search_text": search_text,
                "limit": limit,
                "order_by": "popularity",
                "sort_order": "desc",
            },
            result_key="seriess",
        )

    # =========================================================================
    # FRED API methods
    # =========================================================================

    def _fetch_series_info(self, series_id: str) -> Optional[Dict[str, Any]]:
        """Fetch series metadata."""
        results = self._fred_request(
            "/series",
            params={"series_id": series_id},
            result_key="seriess",
        )
        return results[0] if results else None

    def _fetch_observations(
        self,
        series_id: str,
        observation_start: Optional[str] = None,
        observation_end: Optional[str] = None,
        limit: int = DEFAULT_OBS_LIMIT,
        sort_order: str = "desc",
    ) -> List[Dict[str, Any]]:
        """Fetch time-series observations."""
        params: Dict[str, Any] = {
            "series_id": series_id,
            "limit": limit,
            "sort_order": sort_order,
        }
        if observation_start:
            params["observation_start"] = observation_start
        if observation_end:
            params["observation_end"] = observation_end

        return self._fred_request(
            "/series/observations",
            params=params,
            result_key="observations",
        )

    def _fred_request(
        self,
        endpoint: str,
        params: Dict[str, Any],
        result_key: str,
    ) -> List[Dict[str, Any]]:
        """Make a FRED API request with retry."""
        url = f"{self.FRED_BASE_URL}{endpoint}"
        params["api_key"] = self._api_key
        params["file_type"] = "json"

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                with httpx.Client(timeout=self.DEFAULT_TIMEOUT) as client:
                    resp = client.get(url, params=params)

                    if resp.status_code == 429:
                        wait = float(resp.headers.get("Retry-After", self.RETRY_BACKOFF ** attempt))
                        logger.warning("FRED 429 rate-limit; waiting %.1fs (attempt %d)", wait, attempt)
                        time.sleep(wait)
                        continue

                    resp.raise_for_status()
                    data = resp.json()
                    return data.get(result_key, [])

            except httpx.TimeoutException:
                logger.warning("FRED API timeout (attempt %d/%d)", attempt, self.MAX_RETRIES)
                time.sleep(self.RETRY_BACKOFF ** attempt)
            except Exception as e:
                logger.error("FRED API error on %s: %s", endpoint, e)
                if attempt == self.MAX_RETRIES:
                    break
                time.sleep(self.RETRY_BACKOFF ** attempt)

        return []

    # =========================================================================
    # Evidence Pack creation
    # =========================================================================

    def _create_evidence_pack(
        self,
        series_id: str,
        series_info: Dict[str, Any],
        observations: List[Dict[str, Any]],
        correlation_id: Optional[str],
    ) -> str:
        """Build and emit Evidence Pack from FRED series data."""
        evidence_id = self._generate_evidence_id()

        title = series_info.get("title", series_id)
        units = series_info.get("units", "")
        frequency = series_info.get("frequency", "")
        notes = (series_info.get("notes") or "")[:2000]

        # Clean observation values (FRED uses "." for missing)
        clean_obs = []
        for obs in observations:
            val = obs.get("value", ".")
            if val != ".":
                clean_obs.append({
                    "date": obs.get("date"),
                    "value": val,
                })

        # Build normalized text (literal description, no interpretation)
        latest_obs = clean_obs[0] if clean_obs else None
        obs_summary = ""
        for obs in clean_obs[:10]:
            obs_summary += f"  {obs['date']}: {obs['value']}\n"

        normalized_text = (
            f"Series: {series_id} — {title}\n"
            f"Units: {units}\n"
            f"Frequency: {frequency}\n"
            f"Observations: {len(clean_obs)} data points\n"
            f"Latest: {latest_obs['date']} = {latest_obs['value']}\n" if latest_obs else ""
            f"---\nRecent observations:\n{obs_summary}"
            f"---\nNotes: {notes[:500]}"
        )

        source_hash = self._compute_hash(normalized_text)
        source_uri = f"fred://{series_id}"

        raw_data = {
            "series_id": series_id,
            "title": title,
            "units": units,
            "frequency": frequency,
            "seasonal_adjustment": series_info.get("seasonal_adjustment", ""),
            "last_updated": series_info.get("last_updated", ""),
            "observation_count": len(clean_obs),
            "observations": clean_obs[:self.DEFAULT_OBS_LIMIT],
            "notes": notes,
        }

        evidence_pack = {
            "evidence_id": evidence_id,
            "chunk_id": "CHK-0",
            "schema_version": "1.0.0",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "source_ref": {
                "source_type": "document",
                "source_uri": source_uri,
                "source_hash": source_hash,
                "mime_type": "application/json",
                "byte_size": len(json.dumps(raw_data).encode("utf-8")),
            },
            "normalized_text": normalized_text,
            "technical_metadata": {
                "extraction_method": "fred_api",
                "extraction_version": self.AGENT_VERSION,
                "language_detected": "en",
                "confidence_score": 1.0,
                "chunk_position": {
                    "start_offset": 0,
                    "end_offset": len(normalized_text),
                    "total_chunks": 1,
                },
                "fred_metadata": raw_data,
            },
            "integrity": {
                "evidence_hash": self._compute_evidence_hash(
                    evidence_id, "CHK-0", normalized_text, source_hash
                ),
                "immutable": True,
            },
            "sampling_policy_ref": None,
            "tags": ["fred", f"series:{series_id}", f"frequency:{frequency.lower()}"],
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
            source_uri=source_uri,
            evidence_pack_ref=evidence_pack_ref,
            source_hash=source_hash,
            intake_agent_id=self.AGENT_ID,
            intake_agent_version=self.AGENT_VERSION,
            byte_size=len(json.dumps(raw_data).encode("utf-8")),
            language_detected="en",
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
