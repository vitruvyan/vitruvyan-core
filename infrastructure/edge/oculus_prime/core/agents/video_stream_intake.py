"""
AEGIS INTAKE — Video & Streaming Intake Agent

Media Scope: MP4, OGG, AVI, MOV, WebRTC streams, RTSP feeds, satellite imagery
Constraints: Keyframe extraction + audio STT, governed by Sampling Policy

Compliance: ACCORDO-FONDATIVO-INTAKE-V1.1

Key Principles:
- Chunking via keyframes / time intervals
- Audio transcription (if present)
- Frame captioning (literal only)
- Sampling Policy enforcement (external, versioned)
- Always-on capable (for real-time feeds)
- NO relevance filtering
"""

import uuid
import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from infrastructure.edge.oculus_prime.core.guardrails import IntakeGuardrails

# Video processing libraries (conditional imports)
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


logger = logging.getLogger(__name__)


class VideoStreamIntakeAgent:
    """
    Pre-epistemic video/stream acquisition agent
    
    Responsibilities:
    - Extract keyframes at intervals (governed by Sampling Policy)
    - Transcribe audio track (if present)
    - Generate frame captions (literal only)
    - Create immutable Evidence Packs per chunk
    - Emit oculus_prime.evidence.created events (legacy alias: intake.evidence.created)
    
    DOES NOT:
    - Filter frames by relevance
    - Detect events or anomalies
    - Classify video content semantically
    - Call Codex directly
    
    Sampling Policy Integration:
    - Frame rate: defined externally (e.g., 1 frame/sec, 1 frame/5sec)
    - Keyframe-only vs uniform sampling
    - Stream windowing (e.g., last 60 seconds)
    - Policy referenced in Evidence Pack
    """
    
    SUPPORTED_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.ogg']
    AGENT_ID = "video-stream-intake-v1"
    AGENT_VERSION = "1.0.0"
    
    def __init__(self, event_emitter, postgres_agent=None, whisper_model="base"):
        """
        Args:
            event_emitter: IntakeEventEmitter instance
            postgres_agent: PostgresAgent for Evidence Pack persistence
            whisper_model: Whisper model for audio transcription
        """
        self.event_emitter = event_emitter
        self.postgres_agent = postgres_agent
        self.whisper_model_name = whisper_model
        self.whisper_model = None
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check availability of video processing libraries"""
        if not CV2_AVAILABLE:
            logger.warning("OpenCV not installed. Video processing unavailable.")
        if not PIL_AVAILABLE:
            logger.warning("PIL/Pillow not installed. Frame captioning unavailable.")
        if not WHISPER_AVAILABLE:
            logger.warning("Whisper not installed. Audio transcription unavailable.")
    
    def ingest_video(
        self,
        source_path: str,
        sampling_policy: Dict[str, Any],
        enable_audio: bool = True,
        correlation_id: Optional[str] = None
    ) -> List[str]:
        """
        Ingest video file and create Evidence Packs
        
        Args:
            source_path: Path to video file
            sampling_policy: Dict with 'frame_interval_sec', 'keyframes_only', 'chunk_duration_sec'
            enable_audio: Extract and transcribe audio track
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
        
        # Extract sampling policy parameters
        frame_interval_sec = sampling_policy.get('frame_interval_sec', 1.0)
        keyframes_only = sampling_policy.get('keyframes_only', False)
        chunk_duration_sec = sampling_policy.get('chunk_duration_sec', 60)
        sampling_policy_ref = sampling_policy.get('policy_ref', 'SAMPPOL-VIDEO-DEFAULT-V1')
        
        # Compute source hash
        source_hash = self._compute_file_hash(source_path)
        byte_size = source_path.stat().st_size
        mime_type = self._get_mime_type(source_path)
        
        # Open video
        if not CV2_AVAILABLE:
            raise ValueError("OpenCV not available. Cannot process video.")
        
        cap = cv2.VideoCapture(str(source_path))
        if not cap.isOpened():
            raise ValueError(f"Failed to open video: {source_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_sec = total_frames / fps if fps > 0 else 0
        
        # Extract frames according to sampling policy
        frame_data = self._extract_frames(cap, fps, frame_interval_sec, keyframes_only)
        cap.release()
        
        # Extract audio (if enabled)
        audio_transcript = ""
        if enable_audio:
            audio_transcript = self._extract_audio_transcript(source_path)
        
        # Chunk frames by duration
        chunk_groups = self._chunk_frames_by_duration(frame_data, fps, chunk_duration_sec)
        
        # Create Evidence Packs
        evidence_ids = []
        for chunk_idx, frame_group in enumerate(chunk_groups):
            evidence_id = self._generate_evidence_id()
            chunk_id = f"CHK-{chunk_idx}"
            
            # Build normalized text (frame descriptions + audio)
            normalized_text = self._format_video_content(frame_group, audio_transcript, chunk_idx, len(chunk_groups))
            
            # Extract temporal metadata
            start_time = frame_group[0]['timestamp'] if frame_group else 0.0
            end_time = frame_group[-1]['timestamp'] if frame_group else 0.0
            
            # Build Evidence Pack
            evidence_pack = {
                "evidence_id": evidence_id,
                "chunk_id": chunk_id,
                "schema_version": "1.0.0",
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "source_ref": {
                    "source_type": "video",
                    "source_uri": str(source_path.absolute()),
                    "source_hash": source_hash,
                    "mime_type": mime_type,
                    "byte_size": byte_size
                },
                "normalized_text": normalized_text,
                "technical_metadata": {
                    "extraction_method": "opencv+whisper" if enable_audio else "opencv",
                    "extraction_version": self.AGENT_VERSION,
                    "language_detected": "unknown",
                    "confidence_score": 1.0,
                    "chunk_position": {
                        "start_offset": chunk_idx * chunk_duration_sec,
                        "end_offset": (chunk_idx + 1) * chunk_duration_sec,
                        "total_chunks": len(chunk_groups)
                    },
                    "temporal_metadata": {
                        "timestamp_start": (datetime.now(timezone.utc) + timedelta(seconds=start_time)).isoformat(),
                        "timestamp_end": (datetime.now(timezone.utc) + timedelta(seconds=end_time)).isoformat(),
                        "duration_sec": end_time - start_time
                    },
                    "video_metadata": {
                        "fps": fps,
                        "total_frames": total_frames,
                        "sampled_frames": len(frame_group),
                        "sampling_policy": sampling_policy
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
                IntakeGuardrails.validate_no_semantics(normalized_text, "video")
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
                source_type="video",
                source_uri=str(source_path.absolute()),
                evidence_pack_ref=evidence_pack_ref,
                source_hash=source_hash,
                intake_agent_id=self.AGENT_ID,
                intake_agent_version=self.AGENT_VERSION,
                byte_size=byte_size,
                language_detected="unknown",
                sampling_policy_ref=sampling_policy_ref,
                correlation_id=correlation_id
            )
            
            evidence_ids.append(evidence_id)
        
        return evidence_ids
    
    def ingest_stream(
        self,
        stream_url: str,
        sampling_policy: Dict[str, Any],
        duration_sec: int = 60,
        correlation_id: Optional[str] = None
    ) -> List[str]:
        """
        Ingest real-time stream (RTSP, WebRTC, etc.)
        
        Args:
            stream_url: Stream URL (rtsp://, http://, etc.)
            sampling_policy: Dict with frame sampling rules
            duration_sec: How long to capture stream
            correlation_id: Distributed tracing ID
        
        Returns:
            List of evidence_ids created
        
        Note: Stream capture is always-on capable but governed by Sampling Policy
        """
        # Placeholder: Real implementation would use cv2.VideoCapture(stream_url)
        # and buffer frames according to sampling_policy
        raise NotImplementedError("Stream ingestion coming in v1.1")
    
    def _extract_frames(self, cap: Any, fps: float, interval_sec: float, keyframes_only: bool) -> List[Dict]:
        """
        Extract frames according to sampling policy
        
        Returns list of {frame_number, timestamp, frame_data}
        """
        frames = []
        frame_interval = int(fps * interval_sec)
        frame_number = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Sample frame if matches interval
            if frame_number % frame_interval == 0:
                timestamp = frame_number / fps
                frames.append({
                    'frame_number': frame_number,
                    'timestamp': timestamp,
                    'frame_data': frame  # OpenCV frame (numpy array)
                })
            
            frame_number += 1
        
        return frames
    
    def _chunk_frames_by_duration(self, frames: List[Dict], fps: float, chunk_duration_sec: int) -> List[List[Dict]]:
        """Chunk frames into groups by duration"""
        chunks = []
        current_chunk = []
        chunk_start_time = 0.0
        
        for frame in frames:
            if frame['timestamp'] - chunk_start_time >= chunk_duration_sec and current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                chunk_start_time = frame['timestamp']
            
            current_chunk.append(frame)
        
        if current_chunk:
            chunks.append(current_chunk)
        if not chunks:
            # Preserve append-only evidence behavior for low-information captures.
            chunks.append([])
        
        return chunks
    
    def _format_video_content(self, frames: List[Dict], audio_transcript: str, chunk_idx: int, total_chunks: int) -> str:
        """
        Format video content as normalized text
        
        Includes frame descriptions + audio transcript
        """
        lines = [f"[VIDEO CHUNK {chunk_idx+1}/{total_chunks}]"]
        
        # Frame descriptions
        lines.append("\n[FRAMES]")
        for frame in frames:
            timestamp = self._format_timestamp(frame['timestamp'])
            # Placeholder: In production, generate literal frame caption
            lines.append(f"[{timestamp}] Frame {frame['frame_number']}")
        
        # Audio transcript (if available)
        if audio_transcript:
            lines.append("\n[AUDIO]")
            lines.append(audio_transcript)
        
        return "\n".join(lines)
    
    def _extract_audio_transcript(self, source_path: Path) -> str:
        """Extract and transcribe audio track (literal only)"""
        if not WHISPER_AVAILABLE:
            return ""
        
        try:
            # Placeholder: Extract audio track first (via ffmpeg)
            # Then transcribe with Whisper
            # For now, return empty string
            return ""
        except Exception as e:
            logger.warning(f"Audio transcription failed: {e}")
            return ""
    
    def _format_timestamp(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
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
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska',
            '.webm': 'video/webm',
            '.ogg': 'video/ogg'
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
