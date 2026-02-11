"""
Finance Signals Plugin — FinBERT-based Signal Extraction

Wraps FinBERT model to extract finance-specific signals:
- sentiment_valence: Overall market sentiment polarity [-1, 1]
- market_fear_index: Market stress/uncertainty indicator [0, 1]
- volatility_perception: Perceived volatility [0, 1]

This is LIVELLO 2 (Service) code:
- Instantiates HuggingFace models
- Translates model outputs → SignalExtractionResult
- No business logic (domain layer in LIVELLO 1)

Sacred Law: "Explainability is sacred — every signal must trace its origin"
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass
import logging

# LIVELLO 1 imports (domain primitives)
from core.cognitive.babel_gardens.domain import (
    SignalSchema,
    SignalExtractionResult,
    SignalConfig,
)

logger = logging.getLogger(__name__)


@dataclass
class ModelOutput:
    """Structured output from FinBERT model."""
    label: str              # "positive", "negative", "neutral"
    scores: Dict[str, float]  # {"positive": 0.7, "negative": 0.1, "neutral": 0.2}
    model_version: str
    inference_time_ms: float


class FinanceSignalsPlugin:
    """
    Finance vertical signal extractor using FinBERT.
    
    Architecture:
    - Model: ProsusAI/finbert (HuggingFace)
    - Output: 3-class sentiment (positive, negative, neutral)
    - Signals: sentiment_valence, market_fear_index, volatility_perception
    
    State: Model is loaded on first extraction (lazy loading)
    """
    
    def __init__(self, model_name: str = "ProsusAI/finbert", device: str = "cpu"):
        """
        Initialize plugin with model configuration.
        
        Args:
            model_name: HuggingFace model identifier
            device: "cpu" or "cuda"
        """
        self.model_name = model_name
        self.device = device
        self._model = None
        self._tokenizer = None
        self._initialized = False
        
        logger.info(f"FinanceSignalsPlugin created (model: {model_name}, device: {device})")
    
    def _ensure_model_loaded(self):
        """Lazy load model on first use."""
        if self._initialized:
            return
        
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            import torch
            
            logger.info(f"Loading FinBERT model: {self.model_name}")
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self._model.to(self.device)
            self._model.eval()
            
            self._initialized = True
            logger.info("FinBERT model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load FinBERT model: {e}")
            raise RuntimeError(f"Model loading failed: {e}") from e
    
    def _run_inference(self, text: str) -> ModelOutput:
        """
        Run FinBERT inference on text.
        
        Args:
            text: Input text (news headline, earnings report snippet, etc.)
        
        Returns:
            ModelOutput with label and scores
        """
        self._ensure_model_loaded()
        
        import torch
        import time
        
        start_time = time.perf_counter()
        
        # Tokenize
        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Inference (no gradient)
        with torch.no_grad():
            outputs = self._model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1).squeeze()
        
        # Map to labels (FinBERT uses: negative=0, neutral=1, positive=2)
        label_map = {0: "negative", 1: "neutral", 2: "positive"}
        scores_dict = {
            label_map[i]: float(probs[i])
            for i in range(len(probs))
        }
        
        predicted_label = label_map[torch.argmax(probs).item()]
        
        inference_time = (time.perf_counter() - start_time) * 1000  # ms
        
        return ModelOutput(
            label=predicted_label,
            scores=scores_dict,
            model_version="1.0.2",  # FinBERT version
            inference_time_ms=inference_time,
        )
    
    def extract_sentiment_valence(self, text: str, schema: SignalSchema) -> SignalExtractionResult:
        """
        Extract sentiment_valence signal [-1, 1].
        
        Mapping:
        - sentiment_valence = P(positive) - P(negative)
        - Range: [-1, 1] where -1 = fully negative, +1 = fully positive
        
        Args:
            text: Input text
            schema: SignalSchema defining expected output
        
        Returns:
            SignalExtractionResult with explainability trace
        """
        if schema.name != "sentiment_valence":
            raise ValueError(f"Schema name mismatch: expected 'sentiment_valence', got '{schema.name}'")
        
        # Run inference
        model_output = self._run_inference(text)
        
        # Compute signal value
        raw_value = model_output.scores["positive"] - model_output.scores["negative"]
        
        # Normalize to schema range
        normalized_value = schema.normalize_value(raw_value)
        
        # Confidence = max probability (how certain the model is)
        confidence = max(model_output.scores.values())
        
        # Explainability trace (Orthodoxy Wardens requirement)
        extraction_trace = {
            "method": f"model:{self.model_name}",
            "model_version": model_output.model_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "inference_time_ms": model_output.inference_time_ms,
            "raw_model_output": model_output.scores,
            "predicted_label": model_output.label,
            "computation": f"positive - negative = {model_output.scores['positive']:.3f} - {model_output.scores['negative']:.3f} = {raw_value:.3f}",
        }
        
        return SignalExtractionResult(
            signal_name="sentiment_valence",
            value=normalized_value,
            confidence=confidence,
            extraction_trace=extraction_trace,
            metadata={
                "text_length": len(text),
                "device": self.device,
            },
        )
    
    def extract_market_fear_index(self, text: str, schema: SignalSchema) -> SignalExtractionResult:
        """
        Extract market_fear_index signal [0, 1].
        
        Measures market stress/uncertainty:
        - fear_index = P(negative) + 0.5 * P(neutral)
        - Higher values indicate market stress
        
        Args:
            text: Input text
            schema: SignalSchema defining expected output
        
        Returns:
            SignalExtractionResult with explainability trace
        """
        if schema.name != "market_fear_index":
            raise ValueError(f"Schema name mismatch: expected 'market_fear_index', got '{schema.name}'")
        
        # Run inference
        model_output = self._run_inference(text)
        
        # Compute fear index (negative + partial neutral)
        raw_value = (
            model_output.scores["negative"] +
            0.5 * model_output.scores["neutral"]
        )
        
        # Normalize to schema range
        normalized_value = schema.normalize_value(raw_value)
        
        # Confidence = 1 - entropy (higher certainty = less uncertainty)
        confidence = max(model_output.scores.values())
        
        # Explainability trace
        extraction_trace = {
            "method": f"model:{self.model_name}",
            "model_version": model_output.model_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "inference_time_ms": model_output.inference_time_ms,
            "raw_model_output": model_output.scores,
            "computation": f"negative + 0.5*neutral = {model_output.scores['negative']:.3f} + 0.5*{model_output.scores['neutral']:.3f} = {raw_value:.3f}",
        }
        
        return SignalExtractionResult(
            signal_name="market_fear_index",
            value=normalized_value,
            confidence=confidence,
            extraction_trace=extraction_trace,
            metadata={
                "text_length": len(text),
                "device": self.device,
            },
        )
    
    def extract_signals(self, text: str, config: SignalConfig) -> List[SignalExtractionResult]:
        """
        Extract all configured signals from text.
        
        Batch extraction for efficiency (runs inference once, produces multiple signals).
        
        Args:
            text: Input text
            config: SignalConfig with signals to extract
        
        Returns:
            List of SignalExtractionResult (one per signal in config)
        """
        results = []
        
        for schema in config.signals:
            if schema.name == "sentiment_valence":
                result = self.extract_sentiment_valence(text, schema)
            elif schema.name == "market_fear_index":
                result = self.extract_market_fear_index(text, schema)
            else:
                logger.warning(f"Signal '{schema.name}' not implemented in FinanceSignalsPlugin, skipping")
                continue
            
            results.append(result)
        
        return results
    
    def is_healthy(self) -> bool:
        """Check if plugin is ready for inference."""
        try:
            self._ensure_model_loaded()
            return self._initialized
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# Convenience function for direct usage
def extract_finance_signals(text: str, config_path: str, device: str = "cpu") -> List[SignalExtractionResult]:
    """
    Extract finance signals from text using config YAML.
    
    Example:
    ```python
    from core.cognitive.babel_gardens.domain import load_config_from_yaml
    from api_babel_gardens.plugins.finance_signals import extract_finance_signals
    
    config = load_config_from_yaml("examples/signals_finance.yaml")
    results = extract_finance_signals(
        text="Fed signals rate hike amid inflation concerns",
        config=config
    )
    
    for result in results:
        print(f"{result.signal_name}: {result.value:.3f} (confidence: {result.confidence:.3f})")
    ```
    
    Args:
        text: Input text
        config_path: Path to signals YAML
        device: "cpu" or "cuda"
    
    Returns:
        List of SignalExtractionResult
    """
    from core.cognitive.babel_gardens.domain import load_config_from_yaml
    
    config = load_config_from_yaml(config_path)
    plugin = FinanceSignalsPlugin(device=device)
    
    return plugin.extract_signals(text, config)
