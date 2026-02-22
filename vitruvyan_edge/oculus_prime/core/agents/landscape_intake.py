"""
Vitruvyan INTAKE — Landscape Analysis Intake Agent

Media Scope: Raster maps, satellite imagery, map tiles
Sources: Mapbox, OpenStreetMap, Google Maps, satellite providers

Use Cases:
- Warehouse location scouting (satellite imagery)
- Route planning (OpenStreetMap basemap)
- Terrain analysis (elevation rasters)
- Geospatial context (Google Maps screenshots with coordinates)

Compliance: ACCORDO-FONDATIVO-INTAKE-V1.1

Key Principles:
- Extract raster data + embedded coordinates (if available)
- Support map tile providers (Mapbox, OSM, Google Maps)
- Preserve URL context (style, zoom, bounds)
- Link to GeoJSON boundary polygons (via GeoIntaker)
- NO semantic interpretation (e.g., "good location" forbidden)
"""

import uuid
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import logging
from urllib.parse import urlparse, parse_qs

from vitruvyan_edge.oculus_prime.core.guardrails import IntakeGuardrails

# Image processing (conditional imports)
try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ Warning: Pillow not installed (pip install Pillow)")

# Geospatial libraries
try:
    import rasterio
    from rasterio.crs import CRS
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False
    print("⚠️ Warning: rasterio not installed (pip install rasterio)")


logger = logging.getLogger(__name__)


