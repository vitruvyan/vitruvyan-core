"""
🛡️ Orthodoxy Wardens — Schema Validator
=========================================
Sacred Order: TRUTH & INTEGRITY LAYER
Epistemic Role: Validation and integrity enforcement before ingestion

Ensures dataset integrity before ingestion into Archivarium (PostgreSQL) and Mnemosyne (Qdrant).
Implements professional boundaries for external data sources.

Author: Vitruvyan Core Team
Date: November 3, 2025
"""

import pandas as pd
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class SchemaValidator:
    """
    Validates external datasets before ingestion.
    Enforces epistemic standards for data quality and completeness.
    """
    
    # Required columns for financial datasets
    REQUIRED_FINANCIAL = {"entity_id", "date", "open", "close", "volume"}
    
    # Required columns for sentiment datasets
    REQUIRED_SENTIMENT = {"text", "sentiment"}
    
    # Optional columns that enhance data quality
    OPTIONAL_FINANCIAL = {"high", "low", "adj_close", "dividends", "stock_splits"}
    OPTIONAL_SENTIMENT = {"source", "domain", "date", "confidence"}
    
    @classmethod
    def validate_financial(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate financial dataset schema.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Dict with validation results and warnings
            
        Raises:
            ValueError: If critical columns are missing
        """
        logger.info(f"🛡️ [Orthodoxy Wardens] Validating financial dataset ({len(df)} rows)")
        
        # Normalize column names
        df.columns = [c.lower().strip() for c in df.columns]
        
        # Check required columns
        missing = cls.REQUIRED_FINANCIAL - set(df.columns)
        if missing:
            error_msg = f"Missing required columns: {missing}"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        # Check for null values
        null_counts = df[list(cls.REQUIRED_FINANCIAL)].isnull().sum()
        has_nulls = null_counts[null_counts > 0]
        
        # Check optional columns
        present_optional = cls.OPTIONAL_FINANCIAL & set(df.columns)
        missing_optional = cls.OPTIONAL_FINANCIAL - set(df.columns)
        
        # Validation results
        validation = {
            "status": "valid",
            "rows": len(df),
            "required_columns": list(cls.REQUIRED_FINANCIAL),
            "optional_present": list(present_optional),
            "optional_missing": list(missing_optional),
            "null_counts": has_nulls.to_dict() if not has_nulls.empty else {},
            "warnings": []
        }
        
        if not has_nulls.empty:
            warning = f"⚠️  NaN values detected: {has_nulls.to_dict()}"
            logger.warning(warning)
            validation["warnings"].append(warning)
        
        if missing_optional:
            info = f"💡 Optional columns not present: {missing_optional}"
            logger.info(info)
            validation["warnings"].append(info)
        
        logger.info(f"✅ Financial dataset validated: {len(df)} rows, {len(df.columns)} columns")
        return validation
    
    @classmethod
    def validate_sentiment(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate sentiment dataset schema.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Dict with validation results and warnings
            
        Raises:
            ValueError: If critical columns are missing
        """
        logger.info(f"🛡️ [Orthodoxy Wardens] Validating sentiment dataset ({len(df)} rows)")
        
        # Normalize column names
        df.columns = [c.lower().strip() for c in df.columns]
        
        # Check required columns
        missing = cls.REQUIRED_SENTIMENT - set(df.columns)
        if missing:
            error_msg = f"Missing required columns: {missing}"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        # Check sentiment values
        valid_sentiments = {"positive", "negative", "neutral"}
        if "sentiment" in df.columns:
            unique_sentiments = set(df["sentiment"].unique())
            invalid_sentiments = unique_sentiments - valid_sentiments
            if invalid_sentiments:
                warning = f"⚠️  Invalid sentiment values: {invalid_sentiments}"
                logger.warning(warning)
        
        # Check text length
        if "text" in df.columns:
            text_lengths = df["text"].str.len()
            too_short = (text_lengths < 10).sum()
            too_long = (text_lengths > 5000).sum()
        
        # Check optional columns
        present_optional = cls.OPTIONAL_SENTIMENT & set(df.columns)
        missing_optional = cls.OPTIONAL_SENTIMENT - set(df.columns)
        
        validation = {
            "status": "valid",
            "rows": len(df),
            "required_columns": list(cls.REQUIRED_SENTIMENT),
            "optional_present": list(present_optional),
            "optional_missing": list(missing_optional),
            "warnings": []
        }
        
        if "text" in df.columns:
            if too_short > 0:
                warning = f"⚠️  {too_short} texts shorter than 10 characters"
                logger.warning(warning)
                validation["warnings"].append(warning)
            if too_long > 0:
                warning = f"⚠️  {too_long} texts longer than 5000 characters"
                logger.warning(warning)
                validation["warnings"].append(warning)
        
        if missing_optional:
            info = f"💡 Optional columns not present: {missing_optional}"
            logger.info(info)
            validation["warnings"].append(info)
        
        logger.info(f"✅ Sentiment dataset validated: {len(df)} rows, {len(df.columns)} columns")
        return validation
    
    @classmethod
    def validate_generic(cls, df: pd.DataFrame, required_columns: set) -> Dict[str, Any]:
        """
        Validate generic dataset with custom required columns.
        
        Args:
            df: DataFrame to validate
            required_columns: Set of required column names
            
        Returns:
            Dict with validation results
            
        Raises:
            ValueError: If critical columns are missing
        """
        logger.info(f"🛡️ [Orthodoxy Wardens] Validating generic dataset ({len(df)} rows)")
        
        # Normalize column names
        df.columns = [c.lower().strip() for c in df.columns]
        
        # Check required columns
        missing = required_columns - set(df.columns)
        if missing:
            error_msg = f"Missing required columns: {missing}"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        validation = {
            "status": "valid",
            "rows": len(df),
            "columns": len(df.columns),
            "required_columns": list(required_columns),
            "warnings": []
        }
        
        logger.info(f"✅ Generic dataset validated: {len(df)} rows, {len(df.columns)} columns")
        return validation


class DataQualityChecker:
    """
    Advanced data quality checks beyond schema validation.
    Implements epistemic standards for data integrity.
    """
    
    @staticmethod
    def check_duplicates(df: pd.DataFrame, key_columns: List[str]) -> Dict[str, Any]:
        """Check for duplicate records based on key columns."""
        duplicates = df.duplicated(subset=key_columns, keep=False)
        duplicate_count = duplicates.sum()
        
        if duplicate_count > 0:
            logger.warning(f"⚠️  Found {duplicate_count} duplicate records")
            return {
                "has_duplicates": True,
                "count": int(duplicate_count),
                "percentage": float(duplicate_count / len(df) * 100)
            }
        
        return {"has_duplicates": False, "count": 0, "percentage": 0.0}
    
    @staticmethod
    def check_date_range(df: pd.DataFrame, date_column: str = "date") -> Dict[str, Any]:
        """Check date range and consistency."""
        if date_column not in df.columns:
            return {"error": f"Column '{date_column}' not found"}
        
        # Convert to datetime if not already
        if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
            df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        
        min_date = df[date_column].min()
        max_date = df[date_column].max()
        
        return {
            "min_date": str(min_date),
            "max_date": str(max_date),
            "span_days": (max_date - min_date).days if pd.notna(max_date) and pd.notna(min_date) else None
        }
    
    @staticmethod
    def check_ticker_validity(df: pd.DataFrame, ticker_column: str = "entity_id") -> Dict[str, Any]:
        """Check entity_id format and validity."""
        if ticker_column not in df.columns:
            return {"error": f"Column '{ticker_column}' not found"}
        
        unique_tickers = df[ticker_column].nunique()
        invalid_tickers = df[df[ticker_column].str.len() > 5][ticker_column].unique()
        
        return {
            "unique_tickers": int(unique_tickers),
            "invalid_count": len(invalid_tickers),
            "sample_invalid": list(invalid_tickers[:5]) if len(invalid_tickers) > 0 else []
        }


# Epistemic Note:
# The Orthodoxy Wardens ensure that all knowledge entering the system
# meets the sacred standards of truth, completeness, and coherence.
# They are the first line of defense against corrupted or incomplete data.
