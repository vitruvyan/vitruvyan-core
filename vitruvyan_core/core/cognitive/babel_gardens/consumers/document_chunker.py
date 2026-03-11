# core/cognitive/babel_gardens/consumers/document_chunker.py
"""
Document Chunker — LIVELLO 1 (Pure Domain)
==========================================
Sacred Order: Perception (Babel Gardens)
Responsibility: Split raw text into overlapping chunks suitable for embedding.

Zero I/O. Pure Python. No external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class DocumentChunk:
    """A single chunk of a document with positional metadata."""
    text: str
    index: int
    char_start: int
    char_end: int
    source_filename: str = ""


@dataclass(frozen=True)
class ChunkerConfig:
    """Chunking parameters."""
    chunk_size: int = 1500       # characters per chunk (≈375 tokens)
    chunk_overlap: int = 200     # overlap between adjacent chunks
    min_chunk_size: int = 100    # discard trailing chunks smaller than this


def chunk_text(
    text: str,
    filename: str = "",
    config: ChunkerConfig | None = None,
) -> List[DocumentChunk]:
    """
    Split *text* into overlapping chunks.

    Strategy: character-level sliding window with paragraph-boundary snapping.
    If a paragraph boundary exists within the last 20% of the chunk window,
    we split there instead of mid-sentence.

    Returns:
        List of DocumentChunk (may be empty if text is too short).
    """
    cfg = config or ChunkerConfig()
    if len(text) < cfg.min_chunk_size:
        return []

    chunks: List[DocumentChunk] = []
    start = 0
    idx = 0

    while start < len(text):
        end = min(start + cfg.chunk_size, len(text))

        # Try to snap to paragraph boundary (\n\n) in the last 20% of the window
        if end < len(text):
            snap_zone_start = start + int(cfg.chunk_size * 0.8)
            snap_pos = text.rfind("\n\n", snap_zone_start, end)
            if snap_pos > snap_zone_start:
                end = snap_pos

        chunk_text_str = text[start:end].strip()
        if len(chunk_text_str) >= cfg.min_chunk_size:
            chunks.append(DocumentChunk(
                text=chunk_text_str,
                index=idx,
                char_start=start,
                char_end=end,
                source_filename=filename,
            ))
            idx += 1

        # Advance with overlap
        start = end - cfg.chunk_overlap if end < len(text) else len(text)

    return chunks
