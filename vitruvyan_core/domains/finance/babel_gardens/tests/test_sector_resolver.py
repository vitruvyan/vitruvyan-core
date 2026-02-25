"""Tests for sector resolution with mocked DB fetchers."""

from domains.finance.babel_gardens.sector_resolver import SectorResolver


def _mock_fetcher_tech(sql, params):
    _ = (sql, params)
    return [
        {
            "db_sector": "Technology",
            "gics_sector": "Information Technology",
            "pattern_weaver_concept": "Tech Innovation",
            "multilingual_aliases": {
                "en": ["technology", "tech", "software"],
                "it": ["tecnologia", "informatica"],
                "es": ["tecnologia", "informatica"],
            },
        }
    ]


def _mock_fetcher_empty(sql, params):
    _ = (sql, params)
    return []


def test_resolve_english():
    resolver = SectorResolver(db_fetcher=_mock_fetcher_tech)
    result = resolver.resolve_sector("technology stocks", "en")
    assert result is not None
    assert result["db_sector"] == "Technology"


def test_resolve_italian():
    resolver = SectorResolver(db_fetcher=_mock_fetcher_tech)
    result = resolver.resolve_sector("settore tecnologia", "it")
    assert result is not None
    assert result["gics_sector"] == "Information Technology"


def test_resolve_no_match():
    resolver = SectorResolver(db_fetcher=_mock_fetcher_empty)
    result = resolver.resolve_sector("xyz123", "en")
    assert result is None


def test_keyword_extraction():
    resolver = SectorResolver(db_fetcher=_mock_fetcher_empty)
    keywords = resolver._extract_sector_keywords("migliori biotech italiane")
    assert "biotech" in keywords
    assert "migliori" in keywords
    assert "italiane" in keywords
