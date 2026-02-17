"""
AEGIS INTAKE — Document Intake Agent

Media Scope: PDF, DOCX, MD, TXT, JSON, XML
Constraints: NO semantic inference, NO relevance judgment

Compliance: ACCORDO-FONDATIVO-INTAKE-V1.1

Key Principles:
- Extract text literally (descriptive, not interpretative)
- Preserve raw reference + hash
- Emit Evidence Pack + event
- NO domain-specific logic
"""

import uuid
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

# Intake guardrails
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from guardrails import IntakeGuardrails

# Document processing libraries (conditional imports)
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False


logger = logging.getLogger(__name__)


class DocumentIntakeAgent:
    """
    Pre-epistemic document acquisition agent
    
    Responsibilities:
    - Extract text from documents (PDF, DOCX, MD, TXT, JSON, XML)
    - Generate normalized_text (descriptive-literal only)
    - Create immutable Evidence Pack
    - Emit intake.evidence.created event
    
    DOES NOT:
    - Interpret content semantically
    - Evaluate relevance or importance
    - Apply domain-specific rules
    - Call Codex directly
    """
    
    SUPPORTED_FORMATS = ['.pdf', '.docx', '.md', '.txt', '.json', '.xml']
    AGENT_ID = "doc-intake-v1"
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
        """Check availability of document processing libraries"""
        missing = []
        if not PDFPLUMBER_AVAILABLE:
            missing.append("pdfplumber")
        if not DOCX_AVAILABLE:
            missing.append("python-docx")
        if not MARKDOWN_AVAILABLE:
            missing.append("markdown")
        
        if missing:
            logger.warning(f"Missing optional dependencies: {', '.join(missing)}")
    
    def ingest_document(
        self,
        source_path: str,
        chunking_strategy: str = "none",
        chunk_size: int = 4000,
        sampling_policy_ref: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> List[str]:
        """
        Ingest document and create Evidence Pack(s)
        
        Args:
            source_path: Path to document file
            chunking_strategy: 'none', 'page', 'size' (character count)
            chunk_size: Max characters per chunk (if strategy='size')
            sampling_policy_ref: Reference to external Sampling Policy
            correlation_id: Distributed tracing ID
        
        Returns:
            List of evidence_ids created
        
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
        
        # Extract text
        try:
            extracted_text = self._extract_text(source_path)
        except Exception as e:
            logger.error(f"Text extraction failed for {source_path}: {e}")
            raise ValueError(f"Text extraction failed: {e}")
        
        # Detect language (simple heuristic)
        language_detected = self._detect_language_simple(extracted_text)
        
        # Chunking
        chunks = self._chunk_text(extracted_text, chunking_strategy, chunk_size)
        
        # Create Evidence Packs
        evidence_ids = []
        for chunk_idx, chunk_text in enumerate(chunks):
            evidence_id = self._generate_evidence_id()
            chunk_id = f"CHK-{chunk_idx}"
            
            # Build Evidence Pack
            evidence_pack = {
                "evidence_id": evidence_id,
                "chunk_id": chunk_id,
                "schema_version": "1.0.0",
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "source_ref": {
                    "source_type": "document",
                    "source_uri": str(source_path.absolute()),
                    "source_hash": source_hash,
                    "mime_type": mime_type,
                    "byte_size": byte_size
                },
                "normalized_text": chunk_text,
                "technical_metadata": {
                    "extraction_method": self._get_extraction_method(source_path),
                    "extraction_version": self.AGENT_VERSION,
                    "language_detected": language_detected,
                    "confidence_score": 1.0,  # Text extraction is deterministic
                    "chunk_position": {
                        "start_offset": chunk_idx * chunk_size if chunking_strategy == "size" else 0,
                        "end_offset": (chunk_idx + 1) * chunk_size if chunking_strategy == "size" else len(chunk_text),
                        "total_chunks": len(chunks)
                    }
                },
                "integrity": {
                    "evidence_hash": self._compute_evidence_hash(evidence_id, chunk_id, chunk_text, source_hash),
                    "immutable": True
                },
                "sampling_policy_ref": sampling_policy_ref,
                "tags": []
            }
            
            # ✅ HARDENING: Validate no semantic interpretation
            try:
                IntakeGuardrails.validate_no_semantics(chunk_text, "document")
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
                source_type="document",
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
            
            evidence_ids.append(evidence_id)
        
        return evidence_ids
    
    def _extract_text(self, source_path: Path) -> str:
        """
        Extract text from document (format-specific)
        
        Returns descriptive-literal text only. NO interpretation.
        """
        suffix = source_path.suffix.lower()
        
        if suffix == '.pdf':
            return self._extract_pdf(source_path)
        elif suffix == '.docx':
            return self._extract_docx(source_path)
        elif suffix == '.md':
            return self._extract_markdown(source_path)
        elif suffix == '.txt':
            return self._extract_txt(source_path)
        elif suffix == '.json':
            return self._extract_json(source_path)
        elif suffix == '.xml':
            return self._extract_xml(source_path)
        else:
            raise ValueError(f"No extraction method for: {suffix}")
    
    def _extract_pdf(self, source_path: Path) -> str:
        """Extract text from PDF (literal only)"""
        if not PDFPLUMBER_AVAILABLE:
            raise ValueError("pdfplumber not installed. Cannot process PDF.")
        
        text_parts = []
        with pdfplumber.open(source_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        
        return "\n\n".join(text_parts)
    
    def _extract_docx(self, source_path: Path) -> str:
        """Extract text from DOCX (literal only)"""
        if not DOCX_AVAILABLE:
            raise ValueError("python-docx not installed. Cannot process DOCX.")
        
        doc = DocxDocument(source_path)
        return "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    
    def _extract_markdown(self, source_path: Path) -> str:
        """Extract text from Markdown (preserve structure)"""
        with open(source_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _extract_txt(self, source_path: Path) -> str:
        """Extract text from TXT (as-is)"""
        with open(source_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    
    def _extract_json(self, source_path: Path) -> str:
        """Extract text from JSON (structured representation)"""
        with open(source_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Return pretty-printed JSON as normalized text
        return json.dumps(data, indent=2)
    
    def _extract_xml(self, source_path: Path) -> str:
        """Extract text from XML (as-is)"""
        with open(source_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _chunk_text(self, text: str, strategy: str, chunk_size: int) -> List[str]:
        """
        Chunk text according to strategy
        
        Strategies:
        - 'none': No chunking (single chunk)
        - 'size': Split by character count
        - 'page': Not applicable for text (fallback to 'none')
        """
        if strategy == "none" or strategy == "page":
            return [text]
        elif strategy == "size":
            if not text:
                return [""]
            return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")
    
    def _detect_language_simple(self, text: str) -> str:
        """
        Simple language detection heuristic
        
        Returns ISO 639-1 code (e.g., 'en', 'it', 'fr')
        Fallback: 'unknown'
        """
        # Placeholder: use simple heuristics or external library (langdetect)
        # For now, assume English if ASCII-heavy, else unknown
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
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.md': 'text/markdown',
            '.txt': 'text/plain',
            '.json': 'application/json',
            '.xml': 'application/xml'
        }
        return mime_map.get(source_path.suffix.lower(), 'application/octet-stream')
    
    def _get_extraction_method(self, source_path: Path) -> str:
        """Get extraction method name"""
        method_map = {
            '.pdf': 'pdfplumber',
            '.docx': 'python-docx',
            '.md': 'builtin',
            '.txt': 'builtin',
            '.json': 'builtin',
            '.xml': 'builtin'
        }
        return method_map.get(source_path.suffix.lower(), 'unknown')
    
    def _persist_evidence_pack(self, evidence_pack: Dict[str, Any]) -> str:
        """
        Persist Evidence Pack to PostgreSQL (append-only)
        
        Returns reference to persisted pack
        """
        if not self.postgres_agent:
            # Fallback: return mock reference
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
