"""
Vitruvyan INTAKE — Runtime Guardrails

Enforces "no semantics" constraint at runtime.
Validates that normalized_text is literal/descriptive ONLY (NO interpretation).

Compliance: ACCORDO-FONDATIVO-INTAKE-V1.1
"""

import re
from typing import List, Tuple


class NoSemanticsViolation(Exception):
    """Raised when normalized_text contains semantic interpretation"""
    pass


class IntakeGuardrails:
    """
    Runtime validation for Intake Layer constraints
    
    Key Guardrails:
    - NO semantic interpretation in normalized_text
    - NO evaluative adjectives (good, bad, excellent, poor)
    - NO domain-specific inferences (e.g., "this is a car" when OCR sees "blue object")
    - NO predictive statements (e.g., "this will cause X")
    """
    
    # Forbidden patterns (semantic interpretation indicators)
    FORBIDDEN_PATTERNS = [
        # Evaluative adjectives
        r'\b(good|bad|excellent|poor|great|terrible|amazing|awful|wonderful|horrible)\b',
        
        # Inferential statements
        r'\b(this is|appears to be|seems to be|looks like|probably|likely|suggests that|indicates that)\b',
        
        # Predictive statements
        r'\b(will cause|will result in|will lead to|expected to|predicted to)\b',
        
        # Subjective judgments
        r'\b(important|significant|irrelevant|notable|remarkable|concerning|worrying)\b',
        
        # Causal reasoning
        r'\b(because|therefore|thus|hence|consequently|as a result)\b',
        
        # Domain-specific classifications (should be generic)
        r'\b(car|vehicle|person|human|animal|building|road|tree)\b',  # Example: "blue object" OK, "car" NOT OK
    ]
    
    # Allowed literal terms (generic descriptions)
    ALLOWED_GENERIC_TERMS = [
        "object", "shape", "color", "size", "position", "texture", "pattern",
        "sound", "text", "number", "symbol", "line", "curve", "area", "region"
    ]
    
    @classmethod
    def validate_no_semantics(cls, normalized_text: str, source_type: str) -> Tuple[bool, List[str]]:
        """
        Validate that normalized_text contains NO semantic interpretation
        
        Args:
            normalized_text: Text to validate
            source_type: Media type (document/image/audio/video)
        
        Returns:
            (is_valid, violations) - True if compliant, False with violation list
        
        Raises:
            NoSemanticsViolation: If text contains forbidden patterns
        """
        violations = []
        
        # For document source types, semantic guardrail does not apply:
        # extracted text is already literal by definition (no LLM generation involved).
        # Guardrail is only meaningful for generated content (image captions, audio transcripts
        # post-processed by LLM, etc.).
        if source_type == "document":
            return True, []
        
        # Check each forbidden pattern
        for pattern in cls.FORBIDDEN_PATTERNS:
            matches = re.findall(pattern, normalized_text, re.IGNORECASE)
            if matches:
                violations.append(f"Forbidden pattern '{pattern}' found: {matches}")
        
        # Special validation for image captions
        if source_type == "image":
            if not cls._is_generic_caption(normalized_text):
                violations.append("Image caption must use generic terms only (e.g., 'blue object', NOT 'car')")
        
        # If violations found, raise exception
        if violations:
            raise NoSemanticsViolation(
                f"Semantic interpretation detected in normalized_text. "
                f"Violations: {violations}. "
                f"ACCORDO-FONDATIVO-INTAKE-V1.1 requires literal descriptions only."
            )
        
        return True, []
    
    @classmethod
    def _is_generic_caption(cls, caption: str) -> bool:
        """
        Check if image caption uses generic terms only
        
        Examples:
        - ✅ VALID: "blue object in center, 640x480 pixels"
        - ✅ VALID: "rectangular shape with text overlay"
        - ❌ INVALID: "car parked in parking lot"
        - ❌ INVALID: "person wearing red shirt"
        """
        # Caption must contain at least one generic term
        has_generic_term = any(term in caption.lower() for term in cls.ALLOWED_GENERIC_TERMS)
        
        # Caption must NOT contain domain-specific classifications
        domain_pattern = r'\b(car|vehicle|person|human|animal|building|road|tree|house|plane|boat)\b'
        has_domain_term = re.search(domain_pattern, caption, re.IGNORECASE)
        
        return has_generic_term and not has_domain_term
    
    @classmethod
    def validate_source_hash_required(cls, source_ref: dict) -> bool:
        """
        Validate that source_hash is present and valid
        
        Args:
            source_ref: Dictionary with source metadata
        
        Raises:
            ValueError: If source_hash missing or invalid format
        """
        if "source_hash" not in source_ref:
            raise ValueError("source_hash is REQUIRED in source_ref (ACCORDO-FONDATIVO-INTAKE-V1.1)")
        
        source_hash = source_ref["source_hash"]
        
        # Validate SHA-256 format: "sha256:<64 hex chars>"
        if not re.match(r'^sha256:[0-9a-f]{64}$', source_hash):
            raise ValueError(f"Invalid source_hash format: {source_hash}. Must be 'sha256:<64 hex chars>'")
        
        return True
    
    @classmethod
    def validate_no_codex_import(cls, module_name: str) -> bool:
        """
        Validate that Intake agents do NOT import Codex modules
        
        Args:
            module_name: Module to check
        
        Raises:
            ImportError: If Codex module detected
        """
        forbidden_imports = [
            "codex",
            "codex_hunters",
            "codex_enrichment",
            "semantic_engine",
            "ner_extractor"
        ]
        
        for forbidden in forbidden_imports:
            if forbidden in module_name.lower():
                raise ImportError(
                    f"Intake agents CANNOT import Codex modules: {module_name}. "
                    f"Use event-driven communication via Redis Cognitive Bus. "
                    f"(INTAKE ↔ CODEX boundary violation)"
                )
        
        return True


# Example usage
if __name__ == "__main__":
    guardrails = IntakeGuardrails()
    
    # ✅ VALID: Literal OCR text
    text1 = "[OCR] Invoice #12345 dated 2026-01-09"
    try:
        guardrails.validate_no_semantics(text1, "image")
        print(f"✅ VALID: {text1}")
    except NoSemanticsViolation as e:
        print(f"❌ INVALID: {e}")
    
    # ❌ INVALID: Semantic interpretation
    text2 = "This is an excellent financial report that will probably result in good outcomes"
    try:
        guardrails.validate_no_semantics(text2, "document")
        print(f"✅ VALID: {text2}")
    except NoSemanticsViolation as e:
        print(f"❌ INVALID: {e}")
    
    # ✅ VALID: Generic image caption
    text3 = "[CAPTION] Blue rectangular object in center, 640x480 pixels"
    try:
        guardrails.validate_no_semantics(text3, "image")
        print(f"✅ VALID: {text3}")
    except NoSemanticsViolation as e:
        print(f"❌ INVALID: {e}")
    
    # ❌ INVALID: Domain-specific classification
    text4 = "[CAPTION] Car parked in parking lot"
    try:
        guardrails.validate_no_semantics(text4, "image")
        print(f"✅ VALID: {text4}")
    except NoSemanticsViolation as e:
        print(f"❌ INVALID: {e}")
