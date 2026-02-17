"""
API Intake Agent — Versatile external API data acquisition.

AEGIS INTAKE LAYER — PHASE 2.5
Date: January 12, 2026

Architecture:
    Universal API fetcher with registry pattern for extensibility.
    Supports ANY external API with standardized Evidence Pack creation.

Design Principles:
    1. Abstract base class for all API fetchers
    2. Registry pattern for dynamic fetcher registration
    3. Configuration-driven (API endpoints, auth, parameters)
    4. Evidence Pack creation with standardized metadata
    5. Error handling with retry logic and exponential backoff

Supported APIs (extensible):
    - INGV Seismic Events (https://webservices.ingv.it/fdsnws/event/1/query)
    - DPC Criticality Bulletins (GitHub API)
    - Weather APIs (OpenWeatherMap, MeteoAM) - future
    - Traffic APIs (Google Maps, HERE) - future
    - Any REST API with JSON/XML/CSV response

Usage:
    # Initialize agent
    agent = APIIntakeAgent()
    
    # Fetch INGV seismic data
    evidence_id = agent.fetch_and_persist(
        fetcher_name="ingv_seismic",
        params={"bbox": [40.75, 14.05, 40.90, 14.25], "start_date": "2024-01-01"},
        scenario_name="campi_flegrei_baseline"
    )
    
    # Register custom fetcher
    agent.register_fetcher("custom_api", CustomAPIFetcher())
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from uuid import uuid4
from datetime import datetime, timedelta
import logging
import time
import json
import hashlib

# HTTP client
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logging.warning("httpx not available (pip install httpx)")

# PostgreSQL agent
try:
    from vitruvyan_core.core.agents.postgres_agent import PostgresAgent
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    logging.warning("PostgresAgent not available")


logger = logging.getLogger(__name__)


# =====================================================================
# Configuration Data Structures
# =====================================================================

@dataclass
class APIConfig:
    """
    Configuration for an API endpoint.
    
    Attributes:
        name: API identifier (e.g., "ingv_seismic")
        base_url: API base URL (e.g., "https://webservices.ingv.it")
        endpoint: API endpoint path (e.g., "/fdsnws/event/1/query")
        method: HTTP method (GET, POST)
        auth_type: Authentication type ("none", "bearer", "api_key", "basic")
        auth_credentials: Authentication credentials (token, API key, username/password)
        timeout: Request timeout (seconds)
        max_retries: Maximum retry attempts
        retry_backoff: Exponential backoff multiplier
        headers: Custom HTTP headers
        response_format: Expected response format ("json", "xml", "csv", "text")
    """
    name: str
    base_url: str
    endpoint: str
    method: str = "GET"
    auth_type: str = "none"
    auth_credentials: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    max_retries: int = 3
    retry_backoff: float = 2.0
    headers: Dict[str, str] = field(default_factory=dict)
    response_format: str = "json"
    
    def get_full_url(self) -> str:
        """Construct full URL from base_url + endpoint"""
        return f"{self.base_url.rstrip('/')}/{self.endpoint.lstrip('/')}"


@dataclass
class APIResponse:
    """
    Standardized API response wrapper.
    
    Attributes:
        success: Whether API call succeeded
        data: Parsed response data
        raw_response: Raw response text
        status_code: HTTP status code
        error_message: Error message (if failed)
        metadata: Additional metadata (headers, timing, etc.)
    """
    success: bool
    data: Optional[Dict[str, Any]] = None
    raw_response: Optional[str] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# =====================================================================
# Abstract Base Class for API Fetchers
# =====================================================================

class AbstractAPIFetcher(ABC):
    """
    Abstract base class for all API fetchers.
    
    All concrete fetchers MUST implement:
        - get_config(): Return APIConfig for this fetcher
        - build_params(): Build query parameters from input
        - parse_response(): Parse API response to standardized format
        - create_evidence_metadata(): Create Evidence Pack metadata
    
    Example:
        class CustomAPIFetcher(AbstractAPIFetcher):
            def get_config(self) -> APIConfig:
                return APIConfig(name="custom_api", base_url="https://api.custom.com", ...)
            
            def build_params(self, **kwargs) -> Dict[str, Any]:
                return {"param1": kwargs["value1"], ...}
            
            def parse_response(self, response: APIResponse) -> Dict[str, Any]:
                return {"extracted_key": response.data["key"], ...}
            
            def create_evidence_metadata(self, parsed_data: Dict, params: Dict) -> Dict:
                return {"source_type": "custom_api", "date_range": params["date"], ...}
    """
    
    @abstractmethod
    def get_config(self) -> APIConfig:
        """Return API configuration for this fetcher"""
        pass
    
    @abstractmethod
    def build_params(self, **kwargs) -> Dict[str, Any]:
        """
        Build query parameters from input arguments.
        
        Args:
            **kwargs: User-provided parameters
        
        Returns:
            Dict of query parameters for API request
        
        Example:
            bbox = kwargs["bbox"]  # [40.75, 14.05, 40.90, 14.25]
            return {
                "minlatitude": bbox[0],
                "minlongitude": bbox[1],
                "maxlatitude": bbox[2],
                "maxlongitude": bbox[3]
            }
        """
        pass
    
    @abstractmethod
    def parse_response(self, response: APIResponse) -> Dict[str, Any]:
        """
        Parse API response to standardized format.
        
        Args:
            response: Raw API response wrapper
        
        Returns:
            Dict with parsed data (keys depend on API type)
        
        Example:
            events = response.data["events"]
            return {
                "event_count": len(events),
                "max_magnitude": max(e["magnitude"] for e in events),
                "events": events
            }
        """
        pass
    
    @abstractmethod
    def create_evidence_metadata(
        self,
        parsed_data: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create Evidence Pack metadata from parsed data.
        
        Args:
            parsed_data: Parsed API response
            params: Original query parameters
        
        Returns:
            Dict with Evidence Pack metadata (source_type, date_range, etc.)
        
        Example:
            return {
                "source_type": "ingv_seismic",
                "date_range": f"{params['start_date']} to {params['end_date']}",
                "event_count": parsed_data["event_count"],
                "max_magnitude": parsed_data["max_magnitude"]
            }
        """
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate query parameters (optional override).
        
        Args:
            params: Query parameters to validate
        
        Returns:
            Tuple (is_valid, error_message)
        
        Example:
            if "bbox" not in params:
                return False, "Missing required parameter: bbox"
            if len(params["bbox"]) != 4:
                return False, "bbox must have 4 values [min_lat, min_lon, max_lat, max_lon]"
            return True, ""
        """
        return True, ""


# =====================================================================
# Concrete Fetcher: INGV Seismic Events
# =====================================================================

class INGVSeismicFetcher(AbstractAPIFetcher):
    """
    INGV (Istituto Nazionale di Geofisica e Vulcanologia) seismic events API.
    
    API Documentation:
        https://webservices.ingv.it/fdsnws/event/1/
        Swagger: https://webservices.ingv.it/swagger-ui/dist/?url=https://ingv.github.io/openapi/fdsnws/event/0.0.1/event.yaml
    
    Query Parameters:
        - minlatitude, maxlatitude, minlongitude, maxlongitude (bounding box)
        - starttime, endtime (ISO 8601 timestamps)
        - minmagnitude, maxmagnitude
        - mindepth, maxdepth (km)
        - format (xml, text, json)
    
    Response Format:
        JSON with list of seismic events (magnitude, depth, lat/lon, time)
    
    Example Usage:
        fetcher = INGVSeismicFetcher()
        params = fetcher.build_params(
            bbox=[40.75, 14.05, 40.90, 14.25],
            start_date="2024-01-01T00:00:00",
            end_date="2024-12-31T23:59:59",
            min_magnitude=2.0
        )
    """
    
    def get_config(self) -> APIConfig:
        return APIConfig(
            name="ingv_seismic",
            base_url="https://webservices.ingv.it",
            endpoint="/fdsnws/event/1/query",
            method="GET",
            auth_type="none",
            timeout=60,  # Longer timeout for large datasets
            max_retries=3,
            retry_backoff=2.0,
            headers={"Accept": "application/json"},
            response_format="json"
        )
    
    def build_params(self, **kwargs) -> Dict[str, Any]:
        """
        Build INGV API query parameters.
        
        Args:
            bbox: List[float] — [min_lat, min_lon, max_lat, max_lon]
            start_date: str — ISO 8601 timestamp (e.g., "2024-01-01T00:00:00")
            end_date: str — ISO 8601 timestamp
            min_magnitude: float — Minimum magnitude (optional, default 0.0)
            max_magnitude: float — Maximum magnitude (optional)
            min_depth: float — Minimum depth in km (optional)
            max_depth: float — Maximum depth in km (optional)
        
        Returns:
            Dict of INGV API query parameters
        """
        bbox = kwargs.get("bbox")
        if not bbox or len(bbox) != 4:
            raise ValueError("bbox must be [min_lat, min_lon, max_lat, max_lon]")
        
        params = {
            "minlatitude": bbox[0],
            "minlongitude": bbox[1],
            "maxlatitude": bbox[2],
            "maxlongitude": bbox[3],
            "starttime": kwargs.get("start_date", "2024-01-01T00:00:00"),
            "endtime": kwargs.get("end_date", datetime.utcnow().isoformat()),
            "format": "json"
        }
        
        # Optional parameters
        if "min_magnitude" in kwargs:
            params["minmagnitude"] = kwargs["min_magnitude"]
        if "max_magnitude" in kwargs:
            params["maxmagnitude"] = kwargs["max_magnitude"]
        if "min_depth" in kwargs:
            params["mindepth"] = kwargs["min_depth"]
        if "max_depth" in kwargs:
            params["maxdepth"] = kwargs["max_depth"]
        
        return params
    
    def parse_response(self, response: APIResponse) -> Dict[str, Any]:
        """
        Parse INGV API response.
        
        Returns:
            {
                "event_count": int,
                "max_magnitude": float,
                "min_magnitude": float,
                "avg_magnitude": float,
                "max_depth_km": float,
                "min_depth_km": float,
                "avg_depth_km": float,
                "events": List[Dict] (full event data)
            }
        """
        if not response.success or not response.data:
            return {
                "event_count": 0,
                "max_magnitude": 0.0,
                "avg_magnitude": 0.0,
                "avg_depth_km": 0.0,
                "events": []
            }
        
        # INGV JSON format: {"features": [{"properties": {"mag": X, "depth": Y}, "geometry": {...}}, ...]}
        events = response.data.get("features", [])
        
        if not events:
            return {
                "event_count": 0,
                "max_magnitude": 0.0,
                "avg_magnitude": 0.0,
                "avg_depth_km": 0.0,
                "events": []
            }
        
        magnitudes = [e["properties"]["mag"] for e in events if e["properties"].get("mag")]
        depths = [e["properties"]["depth"] for e in events if e["properties"].get("depth")]
        
        return {
            "event_count": len(events),
            "max_magnitude": max(magnitudes) if magnitudes else 0.0,
            "min_magnitude": min(magnitudes) if magnitudes else 0.0,
            "avg_magnitude": sum(magnitudes) / len(magnitudes) if magnitudes else 0.0,
            "max_depth_km": max(depths) if depths else 0.0,
            "min_depth_km": min(depths) if depths else 0.0,
            "avg_depth_km": sum(depths) / len(depths) if depths else 0.0,
            "events": events
        }
    
    def create_evidence_metadata(
        self,
        parsed_data: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create Evidence Pack metadata for INGV seismic data"""
        return {
            "source_type": "ingv_seismic",
            "api_endpoint": "https://webservices.ingv.it/fdsnws/event/1/query",
            "date_range": f"{params.get('starttime')} to {params.get('endtime')}",
            "bounding_box": [
                params.get("minlatitude"),
                params.get("minlongitude"),
                params.get("maxlatitude"),
                params.get("maxlongitude")
            ],
            "event_count": parsed_data["event_count"],
            "max_magnitude": parsed_data["max_magnitude"],
            "avg_magnitude": parsed_data["avg_magnitude"],
            "avg_depth_km": parsed_data["avg_depth_km"]
        }
    
    def validate_params(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate INGV query parameters"""
        # Check bbox
        if "bbox" not in params:
            return False, "Missing required parameter: bbox"
        
        bbox = params["bbox"]
        if len(bbox) != 4:
            return False, "bbox must have 4 values [min_lat, min_lon, max_lat, max_lon]"
        
        # Validate lat/lon ranges
        if not (-90 <= bbox[0] <= 90) or not (-90 <= bbox[2] <= 90):
            return False, "Latitude must be between -90 and 90"
        
        if not (-180 <= bbox[1] <= 180) or not (-180 <= bbox[3] <= 180):
            return False, "Longitude must be between -180 and 180"
        
        if bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
            return False, "Invalid bbox: min values must be < max values"
        
        return True, ""


# =====================================================================
# Concrete Fetcher: DPC Criticality Bulletins
# =====================================================================

class DPCBulletinFetcher(AbstractAPIFetcher):
    """
    DPC (Dipartimento Protezione Civile) criticality bulletins via GitHub API.
    
    Repository:
        https://github.com/pcm-dpc/DPC-Bollettini-Criticita-Idrogeologica-Idraulica
    
    API:
        GitHub API to fetch latest JSON bulletins
    
    Data Format:
        JSON files with hydrogeological and hydraulic risk levels per region
    
    Example Usage:
        fetcher = DPCBulletinFetcher()
        params = fetcher.build_params(
            region="Campania",
            date="latest"  # or specific date "2024-01-11"
        )
    """
    
    def get_config(self) -> APIConfig:
        return APIConfig(
            name="dpc_bulletin",
            base_url="https://api.github.com",
            endpoint="/repos/pcm-dpc/DPC-Bollettini-Criticita-Idrogeologica-Idraulica/contents",
            method="GET",
            auth_type="none",
            timeout=30,
            max_retries=3,
            headers={"Accept": "application/vnd.github.v3+json"},
            response_format="json"
        )
    
    def build_params(self, **kwargs) -> Dict[str, Any]:
        """
        Build DPC API query parameters.
        
        Args:
            region: str — Region name (e.g., "Campania")
            date: str — Date (ISO format "2024-01-11" or "latest")
        
        Returns:
            Dict of GitHub API query parameters
        """
        # For now, we'll fetch the latest bulletin
        # In production, you'd parse date and region to get specific file
        return {
            "ref": "main",  # GitHub branch
            "path": kwargs.get("date", "latest")
        }
    
    def parse_response(self, response: APIResponse) -> Dict[str, Any]:
        """
        Parse DPC bulletin response.
        
        Returns:
            {
                "alert_level": str (giallo/arancione/rosso),
                "hydrogeological_risk": str,
                "hydraulic_risk": str,
                "issued_at": str (ISO timestamp)
            }
        """
        if not response.success:
            return {
                "alert_level": "unknown",
                "hydrogeological_risk": "unknown",
                "hydraulic_risk": "unknown",
                "issued_at": None
            }
        
        # Parse GitHub API response (content is base64-encoded)
        # In production, you'd decode and parse the actual bulletin JSON
        return {
            "alert_level": "giallo",  # Placeholder
            "hydrogeological_risk": "medium",
            "hydraulic_risk": "low",
            "issued_at": datetime.utcnow().isoformat()
        }
    
    def create_evidence_metadata(
        self,
        parsed_data: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create Evidence Pack metadata for DPC bulletin"""
        return {
            "source_type": "dpc_bulletin",
            "api_endpoint": "GitHub DPC Bollettini",
            "alert_level": parsed_data["alert_level"],
            "hydrogeological_risk": parsed_data["hydrogeological_risk"],
            "hydraulic_risk": parsed_data["hydraulic_risk"],
            "issued_at": parsed_data["issued_at"]
        }


# =====================================================================
# API Registry (Dynamic Fetcher Registration)
# =====================================================================

class APIRegistry:
    """
    Registry for dynamically registering and managing API fetchers.
    
    Allows adding new fetchers at runtime without modifying core code.
    
    Example:
        registry = APIRegistry()
        registry.register("custom_api", CustomAPIFetcher())
        fetcher = registry.get("custom_api")
    """
    
    def __init__(self):
        self._fetchers: Dict[str, AbstractAPIFetcher] = {}
        
        # Register default fetchers
        self.register("ingv_seismic", INGVSeismicFetcher())
        self.register("dpc_bulletin", DPCBulletinFetcher())
    
    def register(self, name: str, fetcher: AbstractAPIFetcher) -> None:
        """Register a new API fetcher"""
        if not isinstance(fetcher, AbstractAPIFetcher):
            raise TypeError(f"Fetcher must inherit from AbstractAPIFetcher")
        
        self._fetchers[name] = fetcher
        logger.info(f"Registered API fetcher: {name}")
    
    def get(self, name: str) -> Optional[AbstractAPIFetcher]:
        """Get registered fetcher by name"""
        return self._fetchers.get(name)
    
    def list_fetchers(self) -> List[str]:
        """List all registered fetcher names"""
        return list(self._fetchers.keys())
    
    def unregister(self, name: str) -> None:
        """Unregister a fetcher"""
        if name in self._fetchers:
            del self._fetchers[name]
            logger.info(f"Unregistered API fetcher: {name}")


# =====================================================================
# HTTP Client with Retry Logic
# =====================================================================

class HTTPClient:
    """
    HTTP client with retry logic and exponential backoff.
    """
    
    @staticmethod
    def execute_request(
        config: APIConfig,
        params: Dict[str, Any]
    ) -> APIResponse:
        """
        Execute HTTP request with retry logic.
        
        Args:
            config: API configuration
            params: Query parameters
        
        Returns:
            APIResponse with standardized response data
        """
        if not HTTPX_AVAILABLE:
            return APIResponse(
                success=False,
                error_message="httpx not available (pip install httpx)"
            )
        
        url = config.get_full_url()
        attempt = 0
        
        while attempt < config.max_retries:
            try:
                logger.info(f"API request attempt {attempt + 1}/{config.max_retries}: {url}")
                
                # Execute HTTP request
                if config.method == "GET":
                    response = httpx.get(
                        url,
                        params=params,
                        headers=config.headers,
                        timeout=config.timeout
                    )
                elif config.method == "POST":
                    response = httpx.post(
                        url,
                        json=params,
                        headers=config.headers,
                        timeout=config.timeout
                    )
                else:
                    return APIResponse(
                        success=False,
                        error_message=f"Unsupported HTTP method: {config.method}"
                    )
                
                # Check status code
                response.raise_for_status()
                
                # Parse response
                if config.response_format == "json":
                    data = response.json()
                elif config.response_format == "text":
                    data = {"text": response.text}
                else:
                    data = {"raw": response.content}
                
                return APIResponse(
                    success=True,
                    data=data,
                    raw_response=response.text,
                    status_code=response.status_code,
                    metadata={
                        "url": url,
                        "params": params,
                        "elapsed_ms": response.elapsed.total_seconds() * 1000
                    }
                )
            
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code}: {e}")
                
                # Don't retry on 4xx errors (client errors)
                if 400 <= e.response.status_code < 500:
                    return APIResponse(
                        success=False,
                        status_code=e.response.status_code,
                        error_message=f"HTTP {e.response.status_code}: {str(e)}"
                    )
                
                # Retry on 5xx errors (server errors)
                attempt += 1
                if attempt < config.max_retries:
                    backoff = config.retry_backoff ** attempt
                    logger.info(f"Retrying in {backoff}s...")
                    time.sleep(backoff)
            
            except Exception as e:
                logger.error(f"Request failed: {e}", exc_info=True)
                attempt += 1
                if attempt < config.max_retries:
                    backoff = config.retry_backoff ** attempt
                    time.sleep(backoff)
        
        return APIResponse(
            success=False,
            error_message=f"Failed after {config.max_retries} attempts"
        )


