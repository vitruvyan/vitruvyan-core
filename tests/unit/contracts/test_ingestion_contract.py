"""
Unit tests for IngestionContract: SourceDescriptor, IngestionQuality,
NormalizedChunk, IngestionPayload, IIngestionPlugin, helpers, channels.

Run: pytest tests/unit/contracts/test_ingestion_contract.py -v
"""

from __future__ import annotations

from typing import Any, ClassVar, Dict, List

import pytest
from pydantic import ValidationError

from contracts.base import ContractRegistry
from contracts.ingestion import (
    CHANNEL_INGESTION_ACQUIRED,
    CHANNEL_INGESTION_DUPLICATE,
    CHANNEL_INGESTION_NORMALIZED,
    CHANNEL_INGESTION_REJECTED,
    IngestionPayload,
    IngestionQuality,
    IIngestionPlugin,
    NormalizedChunk,
    SourceDescriptor,
    SourceType,
    build_chunk_id,
    build_source_id,
    compute_content_hash,
)


# ─────────────────────────────────────────────────────────────
# Shared builders
# ─────────────────────────────────────────────────────────────

def _make_source(
    uri: str = "file:///tmp/test.txt",
    source_type: SourceType = SourceType.FILE,
) -> SourceDescriptor:
    source_id = build_source_id(source_type, uri)
    return SourceDescriptor(
        source_id=source_id,
        source_type=source_type,
        uri=uri,
    )


def _make_chunk(source_id: str = "src001", content: str = "Sample text chunk") -> NormalizedChunk:
    content_hash = compute_content_hash(content)
    chunk_id = build_chunk_id(source_id, content_hash, 0)
    return NormalizedChunk(
        chunk_id=chunk_id,
        source_id=source_id,
        content=content,
        content_hash=content_hash,
    )


def _make_payload() -> IngestionPayload:
    source = _make_source()
    chunks = [
        _make_chunk(source.source_id, f"chunk content {i}")
        for i in range(3)
    ]
    return IngestionPayload(
        source=source,
        chunks=chunks,
        total_chunks=len(chunks),
    )


# ─────────────────────────────────────────────────────────────
# Channel constants
# ─────────────────────────────────────────────────────────────

class TestChannelConstants:
    def test_channel_names_use_dot_notation(self) -> None:
        for ch in [
            CHANNEL_INGESTION_ACQUIRED,
            CHANNEL_INGESTION_NORMALIZED,
            CHANNEL_INGESTION_REJECTED,
            CHANNEL_INGESTION_DUPLICATE,
        ]:
            assert "ingestion" in ch
            assert "." in ch

    def test_channels_unique(self) -> None:
        channels = [
            CHANNEL_INGESTION_ACQUIRED,
            CHANNEL_INGESTION_NORMALIZED,
            CHANNEL_INGESTION_REJECTED,
            CHANNEL_INGESTION_DUPLICATE,
        ]
        assert len(set(channels)) == len(channels)


# ─────────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────────

class TestHelpers:
    def test_compute_content_hash_returns_hex(self) -> None:
        h = compute_content_hash("test data")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_compute_content_hash_deterministic(self) -> None:
        assert compute_content_hash("abc") == compute_content_hash("abc")

    def test_compute_content_hash_different_content(self) -> None:
        assert compute_content_hash("abc") != compute_content_hash("xyz")

    def test_build_source_id_deterministic(self) -> None:
        sid = build_source_id(SourceType.FILE, "file:///a.txt")
        assert sid == build_source_id(SourceType.FILE, "file:///a.txt")

    def test_build_source_id_different_inputs(self) -> None:
        a = build_source_id(SourceType.FILE, "uri_a")
        b = build_source_id(SourceType.API, "uri_b")
        assert a != b

    def test_build_source_id_format(self) -> None:
        sid = build_source_id(SourceType.WEB, "https://example.com")
        assert sid.startswith("web:")

    def test_build_chunk_id_deterministic(self) -> None:
        cid = build_chunk_id("src001", "hash1", 0)
        assert cid == build_chunk_id("src001", "hash1", 0)

    def test_build_chunk_id_different_position(self) -> None:
        assert build_chunk_id("src001", "h", 0) != build_chunk_id("src001", "h", 1)

    def test_build_chunk_id_length(self) -> None:
        assert len(build_chunk_id("src001", "hash", 5)) == 32


# ─────────────────────────────────────────────────────────────
# SourceType
# ─────────────────────────────────────────────────────────────

class TestSourceType:
    def test_all_types_serializable(self) -> None:
        for st in SourceType:
            assert isinstance(st.value, str)

    def test_values(self) -> None:
        assert SourceType.FILE.value == "file"
        assert SourceType.WEB.value == "web"
        assert SourceType.API.value == "api"

    def test_all_expected_members(self) -> None:
        names = {s.name for s in SourceType}
        assert "FILE" in names
        assert "WEB" in names
        assert "API" in names
        assert "STREAM" in names
        assert "DATABASE" in names
        assert "MANUAL" in names
        assert "SYNTHETIC" in names


# ─────────────────────────────────────────────────────────────
# SourceDescriptor
# ─────────────────────────────────────────────────────────────

