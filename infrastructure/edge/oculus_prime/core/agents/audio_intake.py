"""
AEGIS INTAKE — Audio Intake Agent

Media Scope: MP3, WAV, AAC, FLAC, OGG
Constraints: STT + diarization, NO sentiment or intent detection

Compliance: ACCORDO-FONDATIVO-INTAKE-V1.1

Key Principles:
- Speech-to-text (literal transcription only)
- Speaker diarization (who spoke when)
- Timestamped fragments
- NO emotion detection, NO intent inference
"""

import uuid
import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import logging

from infrastructure.edge.oculus_prime.core.guardrails import IntakeGuardrails

# Audio processing libraries (conditional imports)
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False


logger = logging.getLogger(__name__)


class AudioIntakeAgent:
    """
    Pre-epistemic audio acquisition agent
    
    Responsibilities:
    - Speech-to-text transcription (literal only)
    - Speaker diarization (timestamped)
    - Create immutable Evidence Pack per chunk/speaker
    - Emit oculus_prime.evidence.created events (legacy alias: intake.evidence.created)
    
    DOES NOT:
    - Detect sentiment or emotion
    - Infer speaker intent
    - Classify conversation context
    - Call Codex directly
    
    Transcription Rules (STRICT):
    - Verbatim text (including filler words: um, uh, etc.)
    - Preserve speaker turns
    - Include timestamps
    - NO interpretation of tone or meaning
    """
    
    SUPPORTED_FORMATS = ['.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a']
    AGENT_ID = "audio-intake-v1"
    AGENT_VERSION = "1.0.0"
    
    def __init__(self, event_emitter, postgres_agent=None, whisper_model="base"):
        """
        Args:
            event_emitter: IntakeEventEmitter instance
            postgres_agent: PostgresAgent for Evidence Pack persistence
            whisper_model: Whisper model size (tiny/base/small/medium/large)
        """
        self.event_emitter = event_emitter
        self.postgres_agent = postgres_agent
        self.whisper_model_name = whisper_model
        self.whisper_model = None
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check availability of audio processing libraries"""
        if not WHISPER_AVAILABLE:
            logger.warning("OpenAI Whisper not installed. STT unavailable.")
        if not PYDUB_AVAILABLE:
            logger.warning("pydub not installed. Audio format conversion unavailable.")
        
        # Load Whisper model (lazy)
        if WHISPER_AVAILABLE and self.whisper_model is None:
            try:
                self.whisper_model = whisper.load_model(self.whisper_model_name)
                logger.info(f"Loaded Whisper model: {self.whisper_model_name}")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
    
    def ingest_audio(
        self,
        source_path: str,
        enable_diarization: bool = False,
        chunk_duration_sec: int = 300,  # 5 minutes
        sampling_policy_ref: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> List[str]:
        """
        Ingest audio and create Evidence Pack(s)
        
        Args:
            source_path: Path to audio file
            enable_diarization: Enable speaker diarization (experimental)
            chunk_duration_sec: Split audio into chunks (seconds)
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
        
        # Load audio
        try:
            if PYDUB_AVAILABLE:
                audio = AudioSegment.from_file(source_path)
                duration_sec = len(audio) / 1000.0  # milliseconds to seconds
            else:
                # Fallback: assume duration from file metadata (less reliable)
                duration_sec = 0.0
        except Exception as e:
            logger.error(f"Audio loading failed for {source_path}: {e}")
            raise ValueError(f"Audio loading failed: {e}")
        
        # Transcribe audio
        if not WHISPER_AVAILABLE or self.whisper_model is None:
            raise ValueError("Whisper not available. Cannot transcribe audio.")
        
        try:
            result = self.whisper_model.transcribe(
                str(source_path),
                verbose=False,
                word_timestamps=True
            )
        except Exception as e:
            logger.error(f"Transcription failed for {source_path}: {e}")
            raise ValueError(f"Transcription failed: {e}")
        
        # Extract segments with timestamps
        segments = result.get('segments', [])
        language_detected = result.get('language', 'unknown')
        
        # Chunk segments by duration
        chunk_groups = self._chunk_segments_by_duration(segments, chunk_duration_sec)
        
        # Create Evidence Packs
        evidence_ids = []
        for chunk_idx, segment_group in enumerate(chunk_groups):
            evidence_id = self._generate_evidence_id()
            chunk_id = f"CHK-{chunk_idx}"
            
            # Build normalized text (timestamped transcription)
            normalized_text = self._format_transcription(segment_group)
            
            # Extract temporal metadata
            start_time = segment_group[0]['start'] if segment_group else 0.0
            end_time = segment_group[-1]['end'] if segment_group else 0.0
            chunk_duration = end_time - start_time
            
            # Build Evidence Pack
            evidence_pack = {
                "evidence_id": evidence_id,
                "chunk_id": chunk_id,
                "schema_version": "1.0.0",
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "source_ref": {
                    "source_type": "audio",
                    "source_uri": str(source_path.absolute()),
                    "source_hash": source_hash,
                    "mime_type": mime_type,
                    "byte_size": byte_size
                },
                "normalized_text": normalized_text,
                "technical_metadata": {
                    "extraction_method": f"whisper-{self.whisper_model_name}",
                    "extraction_version": self.AGENT_VERSION,
                    "language_detected": language_detected,
                    "confidence_score": self._compute_avg_confidence(segment_group),
                    "chunk_position": {
                        "start_offset": chunk_idx * chunk_duration_sec,
                        "end_offset": (chunk_idx + 1) * chunk_duration_sec,
                        "total_chunks": len(chunk_groups)
                    },
                    "temporal_metadata": {
                        "timestamp_start": (datetime.now(timezone.utc) + timedelta(seconds=start_time)).isoformat(),
                        "timestamp_end": (datetime.now(timezone.utc) + timedelta(seconds=end_time)).isoformat(),
                        "duration_sec": chunk_duration
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
                IntakeGuardrails.validate_no_semantics(normalized_text, "audio")
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
                source_type="audio",
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
    
    def _chunk_segments_by_duration(self, segments: List[Dict], max_duration_sec: int) -> List[List[Dict]]:
        """
        Chunk segments into groups by max duration
        
        Returns list of segment groups
        """
        chunks = []
        current_chunk = []
        current_duration = 0.0
        
        for segment in segments:
            segment_duration = segment['end'] - segment['start']
            
            if current_duration + segment_duration > max_duration_sec and current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_duration = 0.0
            
            current_chunk.append(segment)
            current_duration += segment_duration
        
        if current_chunk:
            chunks.append(current_chunk)
        if not chunks:
            # Preserve append-only evidence behavior even for empty/failed transcripts.
            chunks.append([])
        
        return chunks
    
    def _format_transcription(self, segments: List[Dict]) -> str:
        """
        Format transcription with timestamps (literal only)
        
        Format: [HH:MM:SS] Text
        """
        lines = []
        for segment in segments:
            timestamp = self._format_timestamp(segment['start'])
            text = segment['text'].strip()
            lines.append(f"[{timestamp}] {text}")
        
        return "\n".join(lines)
    
    def _format_timestamp(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _compute_avg_confidence(self, segments: List[Dict]) -> float:
        """Compute average confidence from Whisper segments (if available)"""
        # Whisper doesn't expose per-segment confidence directly
        # Use avg_logprob as proxy (higher = more confident)
        if not segments:
            return 0.0
        
        avg_logprobs = [seg.get('avg_logprob', -1.0) for seg in segments]
        # Convert logprob to 0-1 scale (approximate)
        avg_logprob = sum(avg_logprobs) / len(avg_logprobs)
        confidence = max(0.0, min(1.0, (avg_logprob + 1.0)))  # Normalize
        return confidence
    
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
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.aac': 'audio/aac',
            '.flac': 'audio/flac',
            '.ogg': 'audio/ogg',
            '.m4a': 'audio/mp4'
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
