"""
AEGIS INTAKE — Geospatial Intake Agent

Media Scope: KML, KMZ, GeoJSON, GPX, WKT polygons
Use Cases: Warehouse boundaries, delivery zones, operational areas, GPS tracks

Compliance: ACCORDO-FONDATIVO-INTAKE-V1.1

Key Principles:
- Extract geospatial data literally (coordinates, polygons, metadata)
- Support Google Maps export (KML/KMZ)
- Normalize to GeoJSON canonical format
- Preserve raw reference + hash
- Emit Evidence Pack + event
- NO semantic inference (e.g., "this is optimal zone")
"""

import uuid
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import logging
import xml.etree.ElementTree as ET

# Intake guardrails
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from guardrails import IntakeGuardrails

# Geospatial libraries (conditional imports)
try:
    from shapely.geometry import shape, Point, Polygon, MultiPolygon, LineString
    from shapely import wkt
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    print("⚠️ Warning: shapely not installed (pip install shapely)")


logger = logging.getLogger(__name__)


class GeoIntakeAgent:
    """
    Pre-epistemic geospatial data acquisition agent
    
    Responsibilities:
    - Extract coordinates, polygons, tracks from geo files
    - Parse KML/KMZ (Google Maps export), GeoJSON, GPX, WKT
    - Normalize to canonical GeoJSON format
    - Calculate bounding box, area (if polygon)
    - Create immutable Evidence Pack
    - Emit intake.evidence.created event
    
    DOES NOT:
    - Interpret spatial semantics ("optimal zone", "risky area")
    - Evaluate geographic relevance
    - Apply domain-specific geo rules
    - Call Codex directly
    """
    
    SUPPORTED_FORMATS = ['.kml', '.kmz', '.geojson', '.json', '.gpx', '.wkt', '.txt']
    AGENT_ID = "geo-intake-v1"
    AGENT_VERSION = "1.0.0"
    
    # KML namespace (Google Earth standard)
    KML_NS = {'kml': 'http://www.opengis.net/kml/2.2'}
    
    def __init__(self, event_emitter, postgres_agent=None):
        """
        Args:
            event_emitter: IntakeEventEmitter instance
            postgres_agent: PostgresAgent for Evidence Pack persistence
        """
        self.event_emitter = event_emitter
        self.postgres_agent = postgres_agent
        self.guardrails = IntakeGuardrails()
        
        if not SHAPELY_AVAILABLE:
            logger.warning("Shapely not available - polygon validation disabled")
    
    def ingest(
        self,
        file_path: Path,
        source_type: str = "geo_file",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main ingestion entry point
        
        Args:
            file_path: Path to geospatial file (KML, GeoJSON, GPX, WKT)
            source_type: Origin classification (google_maps, field_gps, manual_polygon)
            metadata: Optional additional context
        
        Returns:
            Dict with Evidence Pack details
        
        Raises:
            ValueError: If file format unsupported or malformed
        """
        # Basic validation
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Geospatial file not found: {file_path}")
        
        if file_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported geospatial format: {file_path.suffix}. "
                f"Supported: {self.SUPPORTED_FORMATS}"
            )
        
        # Check file size (max 50MB for KMZ)
        byte_size = file_path.stat().st_size
        max_size = 50 * 1024 * 1024  # 50MB
        if byte_size > max_size:
            raise ValueError(f"File too large: {byte_size} bytes (max {max_size} bytes)")
        
        # Read file content
        content_bytes = file_path.read_bytes()
        
        # Compute integrity hash (SHA-256)
        integrity_hash = hashlib.sha256(content_bytes).hexdigest()
        
        # Extract geospatial data based on format
        geo_data = self._extract_geo_data(file_path, content_bytes)
        
        # Generate literal text description
        literal_text = self._generate_literal_text(geo_data, file_path)
        
        # Create Evidence Pack (NEW SCHEMA)
        evidence_id = str(uuid.uuid4())
        evidence_pack = {
            "evidence_id": evidence_id,
            "chunk_id": "CHK-0",  # NEW SCHEMA
            "schema_version": "1.0.0",  # NEW SCHEMA
            "created_utc": datetime.now(timezone.utc).isoformat(),  # NEW SCHEMA
            "source_ref": {  # NEW SCHEMA: JSONB
                "source_type": source_type,
                "source_uri": str(file_path.absolute()),
                "source_hash": integrity_hash,
                "fragment_type": "geospatial"
            },
            "normalized_text": literal_text,  # NEW SCHEMA
            "technical_metadata": {  # NEW SCHEMA: JSONB
                **(metadata or {}),
                "file_size_bytes": byte_size,
                "geo_format": geo_data["format"],
                "feature_count": geo_data["feature_count"],
                "bounding_box": geo_data["bounding_box"],
                "geometry_types": geo_data["geometry_types"],
                "coordinate_system": geo_data.get("coordinate_system", "WGS84"),
                "area_km2": geo_data.get("area_km2"),
                "total_length_km": geo_data.get("total_length_km"),
                "geo_json": geo_data["canonical_geojson"],  # Embedded in metadata
                "agent_id": self.AGENT_ID,
                "agent_version": self.AGENT_VERSION
            },
            "integrity": {  # NEW SCHEMA: JSONB
                "hash_algorithm": "SHA-256",
                "hash_value": integrity_hash
            },
            "sampling_policy_ref": None,  # NEW SCHEMA
            "tags": []  # NEW SCHEMA
        }
        
        # Persist to PostgreSQL (if available)
        if self.postgres_agent:
            self._persist_evidence(evidence_pack)
        
        # Emit event to Redis Cognitive Bus (NEW METHOD)
        self.event_emitter.emit_evidence_created_from_pack(evidence_pack)
        
        logger.info(
            f"✅ GeoIntaker: Evidence Pack {evidence_id} created "
            f"(format={geo_data['format']}, features={geo_data['feature_count']}, "
            f"hash={integrity_hash[:8]}...)"
        )
        
        return evidence_pack
    
    def _extract_geo_data(self, file_path: Path, content_bytes: bytes) -> Dict[str, Any]:
        """
        Extract geospatial data from file based on format
        
        Returns:
            Dict with canonical GeoJSON + metadata
        """
        suffix = file_path.suffix.lower()
        
        if suffix == '.kmz':
            return self._parse_kmz(content_bytes)
        elif suffix == '.kml':
            return self._parse_kml(content_bytes.decode('utf-8'))
        elif suffix in ['.geojson', '.json']:
            return self._parse_geojson(content_bytes.decode('utf-8'))
        elif suffix == '.gpx':
            return self._parse_gpx(content_bytes.decode('utf-8'))
        elif suffix in ['.wkt', '.txt']:
            return self._parse_wkt(content_bytes.decode('utf-8'))
        else:
            raise ValueError(f"Unsupported geospatial format: {suffix}")
    
    def _parse_kmz(self, content_bytes: bytes) -> Dict[str, Any]:
        """
        Parse KMZ (zipped KML) from Google Maps export
        
        KMZ structure:
        - doc.kml (main file)
        - images/ (optional placemarks icons)
        """
        import io
        
        with zipfile.ZipFile(io.BytesIO(content_bytes)) as kmz:
            # Find doc.kml or first .kml file
            kml_files = [f for f in kmz.namelist() if f.endswith('.kml')]
            if not kml_files:
                raise ValueError("No KML file found in KMZ archive")
            
            kml_content = kmz.read(kml_files[0]).decode('utf-8')
            return self._parse_kml(kml_content)
    
    def _parse_kml(self, kml_content: str) -> Dict[str, Any]:
        """
        Parse KML from Google Maps (Earth standard)
        
        Extracts:
        - Placemarks (points, polygons, linestrings)
        - Names, descriptions
        - Coordinates
        """
        root = ET.fromstring(kml_content)
        features = []
        geometry_types = set()
        
        # Find all Placemark elements
        for placemark in root.findall('.//kml:Placemark', self.KML_NS):
            name_elem = placemark.find('kml:name', self.KML_NS)
            desc_elem = placemark.find('kml:description', self.KML_NS)
            
            name = name_elem.text if name_elem is not None else "Unnamed"
            description = desc_elem.text if desc_elem is not None else None
            
            # Extract geometry (Point, Polygon, LineString)
            geometry = None
            
            # Point
            point = placemark.find('.//kml:Point/kml:coordinates', self.KML_NS)
            if point is not None:
                coords = self._parse_kml_coordinates(point.text)
                geometry = {"type": "Point", "coordinates": coords[0]}
                geometry_types.add("Point")
            
            # Polygon
            polygon = placemark.find('.//kml:Polygon', self.KML_NS)
            if polygon is not None:
                outer = polygon.find('.//kml:outerBoundaryIs//kml:coordinates', self.KML_NS)
                if outer is not None:
                    coords = self._parse_kml_coordinates(outer.text)
                    geometry = {"type": "Polygon", "coordinates": [coords]}
                    geometry_types.add("Polygon")
            
            # LineString
            linestring = placemark.find('.//kml:LineString/kml:coordinates', self.KML_NS)
            if linestring is not None:
                coords = self._parse_kml_coordinates(linestring.text)
                geometry = {"type": "LineString", "coordinates": coords}
                geometry_types.add("LineString")
            
            if geometry:
                features.append({
                    "type": "Feature",
                    "properties": {
                        "name": name,
                        "description": description
                    },
                    "geometry": geometry
                })
        
        # Create GeoJSON FeatureCollection
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        # Calculate bounding box and area
        bbox = self._calculate_bounding_box(geojson)
        area_km2 = self._calculate_area(geojson) if "Polygon" in geometry_types else None
        
        return {
            "format": "KML",
            "feature_count": len(features),
            "geometry_types": list(geometry_types),
            "bounding_box": bbox,
            "area_km2": area_km2,
            "canonical_geojson": geojson,
            "coordinate_system": "WGS84"
        }
    
    def _parse_kml_coordinates(self, coord_text: str) -> List[List[float]]:
        """
        Parse KML coordinate string (lon,lat,alt format)
        
        Example: "9.1859,45.4654,0 9.1860,45.4655,0"
        Returns: [[9.1859, 45.4654], [9.1860, 45.4655]]
        """
        coords = []
        for point in coord_text.strip().split():
            parts = point.split(',')
            lon, lat = float(parts[0]), float(parts[1])
            coords.append([lon, lat])  # GeoJSON format: [lon, lat]
        return coords
    
    def _parse_geojson(self, geojson_content: str) -> Dict[str, Any]:
        """
        Parse GeoJSON (already canonical format)
        """
        geojson = json.loads(geojson_content)
        
        # Validate structure
        if "type" not in geojson:
            raise ValueError("Invalid GeoJSON: missing 'type' field")
        
        # Extract geometry types
        geometry_types = set()
        feature_count = 0
        
        if geojson["type"] == "FeatureCollection":
            features = geojson.get("features", [])
            feature_count = len(features)
            for feature in features:
                geom_type = feature.get("geometry", {}).get("type")
                if geom_type:
                    geometry_types.add(geom_type)
        elif geojson["type"] == "Feature":
            feature_count = 1
            geom_type = geojson.get("geometry", {}).get("type")
            if geom_type:
                geometry_types.add(geom_type)
        else:
            # Single geometry
            feature_count = 1
            geometry_types.add(geojson["type"])
        
        bbox = self._calculate_bounding_box(geojson)
        area_km2 = self._calculate_area(geojson) if "Polygon" in geometry_types else None
        
        return {
            "format": "GeoJSON",
            "feature_count": feature_count,
            "geometry_types": list(geometry_types),
            "bounding_box": bbox,
            "area_km2": area_km2,
            "canonical_geojson": geojson,
            "coordinate_system": "WGS84"
        }
    
    def _parse_gpx(self, gpx_content: str) -> Dict[str, Any]:
        """
        Parse GPX (GPS Exchange Format) - tracks, routes, waypoints
        """
        root = ET.fromstring(gpx_content)
        features = []
        geometry_types = set()
        
        # GPX namespace
        gpx_ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
        
        # Parse waypoints (points)
        for wpt in root.findall('.//gpx:wpt', gpx_ns):
            lat = float(wpt.get('lat'))
            lon = float(wpt.get('lon'))
            name_elem = wpt.find('gpx:name', gpx_ns)
            name = name_elem.text if name_elem is not None else "Waypoint"
            
            features.append({
                "type": "Feature",
                "properties": {"name": name},
                "geometry": {"type": "Point", "coordinates": [lon, lat]}
            })
            geometry_types.add("Point")
        
        # Parse tracks (linestrings)
        for trk in root.findall('.//gpx:trk', gpx_ns):
            name_elem = trk.find('gpx:name', gpx_ns)
            name = name_elem.text if name_elem is not None else "Track"
            
            coords = []
            for trkpt in trk.findall('.//gpx:trkpt', gpx_ns):
                lat = float(trkpt.get('lat'))
                lon = float(trkpt.get('lon'))
                coords.append([lon, lat])
            
            if coords:
                features.append({
                    "type": "Feature",
                    "properties": {"name": name},
                    "geometry": {"type": "LineString", "coordinates": coords}
                })
                geometry_types.add("LineString")
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        bbox = self._calculate_bounding_box(geojson)
        length_km = self._calculate_length(geojson) if "LineString" in geometry_types else None
        
        return {
            "format": "GPX",
            "feature_count": len(features),
            "geometry_types": list(geometry_types),
            "bounding_box": bbox,
            "total_length_km": length_km,
            "canonical_geojson": geojson,
            "coordinate_system": "WGS84"
        }
    
    def _parse_wkt(self, wkt_content: str) -> Dict[str, Any]:
        """
        Parse WKT (Well-Known Text) format
        
        Example: "POLYGON((9.18 45.46, 9.19 45.46, 9.19 45.47, 9.18 45.47, 9.18 45.46))"
        """
        if not SHAPELY_AVAILABLE:
            raise ImportError("Shapely required for WKT parsing: pip install shapely")
        
        # Parse WKT using shapely
        geom = wkt.loads(wkt_content.strip())
        
        # Convert to GeoJSON
        geojson_geom = json.loads(json.dumps(geom.__geo_interface__))
        
        geojson = {
            "type": "Feature",
            "properties": {"source": "WKT"},
            "geometry": geojson_geom
        }
        
        bbox = self._calculate_bounding_box(geojson)
        area_km2 = self._calculate_area(geojson) if geom.geom_type == "Polygon" else None
        
        return {
            "format": "WKT",
            "feature_count": 1,
            "geometry_types": [geom.geom_type],
            "bounding_box": bbox,
            "area_km2": area_km2,
            "canonical_geojson": geojson,
            "coordinate_system": "WGS84"
        }
    
    def _calculate_bounding_box(self, geojson: Dict) -> Optional[List[float]]:
        """
        Calculate bounding box [min_lon, min_lat, max_lon, max_lat]
        """
        if not SHAPELY_AVAILABLE:
            return None
        
        try:
            # Extract all coordinates
            coords = []
            
            if geojson["type"] == "FeatureCollection":
                for feature in geojson.get("features", []):
                    geom = feature.get("geometry")
                    if geom:
                        coords.extend(self._extract_coords(geom))
            elif geojson["type"] == "Feature":
                coords.extend(self._extract_coords(geojson.get("geometry", {})))
            else:
                coords.extend(self._extract_coords(geojson))
            
            if not coords:
                return None
            
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            
            return [min(lons), min(lats), max(lons), max(lats)]
        except Exception as e:
            logger.warning(f"Bounding box calculation failed: {e}")
            return None
    
    def _extract_coords(self, geometry: Dict) -> List[List[float]]:
        """Recursively extract all coordinates from geometry"""
        coords = []
        geom_type = geometry.get("type")
        geom_coords = geometry.get("coordinates", [])
        
        if geom_type == "Point":
            coords.append(geom_coords)
        elif geom_type in ["LineString", "MultiPoint"]:
            coords.extend(geom_coords)
        elif geom_type in ["Polygon", "MultiLineString"]:
            for ring in geom_coords:
                coords.extend(ring)
        elif geom_type == "MultiPolygon":
            for poly in geom_coords:
                for ring in poly:
                    coords.extend(ring)
        
        return coords
    
    def _calculate_area(self, geojson: Dict) -> Optional[float]:
        """
        Calculate area in km² (for polygons)
        Uses geodesic calculation (WGS84 ellipsoid)
        """
        if not SHAPELY_AVAILABLE:
            return None
        
        try:
            total_area = 0.0
            
            if geojson["type"] == "FeatureCollection":
                for feature in geojson.get("features", []):
                    geom = feature.get("geometry")
                    if geom and geom["type"] in ["Polygon", "MultiPolygon"]:
                        shp = shape(geom)
                        # Approximate area (Shapely uses planar, good for small areas)
                        # For accurate geodesic: use pyproj or geopy
                        area_deg2 = shp.area
                        # Convert deg² to km² (rough: 1° ≈ 111km at equator)
                        total_area += area_deg2 * (111 * 111)
            
            return round(total_area, 4) if total_area > 0 else None
        except Exception as e:
            logger.warning(f"Area calculation failed: {e}")
            return None
    
    def _calculate_length(self, geojson: Dict) -> Optional[float]:
        """
        Calculate total length in km (for linestrings/tracks)
        """
        if not SHAPELY_AVAILABLE:
            return None
        
        try:
            total_length = 0.0
            
            if geojson["type"] == "FeatureCollection":
                for feature in geojson.get("features", []):
                    geom = feature.get("geometry")
                    if geom and geom["type"] in ["LineString", "MultiLineString"]:
                        shp = shape(geom)
                        length_deg = shp.length
                        # Convert deg to km (rough: 1° ≈ 111km)
                        total_length += length_deg * 111
            
            return round(total_length, 4) if total_length > 0 else None
        except Exception as e:
            logger.warning(f"Length calculation failed: {e}")
            return None
    
    def _generate_literal_text(self, geo_data: Dict, file_path: Path) -> str:
        """
        Generate descriptive (non-interpretative) text representation
        """
        parts = [
            f"Geospatial file: {file_path.name}",
            f"Format: {geo_data['format']}",
            f"Features: {geo_data['feature_count']}",
            f"Geometry types: {', '.join(geo_data['geometry_types'])}"
        ]
        
        if geo_data.get("bounding_box"):
            bbox = geo_data["bounding_box"]
            parts.append(
                f"Bounding box: lon[{bbox[0]:.4f}, {bbox[2]:.4f}], "
                f"lat[{bbox[1]:.4f}, {bbox[3]:.4f}]"
            )
        
        if geo_data.get("area_km2"):
            parts.append(f"Total area: {geo_data['area_km2']:.2f} km²")
        
        if geo_data.get("total_length_km"):
            parts.append(f"Total length: {geo_data['total_length_km']:.2f} km")
        
        # Extract feature names (if available)
        geojson = geo_data["canonical_geojson"]
        if geojson["type"] == "FeatureCollection":
            names = [
                f.get("properties", {}).get("name", "Unnamed")
                for f in geojson["features"][:5]  # First 5 only
            ]
            if names:
                parts.append(f"Feature names: {', '.join(names)}")
        
        return "\n".join(parts)
    
    def _persist_evidence(self, evidence_pack: Dict[str, Any]):
        """
        Persist Evidence Pack to PostgreSQL (evidence_packs table)
        """
        try:
            with self.postgres_agent.connection.cursor() as cur:
                cur.execute("""
                    INSERT INTO evidence_packs (
                        evidence_id, chunk_id, schema_version, created_utc,
                        source_ref, normalized_text, technical_metadata,
                        integrity, sampling_policy_ref, tags
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    evidence_pack["evidence_id"],
                    evidence_pack["chunk_id"],
                    evidence_pack["schema_version"],
                    evidence_pack["created_utc"],
                    json.dumps(evidence_pack["source_ref"]),
                    evidence_pack["normalized_text"],
                    json.dumps(evidence_pack["technical_metadata"]),
                    json.dumps(evidence_pack["integrity"]),
                    evidence_pack.get("sampling_policy_ref"),
                    json.dumps(evidence_pack.get("tags", []))
                ))
                
                # CRITICAL: Store canonical GeoJSON separately (for spatial queries)
                cur.execute("""
                    INSERT INTO geospatial_evidence (
                        evidence_id,
                        geo_json,
                        bounding_box,
                        geometry_types,
                        area_km2,
                        created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    evidence_pack["evidence_id"],
                    json.dumps(evidence_pack["technical_metadata"]["geo_json"]),  # NEW SCHEMA: in technical_metadata
                    evidence_pack["technical_metadata"].get("bounding_box"),
                    evidence_pack["technical_metadata"]["geometry_types"],
                    evidence_pack["technical_metadata"].get("area_km2"),
                    evidence_pack["created_utc"]  # NEW SCHEMA: created_utc
                ))
                
                self.postgres_agent.connection.commit()
                
        except Exception as e:
            logger.error(f"PostgreSQL persistence failed: {e}")
            if self.postgres_agent:
                self.postgres_agent.connection.rollback()
            raise
