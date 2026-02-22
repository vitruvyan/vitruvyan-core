"""
Vitruvyan INTAKE — Image Intake Agent

Media Scope: JPG, PNG, TIFF, BMP, GIF
Constraints: OCR + literal caption ONLY, NO evaluative adjectives

Compliance: ACCORDO-FONDATIVO-INTAKE-V1.1

Key Principles:
- Extract text via OCR (literal only)
- Generate descriptive-literal caption (NO interpretation)
- NO domain inference ("military vehicle" → "vehicle")
- Handle empty text gracefully (normalized_text can be "")
"""

import uuid
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from vitruvyan_edge.oculus_prime.core.guardrails import IntakeGuardrails

# Image processing libraries (conditional imports)
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False


logger = logging.getLogger(__name__)


class ImageIntakeAgent:
    """
    Pre-epistemic image acquisition agent
    
    Responsibilities:
    - Extract text via OCR (literal only)
    - Generate descriptive-literal caption
    - Create immutable Evidence Pack
    - Emit oculus_prime.evidence.created event (legacy alias: intake.evidence.created)
    
    DOES NOT:
    - Infer domain context (military, medical, etc.)
    - Use evaluative adjectives (dangerous, suspicious, etc.)
    - Classify objects semantically
    - Call Codex directly
    
    Captioning Rules (STRICT):
    - Describe visible elements literally
    - Use generic terms ("vehicle" not "tank", "person" not "soldier")
    - State positions/counts objectively ("3 vehicles", "building on left")
    - NEVER infer intent, emotion, or context
    """
    
    SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif']
    AGENT_ID = "image-intake-v1"
    AGENT_VERSION = "1.0.0"
    
    def __init__(self, event_emitter, postgres_agent=None):
        """
        Args:
            event_emitter: IntakeEventEmitter instance
            postgres_agent: PostgresAgent for Evidence Pack persistence
        """
        self.event_emitter = event_emitter
        self.postgres_agent = postgres_agent
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check availability of image processing libraries"""
        if not PIL_AVAILABLE:
            logger.warning("PIL/Pillow not installed. Image processing unavailable.")
        if not PYTESSERACT_AVAILABLE:
            logger.warning("pytesseract not installed. OCR unavailable.")
    
    def ingest_image(
        self,
        source_path: str,
        enable_ocr: bool = True,
        enable_caption: bool = True,
        sampling_policy_ref: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Ingest image and create Evidence Pack
        
        Args:
            source_path: Path to image file
            enable_ocr: Extract text via OCR
            enable_caption: Generate literal caption
            sampling_policy_ref: Reference to external Sampling Policy
            correlation_id: Distributed tracing ID
        
        Returns:
            evidence_id created
        
        Raises:
            ValueError: If file format unsupported or unreadable
        """
        source_path = Path(source_path)
        
        # Validate file exists and format supported
        if not source_path.exists():
            raise ValueError(f"Source file not found: {source_path}")
        
        if source_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {source_path.suffix}. Supported: {self.SUPPORTED_FORMATS}")
        
        # Compute source hash
        source_hash = self._compute_file_hash(source_path)
        byte_size = source_path.stat().st_size
        mime_type = self._get_mime_type(source_path)
        
        # Open image
        try:
            image = Image.open(source_path)
            image_width, image_height = image.size
            image_format = image.format
        except Exception as e:
            logger.error(f"Image loading failed for {source_path}: {e}")
            raise ValueError(f"Image loading failed: {e}")
        
        # Extract text (OCR)
        ocr_text = ""
        ocr_confidence = 0.0
        if enable_ocr and PYTESSERACT_AVAILABLE:
            try:
                ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                # Filter confident text only (conf > 60)
                confident_words = [
                    ocr_data['text'][i]
                    for i in range(len(ocr_data['text']))
                    if int(ocr_data['conf'][i]) > 60 and ocr_data['text'][i].strip()
                ]
                ocr_text = " ".join(confident_words)
                if confident_words:
                    ocr_confidence = sum(
                        int(ocr_data['conf'][i]) for i in range(len(ocr_data['text']))
                        if int(ocr_data['conf'][i]) > 60 and ocr_data['text'][i].strip()
                    ) / len(confident_words) / 100.0
            except Exception as e:
                logger.warning(f"OCR failed for {source_path}: {e}")
        
        # Generate caption (literal only)
        caption_text = ""
        if enable_caption:
            caption_text = self._generate_literal_caption(image, source_path)
        
        # Combine OCR + caption as normalized_text
        normalized_text_parts = []
        if ocr_text:
            normalized_text_parts.append(f"[OCR] {ocr_text}")
        if caption_text:
            normalized_text_parts.append(f"[CAPTION] {caption_text}")
        
        normalized_text = "\n".join(normalized_text_parts) if normalized_text_parts else ""
        
        # Language detection (if OCR text present)
        language_detected = "unknown"
        if ocr_text:
            language_detected = self._detect_language_simple(ocr_text)
        
        # Create Evidence Pack
        evidence_id = self._generate_evidence_id()
        chunk_id = "CHK-0"  # Images are single-chunk
        
        evidence_pack = {
            "evidence_id": evidence_id,
            "chunk_id": chunk_id,
            "schema_version": "1.0.0",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "source_ref": {
                "source_type": "image",
                "source_uri": str(source_path.absolute()),
                "source_hash": source_hash,
                "mime_type": mime_type,
                "byte_size": byte_size
            },
            "normalized_text": normalized_text,
            "technical_metadata": {
                "extraction_method": "pytesseract+pil" if PYTESSERACT_AVAILABLE else "pil",
                "extraction_version": self.AGENT_VERSION,
                "language_detected": language_detected,
                "confidence_score": ocr_confidence,
                "chunk_position": {
                    "start_offset": 0,
                    "end_offset": len(normalized_text),
                    "total_chunks": 1
                },
                "image_metadata": {
                    "width": image_width,
                    "height": image_height,
                    "format": image_format,
                    "mode": image.mode
                }
            },
            "integrity": {
                "evidence_hash": self._compute_evidence_hash(evidence_id, chunk_id, normalized_text, source_hash),
                "immutable": True
            },
            "sampling_policy_ref": sampling_policy_ref,
            "tags": []
        }
        
        # ✅ HARDENING: Validate no semantic interpretation
        try:
            IntakeGuardrails.validate_no_semantics(normalized_text, "image")
            IntakeGuardrails.validate_source_hash_required(evidence_pack["source_ref"])
        except Exception as e:
            logger.error(f"Guardrail violation: {e}")
            raise
        
        # Persist Evidence Pack (append-only)
        evidence_pack_ref = self._persist_evidence_pack(evidence_pack)
        
        # Emit event
        self.event_emitter.emit_evidence_created(
            evidence_id=evidence_id,
            chunk_id=chunk_id,
            source_type="image",
            source_uri=str(source_path.absolute()),
            evidence_pack_ref=evidence_pack_ref,
            source_hash=source_hash,
            intake_agent_id=self.AGENT_ID,
            intake_agent_version=self.AGENT_VERSION,
            byte_size=byte_size,
            language_detected=language_detected,
            sampling_policy_ref=sampling_policy_ref,
            correlation_id=correlation_id
        )
        
        return evidence_id
    
    def _generate_literal_caption(self, image: Image.Image, source_path: Path) -> str:
        """
        Generate descriptive-literal caption
        
        STRICT RULES:
        - Generic terms only ("vehicle" not "military vehicle")
        - Objective counts/positions ("3 objects in center")
        - NO evaluative adjectives ("dangerous", "suspicious")
        - NO domain inference ("military", "medical")
        - NO emotion/intent attribution
        
        Fallback: Basic image properties if no advanced captioning available
        """
        # Placeholder: In production, use vision model with constrained prompt
        # For now, return basic properties
        width, height = image.size
        mode = image.mode
        
        # Count dominant colors (simple heuristic)
        try:
            colors = image.getcolors(maxcolors=10)
            if colors:
                dominant_color_count = len(colors)
            else:
                dominant_color_count = "many"
        except Exception:
            dominant_color_count = "unknown"
        
        # Build literal caption
        caption_parts = [
            f"Image dimensions: {width}x{height} pixels",
            f"Color mode: {mode}",
            f"Dominant colors: {dominant_color_count}"
        ]
        
        # Check for text presence (OCR handled separately)
        # This is just basic metadata, not interpretation
        
        return ". ".join(caption_parts) + "."
    
    def _detect_language_simple(self, text: str) -> str:
        """Simple language detection (same as document agent)"""
        if not text.strip():
            return "unknown"
        
        ascii_ratio = sum(1 for c in text if ord(c) < 128) / len(text)
        return "en" if ascii_ratio > 0.7 else "unknown"
    
    def _compute_file_hash(self, source_path: Path) -> str:
        """Compute SHA-256 hash of file"""
        sha256 = hashlib.sha256()
        with open(source_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return f"sha256:{sha256.hexdigest()}"
    
    def _compute_evidence_hash(self, evidence_id: str, chunk_id: str, text: str, source_hash: str) -> str:
        """Compute evidence integrity hash"""
        composite = f"{evidence_id}{chunk_id}{text}{source_hash}"
        return f"sha256:{hashlib.sha256(composite.encode('utf-8')).hexdigest()}"
    
    def _generate_evidence_id(self) -> str:
        """Generate unique Evidence ID"""
        uid = uuid.uuid4()
        return f"EVD-{uid.hex.upper()[:8]}-{uid.hex.upper()[8:12]}-{uid.hex.upper()[12:16]}-{uid.hex.upper()[16:20]}-{uid.hex.upper()[20:32]}"
    
    def _get_mime_type(self, source_path: Path) -> str:
        """Get MIME type from file extension"""
        mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff',
            '.bmp': 'image/bmp',
            '.gif': 'image/gif'
        }
        return mime_map.get(source_path.suffix.lower(), 'application/octet-stream')
    
    def _persist_evidence_pack(self, evidence_pack: Dict[str, Any]) -> str:
        """Persist Evidence Pack to PostgreSQL (append-only)"""
        if not self.postgres_agent:
            return f"mock://evidence_packs/{evidence_pack['evidence_id']}"
        
        try:
            with self.postgres_agent.connection.cursor() as cur:
                cur.execute("""
                    INSERT INTO evidence_packs (
                        evidence_id, chunk_id, schema_version, created_utc,
                        source_ref, normalized_text, technical_metadata,
                        integrity, sampling_policy_ref, tags
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    evidence_pack['evidence_id'],
                    evidence_pack['chunk_id'],
                    evidence_pack['schema_version'],
                    evidence_pack['created_utc'],
                    json.dumps(evidence_pack['source_ref']),
                    evidence_pack['normalized_text'],
                    json.dumps(evidence_pack['technical_metadata']),
                    json.dumps(evidence_pack['integrity']),
                    evidence_pack.get('sampling_policy_ref'),
                    json.dumps(evidence_pack.get('tags', []))
                ))
                row_id = cur.fetchone()[0]
            self.postgres_agent.connection.commit()
            return f"postgres://evidence_packs/{row_id}"
        except Exception as e:
            logger.error(f"Failed to persist Evidence Pack: {e}")
            return f"error://failed_to_persist/{evidence_pack['evidence_id']}"
