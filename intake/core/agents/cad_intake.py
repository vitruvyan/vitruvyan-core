"""
AEGIS INTAKE — CAD/BIM Intake Agent

Media Scope: CAD files (DWG, DXF), BIM files (IFC, RVT)
Sources: AutoCAD, Revit, ArchiCAD, SketchUp exports

Use Cases:
- Warehouse layout analysis (DXF floor plans)
- Building Information Modeling (IFC facility data)
- 3D asset geometry (OBJ, FBX meshes)
- Coordinate system validation

Compliance: ACCORDO-FONDATIVO-INTAKE-V1.1

Key Principles:
- Extract entity metadata (layers, blocks, BIM elements)
- Support coordinate system extraction
- Preserve integrity hash (SHA-256)
- NO semantic interpretation (e.g., "optimal layout" forbidden)

Implementation: Phase 2 - CADIntakeAgent (Jan 11, 2026)
"""

import uuid
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import logging

# Intake guardrails
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from guardrails import IntakeGuardrails

# CAD/BIM libraries (conditional imports)
try:
    import ezdxf
    from ezdxf import bbox
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False
    print("⚠️ Warning: ezdxf not installed (pip install ezdxf)")

try:
    import ifcopenshell
    IFCOPENSHELL_AVAILABLE = True
except ImportError:
    IFCOPENSHELL_AVAILABLE = False
    print("⚠️ Warning: ifcopenshell not installed (pip install ifcopenshell)")


logger = logging.getLogger(__name__)


