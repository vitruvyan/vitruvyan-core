"""
Finance Sector Resolver - GICS Multilingual Resolution
======================================================

Resolve sector queries from multilingual text using the `sector_mappings`
PostgreSQL table with JSONB `multilingual_aliases`.

This module is domain logic only. Database access is injected via `db_fetcher`.
"""

import re
from typing import Any, Callable, Dict, List, Optional


class SectorResolver:
    """Resolve sector queries in multilingual text."""

    def __init__(self, db_fetcher: Callable):
        self._fetch = db_fetcher

    def resolve_sector(
        self,
        query_text: str,
        detected_language: str = "auto",
    ) -> Optional[Dict[str, Any]]:
        """Resolve a sector from query text, returning best-match metadata."""
        keywords = self._extract_sector_keywords(query_text)

        for keyword in keywords:
            sector = self._query_sector_by_alias(keyword, detected_language)
            if sector:
                return sector

        for keyword in keywords:
            sector = self._query_sector_by_alias(keyword.lower(), detected_language)
            if sector:
                return sector

        return None

    def _extract_sector_keywords(self, text: str) -> List[str]:
        """
        Extract sector candidate terms from text.

        Handles CJK tokenization via bigrams and Latin words with stopword
        filtering.
        """
        stopwords = {
            "il",
            "la",
            "i",
            "le",
            "di",
            "da",
            "a",
            "in",
            "per",
            "con",
            "su",
            "the",
            "and",
            "or",
            "of",
            "to",
            "for",
            "on",
            "at",
            "is",
            "are",
            "el",
            "los",
            "las",
            "de",
            "en",
            "y",
            "o",
            "del",
            "les",
            "et",
            "ou",
            "dans",
            "pour",
            "sur",
        }

        cjk_sequences = re.findall(
            r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]+",
            text,
        )
        non_cjk_words = re.findall(r"[a-zA-ZÀ-ÿ]+", text.lower())

        keywords: List[str] = []

        for seq in cjk_sequences:
            if len(seq) <= 2:
                keywords.append(seq)
                continue
            for idx in range(len(seq) - 1):
                keywords.append(seq[idx : idx + 2])

        for word in non_cjk_words:
            if word not in stopwords and len(word) >= 4:
                keywords.append(word)

        return keywords

    def _query_sector_by_alias(
        self,
        alias: str,
        language: str = "auto",
    ) -> Optional[Dict[str, Any]]:
        """Query `sector_mappings` and map DB row to domain response."""
        try:
            if language == "auto":
                rows = self._fetch(
                    """
                    SELECT db_sector, gics_sector, pattern_weaver_concept, multilingual_aliases
                    FROM sector_mappings
                    WHERE EXISTS (
                        SELECT 1 FROM jsonb_each(multilingual_aliases) AS lang
                        WHERE lang.value @> to_jsonb(ARRAY[%s]::text[])
                    )
                    LIMIT 1
                    """,
                    (alias,),
                )
            else:
                rows = self._fetch(
                    """
                    SELECT db_sector, gics_sector, pattern_weaver_concept, multilingual_aliases
                    FROM sector_mappings
                    WHERE multilingual_aliases -> %s @> to_jsonb(ARRAY[%s]::text[])
                    LIMIT 1
                    """,
                    (language, alias),
                )

            if not rows:
                return None

            row = rows[0]
            aliases_dict = row.get("multilingual_aliases", {})
            matched_language = self._resolve_matched_language(aliases_dict, alias)

            return {
                "db_sector": row.get("db_sector"),
                "gics_sector": row.get("gics_sector"),
                "pattern_weaver_concept": row.get("pattern_weaver_concept"),
                "matched_alias": alias,
                "matched_language": matched_language or language,
                "confidence": 0.95 if matched_language else 0.75,
            }
        except Exception:
            return None

    @staticmethod
    def _resolve_matched_language(aliases_dict: Any, alias: str) -> Optional[str]:
        if not isinstance(aliases_dict, dict):
            return None

        for lang, alias_list in aliases_dict.items():
            if not isinstance(alias_list, list):
                continue
            if alias in alias_list:
                return lang
        return None

    def get_all_sectors_multilingual(self, language: str = "en") -> List[Dict[str, Any]]:
        """Fetch all sectors and flatten multilingual aliases."""
        _ = language  # reserved for future filtering by preferred language
        try:
            rows = self._fetch(
                """
                SELECT db_sector, gics_sector, multilingual_aliases
                FROM sector_mappings
                WHERE multilingual_aliases IS NOT NULL
                ORDER BY db_sector
                """,
                (),
            )
        except Exception:
            return []

        sectors = []
        for row in rows:
            aliases_dict = row.get("multilingual_aliases", {})
            aliases = []
            if isinstance(aliases_dict, dict):
                for values in aliases_dict.values():
                    if isinstance(values, list):
                        aliases.extend(values)

            sectors.append(
                {
                    "db_sector": row.get("db_sector"),
                    "gics_sector": row.get("gics_sector"),
                    "aliases": aliases,
                    "languages_count": len(aliases_dict) if isinstance(aliases_dict, dict) else 0,
                }
            )

        return sectors