class LandscapeIntakeAgent:
    """
    Pre-epistemic landscape/raster data acquisition agent
    
    Responsibilities:
    - Extract raster images (PNG, JPG, GeoTIFF) with coordinates
    - Parse map provider URLs (Mapbox, Google Maps, OSM)
    - Extract embedded geospatial metadata (EXIF, GeoTIFF tags)
    - Link to vector boundaries (via evidence_id reference)
    - Create immutable Evidence Pack
    - Emit oculus_prime.evidence.created event (legacy alias: intake.evidence.created)
    
    DOES NOT:
    - Interpret visual content ("this is a good location")
    - Evaluate suitability or quality
    - Apply domain-specific heuristics
    - Call Codex directly
    """
    
    SUPPORTED_FORMATS = ['.png', '.jpg', '.jpeg', '.tif', '.tiff', '.geotiff']
    AGENT_ID = "landscape-intake-v1"
    AGENT_VERSION = "1.0.0"
    
    # Map provider URL patterns
    MAP_PROVIDERS = {
        "mapbox": re.compile(r'mapbox\.com|api\.mapbox\.com'),
        "google_maps": re.compile(r'maps\.google\.com|google\.com/maps'),
        "openstreetmap": re.compile(r'openstreetmap\.org|osm\.org'),
        "bing_maps": re.compile(r'bing\.com/maps'),
        "esri": re.compile(r'arcgis\.com|esri\.com')
    }
    
    def __init__(self, event_emitter, postgres_agent=None):
        """
        Args:
            event_emitter: IntakeEventEmitter instance
            postgres_agent: PostgresAgent for Evidence Pack persistence
        """
        self.event_emitter = event_emitter
        self.postgres_agent = postgres_agent
        self.guardrails = IntakeGuardrails()
        
        if not PIL_AVAILABLE:
            logger.warning("Pillow not available - image processing disabled")
    
    def ingest(
        self,
        file_path: Path,
        source_type: str = "map_screenshot",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main ingestion entry point
        
        Args:
            file_path: Path to raster image (PNG, JPG, GeoTIFF)
            source_type: Origin (map_screenshot, satellite_image, terrain_map)
            metadata: Optional context (map_url, provider, zoom_level)
        
        Returns:
            Dict with Evidence Pack details
        
        Raises:
            ValueError: If file format unsupported
        """
        # Basic validation
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Landscape file not found: {file_path}")
        
        if file_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported raster format: {file_path.suffix}. "
                f"Supported: {self.SUPPORTED_FORMATS}"
            )
        
        # Check file size (max 100MB for satellite imagery)
        byte_size = file_path.stat().st_size
        max_size = 100 * 1024 * 1024  # 100MB
        if byte_size > max_size:
            raise ValueError(f"File too large: {byte_size} bytes (max {max_size} bytes)")
        
        # Read file content
        content_bytes = file_path.read_bytes()
        
        # Compute integrity hash (SHA-256)
        integrity_hash = f"sha256:{hashlib.sha256(content_bytes).hexdigest()}"
        
        # Extract raster metadata
        raster_data = self._extract_raster_metadata(file_path, content_bytes)
        
        # Parse map URL context (if provided)
        map_context = None
        if metadata and "map_url" in metadata:
            map_context = self._parse_map_url(metadata["map_url"])
        
        # Generate literal text description
        literal_text = self._generate_literal_text(raster_data, map_context, file_path)
        
        # Create Evidence Pack (ACCORDO-FONDATIVO v1.1 compliant)
        uid = uuid.uuid4().hex.upper()
        evidence_id = f"EVD-{uid[:8]}-{uid[8:12]}-{uid[12:16]}-{uid[16:20]}-{uid[20:32]}"
        evidence_pack = {
            "evidence_id": evidence_id,
            "chunk_id": "CHK-0",
            "schema_version": "1.0.0",
            "fragment_type": "landscape_raster",
            "source_type": source_type,
            "file_reference": str(file_path.absolute()),
            "byte_size": byte_size,
            "integrity": {
                "evidence_hash": integrity_hash,
                "hash": integrity_hash,  # backward-compatible alias
                "immutable": True,
                "algorithm": "sha256",
            },
            "normalized_text": literal_text,
            "metadata": {
                **(metadata or {}),
                "raster_format": raster_data["format"],
                "dimensions": raster_data["dimensions"],
                "has_georeference": raster_data["has_georeference"],
                "coordinate_system": raster_data.get("coordinate_system"),
                "bounds": raster_data.get("bounds"),  # [min_lon, min_lat, max_lon, max_lat]
                "resolution_meters": raster_data.get("resolution_meters"),
                "exif_gps": raster_data.get("exif_gps"),
                "map_provider": map_context.get("provider") if map_context else None,
                "map_zoom": map_context.get("zoom") if map_context else None,
                "map_style": map_context.get("style") if map_context else None,
            },
            "agent_id": self.AGENT_ID,
            "agent_version": self.AGENT_VERSION,
            "created_utc": datetime.now(timezone.utc).isoformat(),
        }
        
        # Persist to PostgreSQL (if available)
        if self.postgres_agent:
            self._persist_evidence(evidence_pack)
        
        # Emit event to Redis Cognitive Bus (updated for new schema - Jan 13, 2026)
        self.event_emitter.emit_evidence_created(
            evidence_id=evidence_pack["evidence_id"],
            chunk_id=evidence_pack["chunk_id"],
            source_type=evidence_pack["source_type"],
            source_uri=evidence_pack["file_reference"],
            evidence_pack_ref=f"postgres://evidence_packs/{evidence_pack['evidence_id']}",
            source_hash=evidence_pack["integrity"]["evidence_hash"],
            intake_agent_id=evidence_pack["agent_id"],
            intake_agent_version=evidence_pack["agent_version"],
            byte_size=evidence_pack["byte_size"]
        )
        
        logger.info(
            f"✅ LandscapeIntaker: Evidence Pack {evidence_id} created "
            f"(format={raster_data['format']}, dimensions={raster_data['dimensions']}, "
            f"georeferenced={raster_data['has_georeference']}, hash={integrity_hash[:8]}...)"
        )
        
        return evidence_pack
    
    def _extract_raster_metadata(self, file_path: Path, content_bytes: bytes) -> Dict[str, Any]:
        """
        Extract metadata from raster image
        
        Returns:
            Dict with dimensions, georeference, EXIF data
        """
        result = {
            "format": file_path.suffix.lower().lstrip('.'),
            "dimensions": None,
            "has_georeference": False,
            "coordinate_system": None,
            "bounds": None,
            "resolution_meters": None,
            "exif_gps": None
        }
        
        # Try GeoTIFF first (rasterio)
        if file_path.suffix.lower() in ['.tif', '.tiff', '.geotiff'] and RASTERIO_AVAILABLE:
            try:
                with rasterio.open(file_path) as dataset:
                    result["dimensions"] = [dataset.width, dataset.height]
                    result["has_georeference"] = dataset.crs is not None
                    
                    if dataset.crs:
                        result["coordinate_system"] = dataset.crs.to_string()
                        bounds = dataset.bounds
                        result["bounds"] = [bounds.left, bounds.bottom, bounds.right, bounds.top]
                        
                        # Calculate resolution (meters per pixel)
                        # Approximate: transform[0] is pixel width in CRS units
                        if dataset.crs.is_geographic:
                            # Convert degrees to meters (rough: 1° ≈ 111km)
                            result["resolution_meters"] = abs(dataset.transform[0]) * 111000
                        else:
                            result["resolution_meters"] = abs(dataset.transform[0])
                
                return result
            except Exception as e:
                logger.warning(f"GeoTIFF parsing failed: {e}")
        
        # Fallback to PIL for PNG/JPG (EXIF)
        if PIL_AVAILABLE:
            try:
                import io
                img = Image.open(io.BytesIO(content_bytes))
                
                result["dimensions"] = [img.width, img.height]
                
                # Extract EXIF GPS data
                exif_data = img._getexif()
                if exif_data:
                    gps_info = self._extract_gps_from_exif(exif_data)
                    if gps_info:
                        result["exif_gps"] = gps_info
                        result["has_georeference"] = True
                        result["coordinate_system"] = "WGS84"
                        
                        # Create bounds from single point
                        lat, lon = gps_info["latitude"], gps_info["longitude"]
                        result["bounds"] = [lon, lat, lon, lat]
                
                return result
            except Exception as e:
                logger.warning(f"PIL image parsing failed: {e}")
        
        return result
    
    def _extract_gps_from_exif(self, exif_data: Dict) -> Optional[Dict[str, float]]:
        """
        Extract GPS coordinates from EXIF data
        
        Returns:
            {"latitude": 45.4654, "longitude": 9.1859, "altitude": 120.5}
        """
        try:
            gps_info = {}
            for tag, value in exif_data.items():
                tag_name = TAGS.get(tag, tag)
                if tag_name == "GPSInfo":
                    for gps_tag in value:
                        gps_tag_name = GPSTAGS.get(gps_tag, gps_tag)
                        gps_info[gps_tag_name] = value[gps_tag]
            
            if not gps_info:
                return None
            
            # Parse GPS coordinates
            def convert_to_degrees(value):
                """Convert GPS coordinates to degrees"""
                d, m, s = value
                return d + (m / 60.0) + (s / 3600.0)
            
            lat = convert_to_degrees(gps_info.get("GPSLatitude", [0, 0, 0]))
            lon = convert_to_degrees(gps_info.get("GPSLongitude", [0, 0, 0]))
            
            # Apply N/S, E/W
            if gps_info.get("GPSLatitudeRef") == "S":
                lat = -lat
            if gps_info.get("GPSLongitudeRef") == "W":
                lon = -lon
            
            result = {"latitude": lat, "longitude": lon}
            
            # Altitude (optional)
            if "GPSAltitude" in gps_info:
                alt = float(gps_info["GPSAltitude"])
                if gps_info.get("GPSAltitudeRef") == 1:
                    alt = -alt
                result["altitude"] = alt
            
            # GPS accuracy (for provenance/uncertainty tracking)
            if "GPSHPositioningError" in gps_info:
                result["accuracy_meters"] = float(gps_info["GPSHPositioningError"])
            else:
                # Default: typical smartphone GPS accuracy
                result["accuracy_meters"] = 10.0
            
            return result
        except Exception as e:
            logger.warning(f"GPS EXIF extraction failed: {e}")
            return None
    
    def _parse_map_url(self, url: str) -> Dict[str, Any]:
        """
        Parse map provider URL to extract context
        
        Examples:
        - Mapbox: https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/9.1859,45.4654,15/800x600?access_token=...
        - Google Maps: https://www.google.com/maps/@45.4654,9.1859,15z
        - OpenStreetMap: https://www.openstreetmap.org/#map=15/45.4654/9.1859
        
        Returns:
            {"provider": "mapbox", "zoom": 15, "center": [9.1859, 45.4654], "style": "satellite-v9"}
        """
        result = {"provider": None, "zoom": None, "center": None, "style": None}
        
        # Identify provider
        for provider, pattern in self.MAP_PROVIDERS.items():
            if pattern.search(url):
                result["provider"] = provider
                break
        
        if not result["provider"]:
            return result
        
        # Parse provider-specific URL formats
        if result["provider"] == "mapbox":
            # Mapbox Static API: /styles/v1/{username}/{style_id}/static/{lon},{lat},{zoom}/{width}x{height}
            match = re.search(r'/styles/v1/([^/]+)/([^/]+)/static/(-?\d+\.?\d*),(-?\d+\.?\d*),(\d+)/', url)
            if match:
                result["style"] = f"{match.group(1)}/{match.group(2)}"
                result["center"] = [float(match.group(3)), float(match.group(4))]
                result["zoom"] = int(match.group(5))
        
        elif result["provider"] == "google_maps":
            # Google Maps: @{lat},{lon},{zoom}z
            match = re.search(r'@(-?\d+\.?\d*),(-?\d+\.?\d*),(\d+)z', url)
            if match:
                result["center"] = [float(match.group(2)), float(match.group(1))]
                result["zoom"] = int(match.group(3))
        
        elif result["provider"] == "openstreetmap":
            # OpenStreetMap: #map={zoom}/{lat}/{lon}
            match = re.search(r'#map=(\d+)/(-?\d+\.?\d*)/(-?\d+\.?\d*)', url)
            if match:
                result["zoom"] = int(match.group(1))
                result["center"] = [float(match.group(3)), float(match.group(2))]
        
        return result
    
    def _generate_literal_text(
        self,
        raster_data: Dict,
        map_context: Optional[Dict],
        file_path: Path
    ) -> str:
        """
        Generate descriptive (non-interpretative) text representation
        """
        parts = [
            f"Landscape raster file: {file_path.name}",
            f"Format: {raster_data['format'].upper()}"
        ]
        
        # Add dimensions if available
        if raster_data['dimensions']:
            parts.append(f"Dimensions: {raster_data['dimensions'][0]}x{raster_data['dimensions'][1]} pixels")
        else:
            parts.append("Dimensions: unknown (requires Pillow or rasterio)")
        
        # Georeference data (descriptive only, no interpretation)
        if raster_data["has_georeference"]:
            if raster_data.get('coordinate_system'):
                parts.append(f"Coordinate system: {raster_data['coordinate_system']}")
            
            if raster_data.get("bounds"):
                bbox = raster_data["bounds"]
                parts.append(
                    f"Geographic bounds: lon[{bbox[0]:.6f}, {bbox[2]:.6f}], "
                    f"lat[{bbox[1]:.6f}, {bbox[3]:.6f}]"
                )
            
            if raster_data.get("resolution_meters"):
                parts.append(f"Resolution: {raster_data['resolution_meters']:.2f} meters per pixel")
            
            if raster_data.get("exif_gps"):
                gps = raster_data["exif_gps"]
                parts.append(f"GPS coordinates: lat={gps['latitude']:.6f}, lon={gps['longitude']:.6f}")
                if "altitude" in gps:
                    parts.append(f"GPS altitude: {gps['altitude']:.1f} meters")
        else:
            parts.append("Coordinate system: none detected")
        
        # Map context (if from URL)
        if map_context and map_context["provider"]:
            parts.append(f"Map provider: {map_context['provider']}")
            if map_context["zoom"]:
                parts.append(f"Zoom level: {map_context['zoom']}")
            if map_context["center"]:
                parts.append(f"Center: lon={map_context['center'][0]:.6f}, lat={map_context['center'][1]:.6f}")
            if map_context["style"]:
                parts.append(f"Map style: {map_context['style']}")
        
        return "\n".join(parts)
    
    def _persist_evidence(self, evidence_pack: Dict[str, Any]):
        """
        Persist Evidence Pack to PostgreSQL (landscape_evidence table)
        """
        try:
            with self.postgres_agent.connection.cursor() as cur:
                # Prepare JSONB fields (schema v1.0.0 compliant - Jan 13, 2026)
                source_ref = {
                    "source_type": evidence_pack["source_type"],
                    "source_uri": evidence_pack["file_reference"],
                    "source_hash": evidence_pack["integrity"]["evidence_hash"],
                    "domain_family": evidence_pack["metadata"].get("domain_family", "unknown"),
                    "byte_size": evidence_pack["byte_size"],
                }
                
                technical_metadata = {
                    "fragment_type": evidence_pack["fragment_type"],
                    "file_name": Path(evidence_pack["file_reference"]).name,
                    "byte_size": evidence_pack["byte_size"],
                    "agent_id": evidence_pack["agent_id"],
                    "agent_version": evidence_pack["agent_version"]
                }
                
                integrity = {
                    "evidence_hash": evidence_pack["integrity"]["evidence_hash"],
                    "immutable": True,
                    "algorithm": "sha256",
                }
                
                # Insert into evidence_packs (JSONB-based schema)
                cur.execute("""
                    INSERT INTO evidence_packs (
                        evidence_id,
                        chunk_id,
                        created_utc,
                        source_ref,
                        normalized_text,
                        technical_metadata,
                        integrity,
                        tags
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    evidence_pack["evidence_id"],
                    evidence_pack["chunk_id"],
                    evidence_pack["created_utc"],
                    json.dumps(source_ref),
                    evidence_pack["normalized_text"],
                    json.dumps(technical_metadata),
                    json.dumps(integrity),
                    json.dumps([])  # Empty tags array
                ))
                
                # CRITICAL: Store landscape raster metadata separately
                cur.execute("""
                    INSERT INTO landscape_evidence (
                        evidence_id,
                        chunk_id,
                        raster_format,
                        dimensions,
                        has_georeference,
                        coordinate_system,
                        bounds,
                        resolution_meters,
                        map_provider,
                        map_zoom,
                        created_utc,
                        source_hash
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    evidence_pack["evidence_id"],
                    evidence_pack["chunk_id"],
                    evidence_pack["metadata"]["raster_format"],
                    evidence_pack["metadata"]["dimensions"],
                    evidence_pack["metadata"]["has_georeference"],
                    evidence_pack["metadata"].get("coordinate_system"),
                    evidence_pack["metadata"].get("bounds"),
                    evidence_pack["metadata"].get("resolution_meters"),
                    evidence_pack["metadata"].get("map_provider"),
                    evidence_pack["metadata"].get("map_zoom"),
                    evidence_pack["created_utc"],
                    evidence_pack["integrity"]["evidence_hash"].replace("sha256:", ""),
                ))
                
                self.postgres_agent.connection.commit()
                
        except Exception as e:
            logger.error(f"PostgreSQL persistence failed: {e}")
            if self.postgres_agent:
                self.postgres_agent.connection.rollback()
            raise
