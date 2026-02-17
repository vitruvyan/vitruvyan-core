from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class EdgeSourceType(str, Enum):
    document = "document"
    image = "image"
    audio = "audio"
    video = "video"
    cad = "cad"
    landscape = "landscape"
    geo = "geo"


class EdgeEnvelopeIn(BaseModel):
    source_type: EdgeSourceType
    source_uri: str = Field(
        ...,
        description="Local path on edge runtime or remote URI understood by an edge adapter",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    created_utc: Optional[str] = None

    @model_validator(mode="after")
    def _ensure_created_utc(self) -> "EdgeEnvelopeIn":
        if not self.created_utc:
            self.created_utc = datetime.now(timezone.utc).isoformat()
        return self


class EdgeEnvelopeStored(BaseModel):
    envelope_id: str
    source_type: EdgeSourceType
    source_uri: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    created_utc: str

    @classmethod
    def from_input(cls, payload: EdgeEnvelopeIn) -> "EdgeEnvelopeStored":
        return cls(
            envelope_id=f"EEG-{uuid4()}",
            source_type=payload.source_type,
            source_uri=payload.source_uri,
            metadata=payload.metadata,
            correlation_id=payload.correlation_id,
            created_utc=payload.created_utc or datetime.now(timezone.utc).isoformat(),
        )

