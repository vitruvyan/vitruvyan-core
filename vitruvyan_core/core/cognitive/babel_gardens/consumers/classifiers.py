"""
Babel Gardens - Topic Classifier Consumer
==========================================

Pure topic classification logic using configurable taxonomy.
NO hardcoded categories - uses TopicConfig loaded from YAML.

Author: Vitruvyan Core Team
Version: 2.0.0 (February 2026)
"""

import re
from typing import Dict, Any, List, Set
from datetime import datetime
import logging

from .base import BaseConsumer, ProcessResult
from ..domain import (
    BabelConfig,
    ProcessingStatus,
    TopicMatch,
    TopicClassificationResult,
)

logger = logging.getLogger(__name__)


class TopicClassifierConsumer(BaseConsumer):
    """
    Topic classification consumer.
    
    Classifies text into topics based on keyword matching.
    Uses configurable taxonomy from TopicConfig (domain-agnostic).
    """
    
    def process(self, data: Dict[str, Any]) -> ProcessResult:
        """
        Process topic classification request.
        
        Expected input:
            text: str - Text to classify
            min_score: float - Minimum score threshold (optional, default: 0.1)
            max_topics: int - Maximum topics to return (optional, default: 5)
            
        Returns:
            ProcessResult with topics in data
        """
        start_time = datetime.utcnow()
        
        # Validate input
        errors = self.validate_input(data, ["text"])
        if errors:
            self._record_error()
            return ProcessResult(success=False, data={}, errors=errors)
        
        text = data["text"]
        min_score = data.get("min_score", 0.1)
        max_topics = data.get("max_topics", 5)
        
        if not text.strip():
            self._record_error()
            return ProcessResult(
                success=False,
                data={},
                errors=["Empty text provided"],
            )
        
        try:
            # Tokenize text
            tokens = self._tokenize(text.lower())
            
            # Match against taxonomy
            matches = self._match_topics(tokens)
            
            # Filter by score and limit
            filtered = [m for m in matches if m.score >= min_score]
            filtered.sort(key=lambda m: m.score, reverse=True)
            filtered = filtered[:max_topics]
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._record_success()
            
            return ProcessResult(
                success=True,
                data={
                    "topics": [m.to_dict() for m in filtered],
                    "topic_count": len(filtered),
                    "status": ProcessingStatus.COMPLETED.value,
                },
                processing_time_ms=processing_time,
            )
            
        except Exception as e:
            self._record_error()
            return ProcessResult(
                success=False,
                data={},
                errors=[f"Classification error: {str(e)}"],
            )
    
    def _tokenize(self, text: str) -> Set[str]:
        """Tokenize text into unique words."""
        # Remove punctuation and split
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        return set(words)
    
    def _match_topics(self, tokens: Set[str]) -> List[TopicMatch]:
        """Match tokens against taxonomy categories."""
        matches = []
        
        for cat_id, category in self.config.topics.categories.items():
            keywords_matched = []
            
            for keyword in category.keywords:
                keyword_lower = keyword.lower()
                # Check for exact match or partial match
                if keyword_lower in tokens:
                    keywords_matched.append(keyword)
                else:
                    # Check if keyword is substring of any token
                    for token in tokens:
                        if keyword_lower in token or token in keyword_lower:
                            keywords_matched.append(keyword)
                            break
            
            if keywords_matched:
                # Score based on percentage of keywords matched
                total_keywords = len(category.keywords)
                if total_keywords > 0:
                    score = len(keywords_matched) / total_keywords
                else:
                    score = 1.0  # No keywords means always match
                
                matches.append(TopicMatch(
                    topic_id=cat_id,
                    topic_name=category.name,
                    score=min(score, 1.0),  # Cap at 1.0
                    keywords_matched=keywords_matched,
                ))
        
        return matches


class LanguageDetectorConsumer(BaseConsumer):
    """
    Language detection consumer.
    
    Detects language of input text using simple heuristics.
    Actual detection should be done via ML models in adapters.
    """
    
    # Common words per language for basic detection
    LANGUAGE_MARKERS = {
        "en": {"the", "is", "are", "and", "or", "but", "with", "this", "that"},
        "it": {"il", "la", "di", "che", "è", "sono", "per", "con", "una"},
        "es": {"el", "la", "de", "que", "es", "son", "para", "con", "una"},
        "fr": {"le", "la", "de", "que", "est", "sont", "pour", "avec", "une"},
        "de": {"der", "die", "das", "ist", "sind", "und", "für", "mit", "ein"},
        "pt": {"o", "a", "de", "que", "é", "são", "para", "com", "uma"},
    }
    
    def process(self, data: Dict[str, Any]) -> ProcessResult:
        """
        Process language detection request.
        
        Expected input:
            text: str - Text to analyze
            
        Returns:
            ProcessResult with language detection in data
        """
        start_time = datetime.utcnow()
        
        # Validate input
        errors = self.validate_input(data, ["text"])
        if errors:
            self._record_error()
            return ProcessResult(success=False, data={}, errors=errors)
        
        text = data["text"]
        
        if not text.strip():
            return ProcessResult(
                success=True,
                data={
                    "language": self.config.language.default_language,
                    "confidence": 0.0,
                    "method": "default",
                },
            )
        
        try:
            tokens = set(text.lower().split())
            
            # Count matches per language
            scores = {}
            for lang, markers in self.LANGUAGE_MARKERS.items():
                matches = len(tokens & markers)
                if matches > 0:
                    scores[lang] = matches / len(markers)
            
            # Get best match
            if scores:
                best_lang = max(scores, key=scores.get)
                confidence = min(scores[best_lang] * 2, 1.0)  # Scale up
            else:
                best_lang = self.config.language.default_language
                confidence = 0.0
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._record_success()
            
            return ProcessResult(
                success=True,
                data={
                    "language": best_lang,
                    "confidence": confidence,
                    "method": "heuristic",
                    "alternatives": [
                        {"language": lang, "score": score}
                        for lang, score in sorted(
                            scores.items(), 
                            key=lambda x: x[1], 
                            reverse=True
                        )[:3]
                    ],
                },
                processing_time_ms=processing_time,
            )
            
        except Exception as e:
            self._record_error()
            return ProcessResult(
                success=False,
                data={},
                errors=[f"Detection error: {str(e)}"],
            )