class CADIntakeAgent:
    """
    Pre-epistemic CAD/BIM file acquisition agent
    
    Responsibilities:
    - Extract CAD files (DXF, DWG) with ezdxf
    - Extract BIM files (IFC) with ifcopenshell
    - Parse layers, blocks, entities, coordinate systems
    - Link to geospatial evidence (via evidence_id reference)
    - Create immutable Evidence Pack
    - Emit intake.evidence.created event
    
    DOES NOT:
    - Interpret design intent ("this is a good layout")
    - Evaluate quality or suitability
    - Apply domain-specific heuristics
    - Call Codex directly
    """
    
    SUPPORTED_FORMATS = ['.dxf', '.dwg', '.ifc', '.rvt', '.obj', '.fbx', '.3ds']
    AGENT_ID = "cad-intake-v1"
    AGENT_VERSION = "1.0.0"
    
    def __init__(self, event_emitter, postgres_agent=None):
        """
        Args:
            event_emitter: IntakeEventEmitter instance
            postgres_agent: PostgresAgent for Evidence Pack persistence
        """
        self.event_emitter = event_emitter
        self.postgres_agent = postgres_agent
        self.guardrails = IntakeGuardrails()
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Log availability of CAD/BIM libraries"""
        logger.info(f"CAD Libraries: ezdxf={EZDXF_AVAILABLE}, ifcopenshell={IFCOPENSHELL_AVAILABLE}")
    
    def ingest(self, file_path: str, source_type: str = "document", 
               metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main ingestion entry point for CAD/BIM files
        
        Args:
            file_path: Path to CAD/BIM file
            source_type: "document" (CAD/BIM treated as structured documents)
            metadata: Optional user-provided metadata
        
        Returns:
            Evidence Pack dictionary
        
        Raises:
            ValueError: Unsupported file format or parsing error
        """
        logger.info(f"CAD Intake: Processing {file_path}")
        
        # Validate file
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Detect CAD type
        cad_type = self._detect_cad_type(file_path_obj)
        if not cad_type:
            raise ValueError(f"Unsupported file format: {file_path_obj.suffix}")
        
        # Extract metadata based on type
        if cad_type in ["dxf", "dwg"]:
            if not EZDXF_AVAILABLE:
                raise RuntimeError("ezdxf library not available. Install with: pip install ezdxf")
            technical_metadata = self._extract_dxf_metadata(file_path)
        elif cad_type == "ifc":
            if not IFCOPENSHELL_AVAILABLE:
                raise RuntimeError("ifcopenshell library not available. Install with: pip install ifcopenshell")
            technical_metadata = self._extract_ifc_metadata(file_path)
        else:
            # Fallback for unsupported types (OBJ, FBX, 3DS)
            technical_metadata = {"cad_type": cad_type, "parsing": "not_implemented"}
        
        # Generate literal text description
        literal_text = self._generate_literal_text(technical_metadata, file_path_obj)
        
        # Compute integrity hash
        integrity_hash = self._compute_hash(file_path)
        
        # Create Evidence Pack
        evidence_pack = self._create_evidence_pack(
            file_path=file_path_obj,
            cad_type=cad_type,
            technical_metadata=technical_metadata,
            literal_text=literal_text,
            integrity_hash=integrity_hash,
            user_metadata=metadata
        )
        
        # Persist to PostgreSQL
        if self.postgres_agent:
            self._persist_to_postgresql(evidence_pack)
        
        # Emit event to Redis
        file_path_obj = Path(file_path) if not isinstance(file_path, Path) else file_path
        self.event_emitter.emit_evidence_created(
            evidence_id=evidence_pack["evidence_id"],
            chunk_id="FULL",
            source_type=source_type,
            source_uri=evidence_pack["source_ref"]["source_uri"],
            evidence_pack_ref=f"evidence_packs/{evidence_pack['evidence_id']}",
            source_hash=integrity_hash,
            intake_agent_id=self.AGENT_ID,
            intake_agent_version=self.AGENT_VERSION,
            byte_size=file_path_obj.stat().st_size
        )
        
        logger.info(f"CAD Intake: Created Evidence Pack {evidence_pack['evidence_id']}")
        return evidence_pack
    
    def _detect_cad_type(self, file_path: Path) -> Optional[str]:
        """
        Detect CAD/BIM file type from extension
        
        Args:
            file_path: Path object
        
        Returns:
            "dxf" | "dwg" | "ifc" | "rvt" | "obj" | "fbx" | "3ds" | None
        """
        ext = file_path.suffix.lower()
        
        if ext == ".dxf":
            return "dxf"
        elif ext == ".dwg":
            return "dwg"
        elif ext == ".ifc":
            return "ifc"
        elif ext == ".rvt":
            return "rvt"
        elif ext == ".obj":
            return "obj"
        elif ext == ".fbx":
            return "fbx"
        elif ext == ".3ds":
            return "3ds"
        else:
            return None
    
    def _extract_dxf_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from DXF/DWG file using ezdxf
        
        Args:
            file_path: Path to DXF file
        
        Returns:
            Dictionary with layers, entities, blocks, bounds, units
        """
        try:
            doc = ezdxf.readfile(file_path)
            modelspace = doc.modelspace()
            
            # Extract layers
            layers = []
            for layer in doc.layers:
                entity_count = sum(1 for e in modelspace if e.dxf.layer == layer.dxf.name)
                layers.append({
                    "name": layer.dxf.name,
                    "entity_count": entity_count,
                    "color": layer.dxf.color,
                    "frozen": layer.is_frozen()
                })
            
            # Count entity types
            entity_counts = {}
            for entity in modelspace:
                entity_type = entity.dxftype()
                entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            
            # Extract blocks
            blocks = []
            for block in doc.blocks:
                if not block.name.startswith('*'):  # Skip model/paper space
                    block_refs = list(modelspace.query(f'INSERT[name=="{block.name}"]'))
                    blocks.append({
                        "name": block.name,
                        "instances": len(block_refs)
                    })
            
            # Extract bounding box
            try:
                extents = bbox.extents(modelspace)
                bounds = [extents.extmin.x, extents.extmin.y, extents.extmin.z,
                         extents.extmax.x, extents.extmax.y, extents.extmax.z]
            except Exception as e:
                logger.warning(f"Could not compute bounds: {e}")
                bounds = None
            
            # Extract units (from header)
            try:
                insunits = doc.header.get('$INSUNITS', 0)
                units_map = {
                    0: "unitless",
                    1: "inches",
                    2: "feet",
                    4: "millimeters",
                    5: "centimeters",
                    6: "meters",
                    14: "miles"
                }
                units = units_map.get(insunits, "unknown")
            except Exception:
                units = "unknown"
            
            # CAD version
            cad_version = doc.header.get('$ACADVER', 'unknown')
            
            return {
                "cad_type": "dxf",
                "cad_version": cad_version,
                "units": units,
                "coordinate_system": "Local",
                "bounds": bounds,
                "layers": layers,
                "entity_counts": entity_counts,
                "blocks": blocks,
                "total_entities": len(list(modelspace))
            }
        
        except Exception as e:
            logger.error(f"Error parsing DXF: {e}")
            return {
                "cad_type": "dxf",
                "error": str(e),
                "parsing": "failed"
            }
    
    def _extract_ifc_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from IFC file using ifcopenshell
        
        Args:
            file_path: Path to IFC file
        
        Returns:
            Dictionary with BIM elements, building hierarchy, property sets
        """
        try:
            ifc_file = ifcopenshell.open(file_path)
            
            # IFC schema version
            bim_schema = ifc_file.schema
            
            # Count BIM elements
            bim_elements = {}
            element_types = [
                "IfcWall", "IfcSlab", "IfcDoor", "IfcWindow", 
                "IfcColumn", "IfcBeam", "IfcStair", "IfcRoof",
                "IfcSpace", "IfcCovering", "IfcRailing", "IfcFurnishingElement"
            ]
            for elem_type in element_types:
                elements = ifc_file.by_type(elem_type)
                if elements:
                    bim_elements[elem_type] = len(elements)
            
            # Building hierarchy
            buildings = ifc_file.by_type("IfcBuilding")
            storeys = ifc_file.by_type("IfcBuildingStorey")
            spaces = ifc_file.by_type("IfcSpace")
            sites = ifc_file.by_type("IfcSite")
            
            building_hierarchy = {
                "sites": len(sites),
                "buildings": len(buildings),
                "storeys": len(storeys),
                "spaces": len(spaces)
            }
            
            # Extract project units
            try:
                project = ifc_file.by_type("IfcProject")[0]
                units_in_context = project.UnitsInContext
                if units_in_context:
                    unit = units_in_context.Units[0]
                    if hasattr(unit, 'Prefix'):
                        units = f"{unit.Prefix}{unit.Name}".lower()
                    else:
                        units = unit.Name.lower() if hasattr(unit, 'Name') else "unknown"
                else:
                    units = "unknown"
            except Exception:
                units = "unknown"
            
            # Extract bounding box (simplified)
            try:
                # Attempt to get site coordinates
                if sites:
                    site = sites[0]
                    if hasattr(site, 'RefLatitude') and site.RefLatitude:
                        lat = self._convert_ifc_angle(site.RefLatitude)
                        lon = self._convert_ifc_angle(site.RefLongitude)
                        bounds = [lon, lat, 0.0, lon, lat, 0.0]
                        coordinate_system = "WGS84"
                    else:
                        bounds = None
                        coordinate_system = "Local"
                else:
                    bounds = None
                    coordinate_system = "Local"
            except Exception as e:
                logger.warning(f"Could not extract coordinates: {e}")
                bounds = None
                coordinate_system = "Local"
            
            # Property sets (sample first building)
            property_sets = []
            if buildings:
                building = buildings[0]
                if hasattr(building, 'IsDefinedBy'):
                    for definition in building.IsDefinedBy:
                        if definition.is_a('IfcRelDefinesByProperties'):
                            prop_set = definition.RelatingPropertyDefinition
                            if prop_set.is_a('IfcPropertySet'):
                                props = {}
                                for prop in prop_set.HasProperties:
                                    if hasattr(prop, 'NominalValue'):
                                        props[prop.Name] = str(prop.NominalValue.wrappedValue)
                                property_sets.append({
                                    "name": prop_set.Name,
                                    "properties": props
                                })
            
            return {
                "cad_type": "ifc",
                "bim_schema": bim_schema,
                "units": units,
                "coordinate_system": coordinate_system,
                "bounds": bounds,
                "building_hierarchy": building_hierarchy,
                "bim_elements": bim_elements,
                "property_sets": property_sets[:3],  # Limit to first 3
                "total_elements": sum(bim_elements.values())
            }
        
        except Exception as e:
            logger.error(f"Error parsing IFC: {e}")
            return {
                "cad_type": "ifc",
                "error": str(e),
                "parsing": "failed"
            }
    
    def _convert_ifc_angle(self, angle_tuple: Tuple) -> float:
        """
        Convert IFC angle tuple (degrees, minutes, seconds) to decimal degrees
        
        Args:
            angle_tuple: (degrees, minutes, seconds, millionths)
        
        Returns:
            Decimal degrees
        """
        if not angle_tuple or len(angle_tuple) < 3:
            return 0.0
        
        degrees = angle_tuple[0]
        minutes = angle_tuple[1]
        seconds = angle_tuple[2]
        
        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
        return decimal
    
    def _generate_literal_text(self, technical_metadata: Dict[str, Any], 
                               file_path: Path) -> str:
        """
        Generate human-readable description of CAD/BIM file
        
        Args:
            technical_metadata: Parsed metadata
            file_path: Path object
        
        Returns:
            Descriptive text string
        """
        cad_type = technical_metadata.get("cad_type", "unknown")
        filename = file_path.name
        
        if cad_type == "dxf":
            layers = technical_metadata.get("layers", [])
            entities = technical_metadata.get("total_entities", 0)
            units = technical_metadata.get("units", "unknown")
            
            layer_names = [l["name"] for l in layers[:5]]  # First 5 layers
            layer_text = ", ".join(layer_names)
            if len(layers) > 5:
                layer_text += f" (and {len(layers) - 5} more)"
            
            return (f"CAD drawing file: {filename}. "
                   f"Contains {entities} entities across {len(layers)} layers ({layer_text}). "
                   f"Units: {units}. "
                   f"Format: AutoCAD DXF.")
        
        elif cad_type == "ifc":
            schema = technical_metadata.get("bim_schema", "unknown")
            hierarchy = technical_metadata.get("building_hierarchy", {})
            elements = technical_metadata.get("bim_elements", {})
            
            buildings = hierarchy.get("buildings", 0)
            storeys = hierarchy.get("storeys", 0)
            spaces = hierarchy.get("spaces", 0)
            
            element_summary = ", ".join([f"{k.replace('Ifc', '')}: {v}" 
                                        for k, v in list(elements.items())[:5]])
            
            return (f"BIM model file: {filename}. "
                   f"Schema: {schema}. "
                   f"Contains {buildings} building(s), {storeys} storey(s), {spaces} space(s). "
                   f"Elements: {element_summary}.")
        
        else:
            return f"CAD/BIM file: {filename}. Type: {cad_type}. Format not yet fully supported."
    
    def _compute_hash(self, file_path: str) -> str:
        """
        Compute SHA-256 hash of file for integrity verification
        
        Args:
            file_path: Path to file
        
        Returns:
            SHA-256 hash (hex string)
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(8192), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _create_evidence_pack(self, file_path: Path, cad_type: str,
                             technical_metadata: Dict[str, Any],
                             literal_text: str, integrity_hash: str,
                             user_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create Evidence Pack following ACCORDO-FONDATIVO-INTAKE-V1.1
        
        Args:
            file_path: Path object
            cad_type: "dxf" | "ifc" | etc.
            technical_metadata: Parsed metadata
            literal_text: Human-readable description
            integrity_hash: SHA-256 hash
            user_metadata: Optional user-provided metadata
        
        Returns:
            Evidence Pack dictionary
        """
        evidence_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        evidence_pack = {
            "evidence_id": evidence_id,
            "agent_id": self.AGENT_ID,
            "agent_version": self.AGENT_VERSION,
            "created_at": timestamp,
            "source_ref": {
                "source_type": "cad_file",
                "source_uri": f"file://{file_path.absolute()}",
                "source_hash": integrity_hash,
                "fragment_type": cad_type
            },
            "technical_metadata": technical_metadata,
            "integrity": {
                "hash_algorithm": "SHA-256",
                "hash_value": integrity_hash,
                "verified_at": timestamp
            },
            "normalized_text": literal_text,
            "user_metadata": user_metadata or {}
        }
        
        return evidence_pack
    
    def _persist_to_postgresql(self, evidence_pack: Dict[str, Any]):
        """
        Persist Evidence Pack to PostgreSQL evidence_packs table
        
        Args:
            evidence_pack: Evidence Pack dictionary
        """
        if not self.postgres_agent:
            logger.warning("PostgresAgent not configured, skipping persistence")
            return
        
        try:
            with self.postgres_agent.connection.cursor() as cur:
                insert_sql = """
                INSERT INTO evidence_packs (
                    evidence_id, 
                    agent_id, 
                    agent_version,
                    created_at,
                    source_ref,
                    technical_metadata,
                    integrity,
                    normalized_text,
                    user_metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cur.execute(insert_sql, (
                    evidence_pack["evidence_id"],
                    evidence_pack["agent_id"],
                    evidence_pack["agent_version"],
                    evidence_pack["created_at"],
                    json.dumps(evidence_pack["source_ref"]),
                    json.dumps(evidence_pack["technical_metadata"]),
                    json.dumps(evidence_pack["integrity"]),
                    evidence_pack["normalized_text"],
                    json.dumps(evidence_pack["user_metadata"])
                ))
                self.postgres_agent.connection.commit()
                logger.info(f"Evidence Pack {evidence_pack['evidence_id']} persisted to PostgreSQL")
        
        except Exception as e:
            logger.error(f"Error persisting to PostgreSQL: {e}")
            self.postgres_agent.connection.rollback()
            raise