# =====================================================================
# Main API Intake Agent
# =====================================================================

class APIIntakeAgent:
    """
    Main API Intake Agent for orchestrating external API data acquisition.
    
    Responsibilities:
        1. Manage API fetcher registry
        2. Execute API requests with retry logic
        3. Parse and validate responses
        4. Create Evidence Packs in PostgreSQL
        5. Log all API interactions
    
    Example Usage:
        agent = APIIntakeAgent()
        
        # Fetch INGV seismic data
        evidence_id = agent.fetch_and_persist(
            fetcher_name="ingv_seismic",
            params={
                "bbox": [40.75, 14.05, 40.90, 14.25],
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2024-12-31T23:59:59",
                "min_magnitude": 2.0
            },
            scenario_name="campi_flegrei_baseline"
        )
        
        # Register custom fetcher
        agent.register_fetcher("weather_api", WeatherAPIFetcher())
    """
    
    def __init__(self):
        self.registry = APIRegistry()
        self.http_client = HTTPClient()
    
    def register_fetcher(self, name: str, fetcher: AbstractAPIFetcher) -> None:
        """Register a new API fetcher"""
        self.registry.register(name, fetcher)
    
    def list_fetchers(self) -> List[str]:
        """List all registered API fetchers"""
        return self.registry.list_fetchers()
    
    def fetch_and_persist(
        self,
        fetcher_name: str,
        params: Dict[str, Any],
        scenario_name: str,
        user_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Fetch data from external API and persist as Evidence Pack.
        
        Args:
            fetcher_name: Registered fetcher name (e.g., "ingv_seismic")
            params: Query parameters for API (e.g., {"bbox": [...], "start_date": "..."})
            scenario_name: Scenario identifier (e.g., "campi_flegrei_baseline")
            user_id: Optional user identifier
        
        Returns:
            Evidence ID of created Evidence Pack (or None if failed)
        
        Example:
            evidence_id = agent.fetch_and_persist(
                fetcher_name="ingv_seismic",
                params={"bbox": [40.75, 14.05, 40.90, 14.25], "start_date": "2024-01-01"},
                scenario_name="campi_flegrei_baseline"
            )
        """
        logger.info(f"API Intake: fetcher={fetcher_name}, scenario={scenario_name}")
        
        # Step 1: Get fetcher from registry
        fetcher = self.registry.get(fetcher_name)
        if not fetcher:
            logger.error(f"Unknown fetcher: {fetcher_name}")
            return None
        
        # Step 2: Validate parameters
        is_valid, error_msg = fetcher.validate_params(params)
        if not is_valid:
            logger.error(f"Invalid parameters: {error_msg}")
            return None
        
        # Step 3: Build API query parameters
        try:
            query_params = fetcher.build_params(**params)
        except Exception as e:
            logger.error(f"Failed to build params: {e}", exc_info=True)
            return None
        
        # Step 4: Execute API request
        config = fetcher.get_config()
        response = self.http_client.execute_request(config, query_params)
        
        if not response.success:
            logger.error(f"API request failed: {response.error_message}")
            return None
        
        # Step 5: Parse response
        try:
            parsed_data = fetcher.parse_response(response)
        except Exception as e:
            logger.error(f"Failed to parse response: {e}", exc_info=True)
            return None
        
        # Step 6: Create Evidence Pack metadata
        try:
            metadata = fetcher.create_evidence_metadata(parsed_data, query_params)
        except Exception as e:
            logger.error(f"Failed to create metadata: {e}", exc_info=True)
            return None
        
        # Step 7: Persist to PostgreSQL
        try:
            evidence_id = self._persist_evidence_pack(
                fetcher_name=fetcher_name,
                scenario_name=scenario_name,
                parsed_data=parsed_data,
                metadata=metadata,
                raw_response=response.raw_response,
                user_id=user_id
            )
            
            logger.info(f"Evidence Pack created: {evidence_id}")
            return evidence_id
        
        except Exception as e:
            logger.error(f"Failed to persist Evidence Pack: {e}", exc_info=True)
            return None
    
    def _persist_evidence_pack(
        self,
        fetcher_name: str,
        scenario_name: str,
        parsed_data: Dict[str, Any],
        metadata: Dict[str, Any],
        raw_response: Optional[str],
        user_id: Optional[str]
    ) -> str:
        """
        Persist Evidence Pack to PostgreSQL.
        
        Returns:
            Evidence ID of created Evidence Pack
        """
        if not POSTGRES_AVAILABLE:
            raise RuntimeError("PostgresAgent not available")
        
        pg = PostgresAgent()
        uid = uuid4().hex.upper()
        evidence_id = f"EVD-{uid[:8]}-{uid[8:12]}-{uid[12:16]}-{uid[16:20]}-{uid[20:32]}"
        chunk_id = "CHK-0"
        created_utc = datetime.utcnow().isoformat() + "Z"
        source_type = metadata.get("source_type", "document")
        if source_type not in {"document", "image", "audio", "video", "stream", "sensor"}:
            source_type = "document"

        normalized_text = json.dumps(parsed_data, ensure_ascii=False, indent=2)
        source_uri = metadata.get("source_url") or f"api://{fetcher_name}/{scenario_name}"
        source_hash_raw = hashlib.sha256((raw_response or normalized_text).encode("utf-8")).hexdigest()
        source_hash = f"sha256:{source_hash_raw}"
        evidence_hash = hashlib.sha256(
            f"{evidence_id}{chunk_id}{normalized_text}{source_hash}".encode("utf-8")
        ).hexdigest()
        
        with pg.connection.cursor() as cur:
            cur.execute("""
                INSERT INTO evidence_packs (
                    evidence_id,
                    chunk_id,
                    schema_version,
                    created_utc,
                    source_ref,
                    normalized_text,
                    technical_metadata,
                    integrity,
                    sampling_policy_ref,
                    tags
                ) VALUES (
                    %s, %s, %s, %s, %s::jsonb, %s, %s::jsonb, %s::jsonb, %s, %s::jsonb
                )
            """, (
                evidence_id,
                chunk_id,
                "1.0.0",
                created_utc,
                json.dumps({
                    "source_type": source_type,
                    "source_uri": source_uri,
                    "source_hash": source_hash,
                    "mime_type": "application/json",
                    "byte_size": len((raw_response or "").encode("utf-8")),
                }),
                normalized_text,
                json.dumps({
                    "fetcher_name": fetcher_name,
                    "scenario_name": scenario_name,
                    "user_id": user_id,
                    "metadata": metadata,
                    "parsed_data_summary": {
                        "keys": sorted(parsed_data.keys()) if isinstance(parsed_data, dict) else [],
                        "record_count": parsed_data.get("event_count") if isinstance(parsed_data, dict) else None,
                    },
                    "raw_response_present": raw_response is not None,
                }),
                json.dumps({
                    "evidence_hash": f"sha256:{evidence_hash}",
                    "immutable": True,
                }),
                None,
                json.dumps([f"source:{fetcher_name}", f"scenario:{scenario_name}"]),
            ))
        
        pg.connection.commit()
        return evidence_id


# =====================================================================
# Convenience Functions
# =====================================================================

def fetch_ingv_seismic_data(
    bbox: List[float],
    start_date: str,
    end_date: str,
    min_magnitude: float = 0.0,
    scenario_name: str = "default"
) -> Optional[str]:
    """
    Convenience function to fetch INGV seismic data.
    
    Args:
        bbox: [min_lat, min_lon, max_lat, max_lon]
        start_date: ISO 8601 timestamp
        end_date: ISO 8601 timestamp
        min_magnitude: Minimum magnitude (default 0.0)
        scenario_name: Scenario identifier
    
    Returns:
        Evidence ID of created Evidence Pack
    
    Example:
        evidence_id = fetch_ingv_seismic_data(
            bbox=[40.75, 14.05, 40.90, 14.25],
            start_date="2024-01-01T00:00:00",
            end_date="2024-12-31T23:59:59",
            min_magnitude=2.0,
            scenario_name="campi_flegrei_baseline"
        )
    """
    agent = APIIntakeAgent()
    return agent.fetch_and_persist(
        fetcher_name="ingv_seismic",
        params={
            "bbox": bbox,
            "start_date": start_date,
            "end_date": end_date,
            "min_magnitude": min_magnitude
        },
        scenario_name=scenario_name
    )
