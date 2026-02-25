"""Tests for financial context detection."""

import pytest

from domains.finance.babel_gardens.financial_context import FinancialContextDetector


@pytest.fixture
def detector():
    return FinancialContextDetector()


def test_financial_text_english(detector):
    result = detector.is_financial("The stock market rallied on earnings reports", "en")
    assert result["is_financial"] is True
    assert result["confidence"] > 0.0


def test_financial_text_italian(detector):
    result = detector.is_financial("Il mercato azionario e in rialzo", "it")
    assert result["is_financial"] is True


def test_non_financial_text(detector):
    result = detector.is_financial("The weather is nice today", "en")
    assert result["is_financial"] is False


def test_auto_language_detection(detector):
    result = detector.is_financial("La borsa di Milano ha chiuso in positivo", "auto")
    assert result["is_financial"] is True


def test_empty_text(detector):
    result = detector.is_financial("", "en")
    assert result["is_financial"] is False
