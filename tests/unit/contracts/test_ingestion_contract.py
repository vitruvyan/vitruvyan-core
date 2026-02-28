"""
Unit tests for IngestionContract: SourceDescriptor, IngestionQuality,
NormalizedChunk, IngestionPayload, IIngestionPlugin, helpers, channels.

Run: pytest tests/unit/contracts/test_ingestion_contract.py -v
"""

from __future__ import annotations

from datetime import datetime, timezone
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
    content: bytes = b"hello world",
    source_type: SourceType = SourceType.FILE,
) -> SourceDescriptor:
    content_hash = compute_content_hash(content)
    source_id = build_source_id(uri, content_hash)
    return SourceDescriptor(
        source_id=source_id,
        source_type=source_type,
        uri=uri,
        content_hash=content_hash,
        size_bytes=len(content),
    )


def _make_quality(
    quality_score: float = 0.8,
    gate_passed: bool = True,
    gate_threshold: float = 0.3,
) -> IngestionQuality:
    return IngestionQuality(
        quality_score=quality_score,
        gate_passed=gate_passed,
        gate_threshold=gate_threshold,
        completeness=0.9,
        confidence=0.8,
    )


def _make_chunk(source_id: str = "src001", chunk_index: int = 0) -> NormalizedChunk:
    return NormalizedChunk(
        chunk_id=build_chunk_id(source_id, chunk_index),
        chunk_index=chunk_index,
        text="Sample text chunk",
        token_count=4,
    )


