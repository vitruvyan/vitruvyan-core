"""
Financial Context Detector
==========================

Detects whether a query is finance-related for vertical routing and scoring.
"""

from typing import Any, Dict, Set


class FinancialContextDetector:
    """Keyword-based finance context detector."""

    FINANCIAL_TERMS: Dict[str, Set[str]] = {
        "en": {
            "market",
            "stock",
            "bond",
            "equity",
            "fund",
            "portfolio",
            "dividend",
            "earnings",
            "revenue",
            "profit",
            "loss",
            "trading",
            "investment",
            "volatility",
            "inflation",
            "yield",
            "forex",
            "crypto",
            "sector",
            "analyst",
        },
        "it": {
            "mercato",
            "borsa",
            "azioni",
            "titolo",
            "obbligazione",
            "fondo",
            "portafoglio",
            "dividendo",
            "utili",
            "ricavi",
            "trading",
            "investimento",
            "volatilità",
            "inflazione",
            "rendimento",
            "settore",
            "analista",
        },
        "es": {
            "mercado",
            "bolsa",
            "acciones",
            "bono",
            "fondo",
            "cartera",
            "dividendo",
            "ganancias",
            "inversión",
            "volatilidad",
            "inflación",
            "rendimiento",
            "sector",
        },
    }

    def __init__(self):
        self._all_terms: Set[str] = set()
        for terms in self.FINANCIAL_TERMS.values():
            self._all_terms.update(term.lower() for term in terms)

    def is_financial(self, text: str, language: str = "auto") -> Dict[str, Any]:
        """Return finance classification with confidence and trace."""
        if not text:
            return {
                "is_financial": False,
                "confidence": 0.0,
                "matched_terms": [],
                "language": language,
            }

        text_lower = text.lower()
        selected_terms = self._terms_for_language(language)
        matched = [term for term in selected_terms if term in text_lower]

        words_count = max(len(text_lower.split()), 1)
        match_ratio = len(matched) / words_count
        is_financial = len(matched) >= 1
        confidence = min(1.0, match_ratio * 10.0) if matched else 0.0

        return {
            "is_financial": is_financial,
            "confidence": round(confidence, 3),
            "matched_terms": matched[:10],
            "language": language,
        }

    def _terms_for_language(self, language: str) -> Set[str]:
        lang = (language or "auto").lower()
        if lang != "auto" and lang in self.FINANCIAL_TERMS:
            return {term.lower() for term in self.FINANCIAL_TERMS[lang]}
        return self._all_terms