class TestSourceDescriptor:
    def test_basic_creation(self) -> None:
        src = _make_source()
        assert src.source_id
        assert src.source_type == SourceType.FILE
        assert src.uri == "file:///tmp/test.txt"

    def test_contract_id(self) -> None:
        assert SourceDescriptor.contract_id() == "ingestion.source_descriptor@1.0.0"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            SourceDescriptor(
                source_id="x",
                source_type=SourceType.API,
                uri="http://test",
                unknown_field="oops",
            )

    def test_metadata_dict(self) -> None:
        src = SourceDescriptor(
            source_id="s1",
            source_type=SourceType.FILE,
            uri="file:///x.txt",
            metadata={"page_count": 5},
        )
        assert src.metadata["page_count"] == 5

    def test_registered_in_registry(self) -> None:
        assert ContractRegistry.is_registered("ingestion.source_descriptor")


# ─────────────────────────────────────────────────────────────
# IngestionQuality (Enum)
# ─────────────────────────────────────────────────────────────

class TestIngestionQuality:
    def test_enum_values(self) -> None:
        assert IngestionQuality.HIGH.value == "high"
        assert IngestionQuality.MEDIUM.value == "medium"
        assert IngestionQuality.LOW.value == "low"
        assert IngestionQuality.UNKNOWN.value == "unknown"

    def test_all_members(self) -> None:
        names = {q.name for q in IngestionQuality}
        assert names == {"HIGH", "MEDIUM", "LOW", "UNKNOWN"}

    def test_str_enum(self) -> None:
        assert str(IngestionQuality.HIGH) == "IngestionQuality.HIGH"


# ─────────────────────────────────────────────────────────────
# NormalizedChunk
# ─────────────────────────────────────────────────────────────

class TestNormalizedChunk:
    def test_basic_creation(self) -> None:
        chunk = _make_chunk()
        assert chunk.content == "Sample text chunk"
        assert chunk.chunk_id
        assert chunk.source_id == "src001"

    def test_contract_id(self) -> None:
        assert NormalizedChunk.contract_id() == "ingestion.normalized_chunk@1.0.0"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            NormalizedChunk(
                chunk_id="c001",
                source_id="s001",
                content="hi",
                content_hash="abc",
                illegal="oops",
            )

    def test_chunk_id_deterministic(self) -> None:
        chunk_id_a = build_chunk_id("src001", "h", 0)
        chunk_id_b = build_chunk_id("src001", "h", 0)
        assert chunk_id_a == chunk_id_b

    def test_default_quality_unknown(self) -> None:
        chunk = _make_chunk()
        assert chunk.quality == IngestionQuality.UNKNOWN

    def test_metadata_dict(self) -> None:
        chunk = NormalizedChunk(
            chunk_id="c001",
            source_id="s001",
            content="text",
            content_hash="hash123",
            metadata={"page": 1, "heading": "Intro"},
        )
        assert chunk.metadata["page"] == 1

    def test_tags(self) -> None:
        chunk = NormalizedChunk(
            chunk_id="c001",
            source_id="s001",
            content="text",
            content_hash="hash123",
            tags=["important", "verified"],
        )
        assert "important" in chunk.tags

    def test_optional_fields_default(self) -> None:
        chunk = _make_chunk()
        assert chunk.language is None
        assert chunk.position is None
        assert chunk.metadata == {}
        assert chunk.tags == []

    def test_registered_in_registry(self) -> None:
        assert ContractRegistry.is_registered("ingestion.normalized_chunk")


# ─────────────────────────────────────────────────────────────
# IngestionPayload
# ─────────────────────────────────────────────────────────────

class TestIngestionPayload:
    def test_basic_creation(self) -> None:
        payload = _make_payload()
        assert payload.ingestion_id
        assert len(payload.chunks) == 3
        assert payload.total_chunks == 3

    def test_contract_id(self) -> None:
        assert IngestionPayload.contract_id() == "ingestion.payload@1.0.0"

    def test_to_dict_roundtrip(self) -> None:
        payload = _make_payload()
        d = payload.to_dict()
        assert "ingestion_id" in d
        assert "source" in d
        assert "chunks" in d

    def test_to_dict_with_meta(self) -> None:
        payload = _make_payload()
        d = payload.to_dict(include_meta=True)
        assert "__contract_meta__" in d
        assert d["__contract_meta__"]["contract_name"] == "ingestion.payload"

    def test_ingestion_id_auto_generated(self) -> None:
        p1 = _make_payload()
        p2 = _make_payload()
        assert p1.ingestion_id != p2.ingestion_id

    def test_metadata_default_empty(self) -> None:
        payload = _make_payload()
        assert payload.metadata == {}

    def test_registered_in_registry(self) -> None:
        assert ContractRegistry.is_registered("ingestion.payload")


# ─────────────────────────────────────────────────────────────
# IIngestionPlugin
# ─────────────────────────────────────────────────────────────

class TestIIngestionPlugin:
    def test_plugin_contract_id(self) -> None:
        assert IIngestionPlugin.plugin_contract_id() == "ingestion_plugin@1.0.0"

    def test_abstract_methods_must_be_implemented(self) -> None:
        class _Incomplete(IIngestionPlugin):
            pass

        with pytest.raises(TypeError):
            _Incomplete()

    def test_concrete_plugin(self) -> None:
        class _MockPlugin(IIngestionPlugin):
            def ingest(self, source, raw):
                return []

            def can_handle(self, source_type):
                return source_type == SourceType.FILE

        plugin = _MockPlugin()
        assert plugin.can_handle(SourceType.FILE) is True
        assert plugin.can_handle(SourceType.API) is False
        assert plugin.ingest(_make_source(), "raw") == []