def _make_payload() -> IngestionPayload:
    source = _make_source()
    quality = _make_quality()
    chunks = [_make_chunk(source.source_id, i) for i in range(3)]
    return IngestionPayload(
        source=source,
        quality=quality,
        chunks=chunks,
        total_chunks=len(chunks),
        total_tokens=sum(c.token_count for c in chunks),
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
            assert ch.startswith("perception.ingestion.")

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
        h = compute_content_hash(b"test data")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_compute_content_hash_deterministic(self) -> None:
        assert compute_content_hash(b"abc") == compute_content_hash(b"abc")

    def test_compute_content_hash_different_content(self) -> None:
        assert compute_content_hash(b"abc") != compute_content_hash(b"xyz")

    def test_build_source_id_deterministic(self) -> None:
        sid = build_source_id("file:///a.txt", "abc123")
        assert sid == build_source_id("file:///a.txt", "abc123")

    def test_build_source_id_length(self) -> None:
        sid = build_source_id("file:///a.txt", "abc123")
        assert len(sid) == 32

    def test_build_source_id_different_inputs(self) -> None:
        assert build_source_id("uri_a", "hash1") != build_source_id("uri_b", "hash2")

    def test_build_chunk_id_deterministic(self) -> None:
        cid = build_chunk_id("src001", 0)
        assert cid == build_chunk_id("src001", 0)

    def test_build_chunk_id_different_index(self) -> None:
        assert build_chunk_id("src001", 0) != build_chunk_id("src001", 1)

    def test_build_chunk_id_length(self) -> None:
        assert len(build_chunk_id("src001", 5)) == 32


# ─────────────────────────────────────────────────────────────
# SourceType
# ─────────────────────────────────────────────────────────────

class TestSourceType:
    def test_all_types_serializable(self) -> None:
        for st in SourceType:
            assert isinstance(st.value, str)

    def test_values(self) -> None:
        assert SourceType.FILE.value == "file"
        assert SourceType.USER_INPUT.value == "user_input"


# ─────────────────────────────────────────────────────────────
# SourceDescriptor
# ─────────────────────────────────────────────────────────────

class TestSourceDescriptor:
    def test_basic_creation(self) -> None:
        src = _make_source()
        assert src.source_id
        assert src.source_type == SourceType.FILE
        assert src.size_bytes == len(b"hello world")
        assert src.encoding == "utf-8"
        assert src.language == "auto"

    def test_contract_id(self) -> None:
        assert SourceDescriptor.contract_id() == "ingestion.source@1.0.0"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            SourceDescriptor(
                source_id="x",
                source_type=SourceType.API,
                unknown_field="oops",  # type: ignore[call-arg]
            )

    def test_empty_source_id_invariant(self) -> None:
        src = SourceDescriptor(source_id="", source_type=SourceType.FILE)
        violations = src.validate_invariants()
        assert any("source_id" in v for v in violations)

    def test_invalid_size_bytes_rejected(self) -> None:
        content_hash = compute_content_hash(b"x")
        source_id = build_source_id("uri", content_hash)
        with pytest.raises(ValidationError):
            SourceDescriptor(
                source_id=source_id,
                source_type=SourceType.FILE,
                size_bytes=-1,
            )

    def test_provenance_chain(self) -> None:
        parent = _make_source(uri="file:///parent.txt")
        child = _make_source(uri="file:///child.txt")
        child_with_prov = SourceDescriptor(
            **{
                **child.model_dump(),
                "parent_source_id": parent.source_id,
                "provenance_chain": [parent.source_id, child.source_id],
            }
        )
        assert child_with_prov.parent_source_id == parent.source_id
        assert parent.source_id in child_with_prov.provenance_chain

    def test_registered_in_registry(self) -> None:
        assert ContractRegistry.is_registered("ingestion.source")


# ─────────────────────────────────────────────────────────────
# IngestionQuality
# ─────────────────────────────────────────────────────────────

class TestIngestionQuality:
    def test_basic_creation(self) -> None:
        q = _make_quality()
        assert q.gate_passed is True
        assert q.quality_score == 0.8

    def test_contract_id(self) -> None:
        assert IngestionQuality.contract_id() == "ingestion.quality@1.0.0"

    def test_gate_invariant_passed_below_threshold(self) -> None:
        q = IngestionQuality(quality_score=0.2, gate_passed=True, gate_threshold=0.3)
        violations = q.validate_invariants()
        assert any("gate_passed=True" in v for v in violations)

    def test_gate_invariant_ok_above_threshold(self) -> None:
        q = IngestionQuality(quality_score=0.5, gate_passed=True, gate_threshold=0.3)
        assert q.validate_invariants() == []

    def test_gate_invariant_duplicate_conflict(self) -> None:
        q = IngestionQuality(
            quality_score=0.8,
            gate_passed=True,
            gate_threshold=0.3,
            duplicate_of="src_original",
        )
        violations = q.validate_invariants()
        assert any("duplicate" in v for v in violations)

    def test_not_passed_no_violation(self) -> None:
        q = IngestionQuality(quality_score=0.1, gate_passed=False, gate_threshold=0.3)
        assert q.validate_invariants() == []

    def test_enforce_strict_raises_on_violation(self) -> None:
        q = IngestionQuality(quality_score=0.1, gate_passed=True, gate_threshold=0.3)
        with pytest.raises(ValueError):
            q.enforce(strict=True)

    def test_out_of_range_score_rejected(self) -> None:
        with pytest.raises(ValidationError):
            IngestionQuality(quality_score=1.5)

    def test_registered_in_registry(self) -> None:
        assert ContractRegistry.is_registered("ingestion.quality")


# ─────────────────────────────────────────────────────────────
# NormalizedChunk
# ─────────────────────────────────────────────────────────────

class TestNormalizedChunk:
    def test_basic_creation(self) -> None:
        chunk = _make_chunk()
        assert chunk.chunk_index == 0
        assert chunk.text == "Sample text chunk"
        assert chunk.token_count == 4

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            NormalizedChunk(
                chunk_id="c001",
                text="hi",
                illegal="oops",  # type: ignore[call-arg]
            )

    def test_chunk_id_deterministic(self) -> None:
        chunk_id_a = build_chunk_id("src001", 0)
        chunk_id_b = build_chunk_id("src001", 0)
        assert chunk_id_a == chunk_id_b

    def test_metadata_dict(self) -> None:
        chunk = NormalizedChunk(
            chunk_id="c001",
            text="text",
            metadata={"page": 1, "heading": "Intro"},
        )
        assert chunk.metadata["page"] == 1


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

    def test_enforce_valid_payload(self) -> None:
        payload = _make_payload()
        result = payload.enforce(strict=True)
        assert result is payload

    def test_invariant_empty_chunks(self) -> None:
        source = _make_source()
        quality = _make_quality()
        payload = IngestionPayload(
            source=source,
            quality=quality,
            chunks=[],
            total_chunks=0,
        )
        violations = payload.validate_invariants()
        assert any("at least 1" in v for v in violations)

    def test_invariant_total_chunks_mismatch(self) -> None:
        source = _make_source()
        quality = _make_quality()
        chunk = _make_chunk(source.source_id)
        payload = IngestionPayload(
            source=source,
            quality=quality,
            chunks=[chunk],
            total_chunks=99,  # wrong
        )
        violations = payload.validate_invariants()
        assert any("total_chunks" in v for v in violations)

    def test_invariant_empty_source_id(self) -> None:
        source = SourceDescriptor(source_id="", source_type=SourceType.FILE)
        quality = _make_quality()
        chunk = _make_chunk("", 0)
        payload = IngestionPayload(
            source=source,
            quality=quality,
            chunks=[chunk],
            total_chunks=1,
        )
        violations = payload.validate_invariants()
        assert any("source_id" in v for v in violations)

    def test_invariant_gate_not_passed(self) -> None:
        source = _make_source()
        quality = _make_quality(quality_score=0.1, gate_passed=False)
        chunk = _make_chunk(source.source_id)
        payload = IngestionPayload(
            source=source,
            quality=quality,
            chunks=[chunk],
            total_chunks=1,
        )
        violations = payload.validate_invariants()
        assert any("gate not passed" in v for v in violations)

    def test_to_dict_roundtrip(self) -> None:
        payload = _make_payload()
        d = payload.to_dict()
        # Check required top-level keys
        assert "ingestion_id" in d
        assert "source" in d
        assert "quality" in d
        assert "chunks" in d

    def test_to_dict_with_meta(self) -> None:
        payload = _make_payload()
        d = payload.to_dict(include_meta=True)
        assert "__contract_meta__" in d
        assert d["__contract_meta__"]["contract_name"] == "ingestion.payload"

    def test_processing_pipeline_append(self) -> None:
        payload = _make_payload()
        steps = ["codex_hunters.discover", "babel_gardens.comprehend"]
        p2 = payload.model_copy(update={"processing_pipeline": steps})
        assert len(p2.processing_pipeline) == 2

    def test_extracted_metadata(self) -> None:
        payload = _make_payload()
        p2 = payload.model_copy(
            update={"extracted_metadata": {"title": "Test Doc", "author": "Alice"}}
        )
        assert p2.extracted_metadata["title"] == "Test Doc"

    def test_registered_in_registry(self) -> None:
        assert ContractRegistry.is_registered("ingestion.payload")

    def test_ingestion_id_auto_generated(self) -> None:
        p1 = _make_payload()
        p2 = _make_payload()
        # Auto-generated UUIDs should be unique
        assert p1.ingestion_id != p2.ingestion_id


# ─────────────────────────────────────────────────────────────
# IIngestionPlugin
# ─────────────────────────────────────────────────────────────

class TestIIngestionPlugin:
    def _make_plugin(self, threshold: float = 0.5) -> IIngestionPlugin:
        class _MockPlugin(IIngestionPlugin):
            def get_domain_name(self) -> str:
                return "mock"

            def get_accepted_source_types(self) -> List[SourceType]:
                return [SourceType.FILE, SourceType.API]

            def extract_domain_metadata(
                self,
                raw_text: str,
                source: SourceDescriptor,
            ) -> Dict[str, Any]:
                return {"length": len(raw_text)}

            def get_quality_threshold(self) -> float:
                return threshold

        return _MockPlugin()

    def test_plugin_contract_id(self) -> None:
        assert IIngestionPlugin.plugin_contract_id() == "ingestion_plugin@1.0.0"

    def test_abstract_methods_must_be_implemented(self) -> None:
        class _Incomplete(IIngestionPlugin):
            pass

        with pytest.raises(TypeError):
            _Incomplete()  # type: ignore[abstract]

    def test_default_validate_source_returns_empty(self) -> None:
        plugin = self._make_plugin()
        source = _make_source()
        assert plugin.validate_source(source) == []

    def test_default_normalize_text_passthrough(self) -> None:
        plugin = self._make_plugin()
        text = "hello world"
        assert plugin.normalize_text(text) == text

    def test_extract_domain_metadata(self) -> None:
        plugin = self._make_plugin()
        source = _make_source()
        meta = plugin.extract_domain_metadata("a test document", source)
        assert meta["length"] == len("a test document")

    def test_get_quality_threshold(self) -> None:
        plugin = self._make_plugin(threshold=0.6)
        assert plugin.get_quality_threshold() == 0.6

    def test_get_accepted_source_types(self) -> None:
        plugin = self._make_plugin()
        types = plugin.get_accepted_source_types()
        assert SourceType.FILE in types
        assert SourceType.API in types
