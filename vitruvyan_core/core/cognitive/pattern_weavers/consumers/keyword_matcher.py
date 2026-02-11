"""
Pattern Weavers - Keyword Matcher Consumer
==========================================

Pure keyword matching logic using taxonomy configuration.
NO I/O - uses taxonomy loaded from configuration.

The KeywordMatcher:
- Matches query text against taxonomy keywords
- Provides fast fallback when embedding service unavailable
- Uses configurable taxonomy (not hardcoded categories)

Author: Vitruvyan Core Team
Created: February 2026
"""

from typing import Dict, Any, List, Set
from datetime import datetime
import re
import logging

from .base import BaseConsumer, ProcessResult
from ..domain import (
    PatternConfig,
    PatternMatch,
    MatchType,
    TaxonomyCategory,
)

logger = logging.getLogger(__name__)


class KeywordMatcherConsumer(BaseConsumer):
    """
    Keyword matching consumer for Pattern Weavers.
    
    Responsibilities:
    - Match query text against taxonomy keywords
    - Score matches based on keyword frequency
    - Provide fallback when semantic search unavailable
    
    Uses taxonomy from configuration (domain-agnostic).
    """
    
    def process(self, data: Dict[str, Any]) -> ProcessResult:
        """
        Process a keyword matching request.
        
        Expected input:
            query_text: str - Query to match
            categories: List[str] - Category types to search (optional)
            min_matches: int - Minimum keyword matches required (default: 1)
            
        Returns:
            ProcessResult with matches in data["matches"]
        """
        start_time = datetime.utcnow()
        
        # Validate input
        errors = self.validate_input(data, ["query_text"])
        if errors:
            self._record_error()
            return ProcessResult(success=False, data={}, errors=errors)
        
        query_text = data["query_text"].lower()
        categories_filter = data.get("categories")  # Optional filter
        min_matches = data.get("min_matches", 1)
        
        # Tokenize query
        query_tokens = self._tokenize(query_text)
        
        matches = []
        
        # Search through taxonomy categories
        for category_type in self.config.taxonomy.categories:
            # Skip if filter specified and not in filter
            if categories_filter and category_type not in categories_filter:
                continue
            
            category_matches = self._match_category(
                query_tokens,
                category_type,
                self.config.taxonomy.get_category(category_type),
                min_matches,
            )
            matches.extend(category_matches)
        
        # Sort by score descending
        matches.sort(key=lambda m: m.score, reverse=True)
        
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        self._record_success()
        
        return ProcessResult(
            success=True,
            data={
                "matches": matches,
                "match_count": len(matches),
                "categories_searched": list(self.config.taxonomy.categories.keys()),
            },
            processing_time_ms=processing_time,
        )
    
    def _tokenize(self, text: str) -> Set[str]:
        """
        Tokenize text into words.
        
        - Lowercase
        - Remove punctuation
        - Split on whitespace
        """
        # Remove punctuation except hyphens
        cleaned = re.sub(r'[^\w\s-]', ' ', text)
        # Split and lowercase
        tokens = set(cleaned.lower().split())
        return tokens
    
    def _match_category(
        self,
        query_tokens: Set[str],
        category_type: str,
        categories: List[TaxonomyCategory],
        min_matches: int,
    ) -> List[PatternMatch]:
        """
        Match query tokens against category keywords.
        
        Args:
            query_tokens: Set of query tokens
            category_type: Type of category (e.g., "concepts")
            categories: List of TaxonomyCategory to search
            min_matches: Minimum keyword matches required
            
        Returns:
            List of PatternMatch for matching categories
        """
        matches = []
        
        for category in categories:
            keyword_set = set(kw.lower() for kw in category.keywords)
            
            # Count matching keywords
            matched_keywords = query_tokens & keyword_set
            match_count = len(matched_keywords)
            
            if match_count >= min_matches:
                # Score based on proportion of keywords matched
                total_keywords = len(keyword_set) or 1
                score = match_count / total_keywords
                
                match = PatternMatch(
                    category=category_type,
                    name=category.name,
                    score=min(score, 1.0),  # Cap at 1.0
                    match_type=MatchType.KEYWORD,
                    metadata={
                        "matched_keywords": list(matched_keywords),
                        "total_keywords": total_keywords,
                        **category.metadata,
                    },
                )
                matches.append(match)
        
        return matches
