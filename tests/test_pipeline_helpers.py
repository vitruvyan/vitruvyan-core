"""
Pipeline Integration Unit Tests
================================

Tests for auto-embed text extraction (Codex bus_adapter._build_embed_text)
and BG listener text extraction (_extract_text_from_payload).

Pure unit tests — no Redis, no HTTP.
"""

import pytest


# ============================================================================
# _build_embed_text tests (extracted as pure function for testing)
# ============================================================================

def _build_embed_text(entity_id: str, data: dict, max_len: int = 2000) -> str:
    """
    Mirror of CodexHuntersBusAdapter._build_embed_text.

    Extracted as standalone function for unit-testability without
    needing to instantiate the full adapter.
    """
    parts = []
    priority_keys = [
        "title", "normalized_text", "text", "description",
        "selftext", "content", "notes", "summary",
    ]
    seen = set()
    for key in priority_keys:
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            parts.append(val.strip())
            seen.add(key)

    for key, val in data.items():
        if key in seen:
            continue
        if isinstance(val, str) and len(val) > 10:
            parts.append(val.strip())

    joined = " ".join(parts)[:max_len]
    return joined if joined.strip() else entity_id


class TestBuildEmbedText:
    """Verify text extraction for auto-embedding."""

    def test_priority_key_title(self):
        data = {"title": "My Article", "random_field": "something else"}
        result = _build_embed_text("ent-1", data)
        assert result.startswith("My Article")

    def test_priority_key_normalized_text(self):
        data = {"normalized_text": "Full text content here", "id": "123"}
        result = _build_embed_text("ent-1", data)
        assert "Full text content here" in result

    def test_multiple_priority_keys(self):
        data = {"title": "Title", "description": "Description", "notes": "Extra"}
        result = _build_embed_text("ent-1", data)
        assert "Title" in result
        assert "Description" in result
        assert "Extra" in result

    def test_fallback_to_entity_id(self):
        """Empty data returns entity_id as fallback."""
        result = _build_embed_text("ent-42", {})
        assert result == "ent-42"

    def test_whitespace_only_values_ignored(self):
        data = {"title": "   ", "description": "  \n  "}
        result = _build_embed_text("ent-42", data)
        assert result == "ent-42"

    def test_max_len_truncation(self):
        data = {"text": "a" * 5000}
        result = _build_embed_text("ent-1", data, max_len=100)
        assert len(result) == 100

    def test_non_priority_string_fields_included(self):
        data = {"custom_field": "Custom content longer than 10 chars"}
        result = _build_embed_text("ent-1", data)
        assert "Custom content" in result

    def test_short_strings_excluded(self):
        """Strings <= 10 chars from non-priority fields are excluded."""
        data = {"short": "tiny"}
        result = _build_embed_text("ent-1", data)
        assert result == "ent-1"

    def test_non_string_values_ignored(self):
        data = {"title": "Valid", "count": 42, "active": True, "tags": ["a", "b"]}
        result = _build_embed_text("ent-1", data)
        assert result == "Valid"

    def test_reddit_shaped_payload(self):
        """Reddit evidence pack data shape."""
        data = {
            "title": "Reddit Post Title",
            "selftext": "This is the body text of the post.",
            "subreddit": "technology_discussion",  # len > 10
            "author": "user123",        # len < 10 → excluded
        }
        result = _build_embed_text("ent-reddit", data)
        assert "Reddit Post Title" in result
        assert "body text" in result

    def test_fred_shaped_payload(self):
        """FRED evidence pack data shape."""
        data = {
            "title": "Gross Domestic Product",
            "notes": "BEA Account Code: A191RC. Computed from quarterly data.",
            "frequency": "Quarterly",   # len < 10 → excluded
        }
        result = _build_embed_text("ent-fred", data)
        assert "Gross Domestic Product" in result
        assert "BEA Account Code" in result


# ============================================================================
# _extract_text_from_payload tests (BG listener)
# ============================================================================

def _extract_text_from_payload(payload: dict):
    """
    Mirror of BG streams_listener._extract_text_from_payload.

    Extracted for unit-testability.
    """
    if isinstance(payload.get("text"), str) and payload["text"].strip():
        return payload["text"]

    data = payload.get("data") or payload.get("normalized_data") or {}
    if isinstance(data, dict):
        for key in ("normalized_text", "title", "text", "description", "content"):
            val = data.get(key)
            if isinstance(val, str) and val.strip():
                return val

    entity_id = payload.get("entity_id")
    if entity_id:
        return f"Entity: {entity_id}"

    return None


class TestExtractTextFromPayload:
    """Verify BG listener text extraction from event payloads."""

    def test_direct_text_field(self):
        payload = {"text": "Direct text content", "entity_id": "ent-1"}
        assert _extract_text_from_payload(payload) == "Direct text content"

    def test_nested_data_normalized_text(self):
        payload = {
            "entity_id": "ent-1",
            "data": {"normalized_text": "Nested normalized text"},
        }
        assert _extract_text_from_payload(payload) == "Nested normalized text"

    def test_nested_data_title(self):
        payload = {
            "entity_id": "ent-1",
            "data": {"title": "Article Title"},
        }
        assert _extract_text_from_payload(payload) == "Article Title"

    def test_nested_normalized_data(self):
        """Uses 'normalized_data' key as alternative to 'data'."""
        payload = {
            "entity_id": "ent-1",
            "normalized_data": {"description": "A description field"},
        }
        assert _extract_text_from_payload(payload) == "A description field"

    def test_fallback_to_entity_id(self):
        payload = {"entity_id": "ent-42"}
        assert _extract_text_from_payload(payload) == "Entity: ent-42"

    def test_empty_payload_returns_none(self):
        assert _extract_text_from_payload({}) is None

    def test_whitespace_only_text_ignored(self):
        payload = {"text": "   ", "entity_id": "ent-1"}
        assert _extract_text_from_payload(payload) == "Entity: ent-1"

    def test_codex_bind_event_shape(self):
        """Simulates the actual codex.entity.bound event payload."""
        payload = {
            "entity_id": "ent-abc123",
            "postgres_stored": True,
            "qdrant_stored": True,
            "bound_at": "2026-02-25T12:00:00",
            "data": {
                "normalized_text": "Title: GDP Report\nUnits: Billions",
                "title": "GDP Report",
            },
        }
        result = _extract_text_from_payload(payload)
        assert result == "Title: GDP Report\nUnits: Billions"

    def test_codex_discovery_event_shape(self):
        """Simulates codex.entity.discovered payload."""
        payload = {
            "entity_id": "ent-xyz",
            "data": {
                "content": "Full article content from the source.",
            },
        }
        result = _extract_text_from_payload(payload)
        assert result == "Full article content from the source."
