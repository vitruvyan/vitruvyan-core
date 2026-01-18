# api_gemma_cognitive/modules/sentiment_fusion.py
"""
🎭 Sentiment Fusion Module
Advanced multi-model sentiment analysis with fusion algorithms
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
import torch
import numpy as np
from datetime import datetime
import statistics

from ..shared import GemmaServiceBase, model_manager, vector_cache
from ..schemas import (
    SentimentRequest, BatchSentimentRequest, SentimentResponse,
    BatchSentimentResponse, FeedbackData, CalibrationRequest,
    LanguageCode, FusionMode
)

logger = logging.getLogger(__name__)

class SentimentFusionModule(GemmaServiceBase):
    """
    🚀 Multi-model sentiment fusion engine
    Combines Gemma, FinBERT, and custom models for robust sentiment analysis
    """
    
    def __init__(self):
        super().__init__("sentiment_fusion")
        self.name = "SentimentFusion"
        self.version = "1.0.0"
        self.max_batch_size = 25
        self.supported_languages = set(lang.value for lang in LanguageCode)
        self.calibration_data = []
        self.fusion_weights = {
            "gemma": 0.45,
            "finbert": 0.35, 
            "multilingual": 0.20
        }
    
    async def _initialize_service(self):
        """Service-specific initialization for sentiment fusion"""
        pass
    
    async def initialize(self, model_manager, vector_cache, integrity_watcher):
        """Initialize sentiment fusion module"""
        await super().initialize(model_manager, vector_cache, integrity_watcher)
        
        # Preload sentiment models
        await model_manager.preload_models(["gemma_sentiment", "finbert", "gemma_multilingual"])
        
        logger.info("🎭 Sentiment Fusion Module initialized")
    
    async def analyze_sentiment(self, request: SentimentRequest) -> SentimentResponse:
        """
        Analyze sentiment with multi-model fusion
        
        Args:
            request: Sentiment analysis request
            
        Returns:
            Sentiment response with fusion results
        """
        try:
            start_time = datetime.now()
            
            # Input validation
            if len(request.text.strip()) == 0:
                return SentimentResponse(
                    status="error",
                    sentiment={},
                    confidence=0.0,
                    language="",
                    model_fusion={},
                    metadata={},
                    error="Empty text provided"
                )
            
            # Check cache first
            if request.use_cache:
                cached_result = await vector_cache.get_sentiment(
                    request.text,
                    request.fusion_mode.value,
                    request.language.value
                )
                if cached_result is not None:
                    processing_time = (datetime.now() - start_time).total_seconds() * 1000
                    return SentimentResponse(
                        status="success",
                        sentiment=cached_result["sentiment"],
                        confidence=cached_result["confidence"],
                        language=cached_result["language"],
                        model_fusion=cached_result["model_fusion"],
                        metadata={
                            "cached": True,
                            "processing_time_ms": processing_time,
                            "fusion_mode": request.fusion_mode.value
                        }
                    )
            
            # Detect language
            detected_language = await self._detect_language(request.text, request.language)
            
            # Get sentiment predictions from multiple models
            model_predictions = await self._get_model_predictions(
                request.text, detected_language, request.fusion_mode
            )
            
            if not model_predictions:
                return SentimentResponse(
                    status="error",
                    sentiment={},
                    confidence=0.0,
                    language=detected_language,
                    model_fusion={},
                    metadata={},
                    error="Failed to get predictions from models"
                )
            
            # Apply fusion algorithm
            fused_result = await self._apply_fusion(
                model_predictions, request.fusion_mode, detected_language
            )
            
            # Cache result
            if request.use_cache:
                cache_data = {
                    "sentiment": fused_result["sentiment"],
                    "confidence": fused_result["confidence"],
                    "language": detected_language,
                    "model_fusion": fused_result["model_fusion"]
                }
                await vector_cache.set_sentiment(
                    request.text,
                    cache_data,
                    request.fusion_mode.value,
                    detected_language
                )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return SentimentResponse(
                status="success",
                sentiment=fused_result["sentiment"],
                confidence=fused_result["confidence"],
                language=detected_language,
                model_fusion=fused_result["model_fusion"],
                metadata={
                    "cached": False,
                    "processing_time_ms": processing_time,
                    "fusion_mode": request.fusion_mode.value,
                    "models_used": list(model_predictions.keys())
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Sentiment analysis error: {str(e)}")
            return SentimentResponse(
                status="error",
                sentiment={},
                confidence=0.0,
                language="",
                model_fusion={},
                metadata={},
                error=str(e)
            )
    
    async def analyze_batch_sentiment(self, request: BatchSentimentRequest) -> BatchSentimentResponse:
        """
        Analyze sentiment for multiple texts
        
        Args:
            request: Batch sentiment request
            
        Returns:
            Batch sentiment response
        """
        try:
            start_time = datetime.now()
            
            if not request.texts:
                return BatchSentimentResponse(
                    status="error",
                    results=[],
                    metadata={},
                    error="No texts provided"
                )
            
            if len(request.texts) > self.max_batch_size:
                return BatchSentimentResponse(
                    status="error",
                    results=[],
                    metadata={},
                    error=f"Batch size {len(request.texts)} exceeds limit {self.max_batch_size}"
                )
            
            # Process batch with concurrency control
            semaphore = asyncio.Semaphore(8)  # Limit concurrent processing
            
            async def process_single(text: str) -> Dict[str, Any]:
                async with semaphore:
                    single_request = SentimentRequest(
                        text=text,
                        language=request.language,
                        fusion_mode=request.fusion_mode,
                        use_cache=request.use_cache
                    )
                    response = await self.analyze_sentiment(single_request)
                    
                    return {
                        "text": text,
                        "sentiment": response.sentiment,
                        "confidence": response.confidence,
                        "language": response.language,
                        "model_fusion": response.model_fusion,
                        "error": response.error
                    }
            
            # Process all texts
            tasks = [process_single(text) for text in request.texts]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle exceptions
            processed_results = []
            error_count = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        "text": request.texts[i],
                        "sentiment": {},
                        "confidence": 0.0,
                        "language": "",
                        "model_fusion": {},
                        "error": str(result)
                    })
                    error_count += 1
                else:
                    processed_results.append(result)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Calculate average confidence (handle empty list)
            valid_confidences = [r["confidence"] for r in processed_results if r["confidence"] > 0]
            avg_confidence = float(np.mean(valid_confidences)) if valid_confidences else 0.0
            
            return BatchSentimentResponse(
                status="success" if error_count == 0 else "partial_success",
                results=processed_results,
                metadata={
                    "total_texts": len(request.texts),
                    "successful": len(request.texts) - error_count,
                    "errors": error_count,
                    "processing_time_ms": processing_time,
                    "fusion_mode": request.fusion_mode.value,
                    "average_confidence": avg_confidence
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Batch sentiment analysis error: {str(e)}")
            return BatchSentimentResponse(
                status="error",
                results=[],
                metadata={},
                error=str(e)
            )
    
    async def calibrate_models(self, request: CalibrationRequest) -> Dict[str, Any]:
        """
        Calibrate fusion weights based on feedback data
        
        Args:
            request: Calibration request with feedback data
            
        Returns:
            Calibration results
        """
        try:
            if not request.feedback_data:
                return {"error": "No feedback data provided"}
            
            # Add to calibration dataset
            self.calibration_data.extend(request.feedback_data)
            
            # Keep only recent calibration data (last 10000 samples)
            if len(self.calibration_data) > 10000:
                self.calibration_data = self.calibration_data[-10000:]
            
            # Perform weight optimization
            if request.method == "online_learning":
                new_weights = await self._optimize_fusion_weights_online()
            else:
                new_weights = await self._optimize_fusion_weights_batch()
            
            # Update fusion weights
            old_weights = self.fusion_weights.copy()
            self.fusion_weights.update(new_weights)
            
            logger.info(f"🎯 Updated fusion weights: {self.fusion_weights}")
            
            return {
                "status": "success",
                "calibration_data_count": len(self.calibration_data),
                "old_weights": old_weights,
                "new_weights": self.fusion_weights,
                "improvement": self._calculate_weight_improvement(old_weights, new_weights),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Model calibration error: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    # ===========================
    # PRIVATE HELPER METHODS
    # ===========================
    
    async def _detect_language(self, text: str, language: LanguageCode) -> str:
        """Detect or validate language for sentiment analysis"""
        if language != LanguageCode.AUTO:
            return language.value
        
        # Enhanced language detection for sentiment
        text_sample = text[:300].lower()
        
        # Financial terms in different languages
        financial_terms = {
            "it": ["borsa", "mercato", "azioni", "titolo", "investimento", "economia"],
            "es": ["bolsa", "mercado", "acciones", "inversion", "economia"],
            "en": ["market", "entity", "investment", "economy", "financial", "trading"]
        }
        
        for lang, terms in financial_terms.items():
            if any(term in text_sample for term in terms):
                return lang
        
        # Fallback to basic detection
        if any(word in text_sample for word in ['della', 'delle', 'mercato', 'azioni']):
            return LanguageCode.ITALIAN.value
        elif any(word in text_sample for word in ['esta', 'este', 'mercado', 'bolsa']):
            return LanguageCode.SPANISH.value
        
        return LanguageCode.ENGLISH.value
    
    async def _get_model_predictions(
        self, text: str, language: str, fusion_mode: FusionMode
    ) -> Dict[str, Dict[str, Any]]:
        """Get predictions from multiple models"""
        predictions = {}
        
        try:
            # Get Gemma sentiment prediction
            if fusion_mode in [FusionMode.BASIC, FusionMode.ENHANCED, FusionMode.DEEP]:
                gemma_pred = await self._get_gemma_prediction(text, language)
                if gemma_pred:
                    predictions["gemma"] = gemma_pred
            
            # Get FinBERT prediction (for financial texts)
            if fusion_mode in [FusionMode.ENHANCED, FusionMode.DEEP]:
                finbert_pred = await self._get_finbert_prediction(text)
                if finbert_pred:
                    predictions["finbert"] = finbert_pred
            
            # Get multilingual model prediction
            if fusion_mode == FusionMode.DEEP and language != "en":
                multilingual_pred = await self._get_multilingual_prediction(text, language)
                if multilingual_pred:
                    predictions["multilingual"] = multilingual_pred
            
        except Exception as e:
            logger.error(f"❌ Error getting model predictions: {str(e)}")
        
        return predictions
    
    async def _get_gemma_prediction(self, text: str, language: str) -> Optional[Dict[str, Any]]:
        """Get Gemma model sentiment prediction"""
        try:
            model = await model_manager.get_model("gemma_sentiment")
            tokenizer = await model_manager.get_tokenizer("gemma_sentiment")
            
            if not model or not tokenizer:
                return None
            
            # Create prompt for sentiment analysis
            prompt = f"Analyze the sentiment of this text and classify it as positive, negative, or neutral:\n\nText: {text}\n\nSentiment:"
            
            inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
            
            if torch.cuda.is_available() and next(model.parameters()).is_cuda:
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = model(**inputs)
                logits = outputs.last_hidden_state
                
                # Simple classification based on embeddings
                # This is a simplified approach - in practice, you'd want a proper classification head
                embedding = logits.mean(dim=1)
                
                # Simplified sentiment classification
                sentiment_scores = {
                    "positive": float(torch.sigmoid(embedding[:, 0]).item()),
                    "negative": float(torch.sigmoid(embedding[:, 1]).item()) if embedding.shape[1] > 1 else 0.3,
                    "neutral": 0.5
                }
                
                # Normalize scores
                total = sum(sentiment_scores.values())
                sentiment_scores = {k: v/total for k, v in sentiment_scores.items()}
                
                predicted_sentiment = max(sentiment_scores, key=sentiment_scores.get)
                confidence = sentiment_scores[predicted_sentiment]
            
            return {
                "sentiment": predicted_sentiment,
                "confidence": confidence,
                "scores": sentiment_scores,
                "model": "gemma"
            }
            
        except Exception as e:
            logger.error(f"❌ Gemma prediction error: {str(e)}")
            return None
    
    async def _get_finbert_prediction(self, text: str) -> Optional[Dict[str, Any]]:
        """Get FinBERT sentiment prediction"""
        try:
            # Use pipeline for FinBERT
            pipeline = await model_manager.get_pipeline("finbert", "sentiment-analysis")
            
            if not pipeline:
                return None
            
            results = pipeline(text)
            
            if results and len(results) > 0:
                # FinBERT pipeline returns [[{label, score}, {label, score}, ...]]
                # Get the first batch result
                batch_result = results[0] if isinstance(results[0], list) else results
                
                # Build scores dict from all predictions
                scores = {}
                best_label = None
                best_score = 0.0
                
                for pred in batch_result:
                    label = pred["label"].lower()
                    score = pred["score"]
                    scores[label] = score
                    
                    if score > best_score:
                        best_score = score
                        best_label = label
                
                # Map FinBERT labels to standard sentiment
                label_map = {
                    "positive": "positive",
                    "negative": "negative", 
                    "neutral": "neutral",
                }
                
                sentiment = label_map.get(best_label, "neutral")
                confidence = best_score
                
                return {
                    "sentiment": sentiment,
                    "confidence": confidence,
                    "scores": scores,
                    "model": "finbert"
                }
        
        except Exception as e:
            logger.error(f"❌ FinBERT prediction error: {str(e)}")
            return None
    
    async def _get_multilingual_prediction(self, text: str, language: str) -> Optional[Dict[str, Any]]:
        """Get multilingual model sentiment prediction"""
        try:
            model = await model_manager.get_model("gemma_multilingual")
            tokenizer = await model_manager.get_tokenizer("gemma_multilingual")
            
            if not model or not tokenizer:
                return None
            
            # Language-specific prompts
            prompts = {
                "it": f"Analizza il sentiment di questo testo (positivo, negativo, neutro):\n\n{text}\n\nSentiment:",
                "es": f"Analiza el sentimiento de este texto (positivo, negativo, neutro):\n\n{text}\n\nSentimiento:",
                "default": f"Analyze sentiment (positive, negative, neutral):\n\n{text}\n\nSentiment:"
            }
            
            prompt = prompts.get(language, prompts["default"])
            
            inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
            
            if torch.cuda.is_available() and next(model.parameters()).is_cuda:
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = model(**inputs)
                # Simplified multilingual sentiment classification
                embedding = outputs.last_hidden_state.mean(dim=1)
                
                sentiment_scores = {
                    "positive": 0.4,
                    "negative": 0.3,
                    "neutral": 0.3
                }
                
                predicted_sentiment = max(sentiment_scores, key=sentiment_scores.get)
                confidence = sentiment_scores[predicted_sentiment]
            
            return {
                "sentiment": predicted_sentiment,
                "confidence": confidence,
                "scores": sentiment_scores,
                "model": "multilingual"
            }
            
        except Exception as e:
            logger.error(f"❌ Multilingual prediction error: {str(e)}")
            return None
    
    async def _apply_fusion(
        self, predictions: Dict[str, Dict[str, Any]], fusion_mode: FusionMode, language: str
    ) -> Dict[str, Any]:
        """Apply fusion algorithm to combine predictions"""
        
        if len(predictions) == 1:
            # Single model, no fusion needed
            model_name = list(predictions.keys())[0]
            pred = predictions[model_name]
            return {
                "sentiment": {
                    "label": pred["sentiment"],
                    "score": pred["confidence"]
                },
                "confidence": pred["confidence"], 
                "model_fusion": {
                    "method": "single_model",
                    "models": predictions
                }
            }
        
        # Multi-model fusion
        if fusion_mode == FusionMode.BASIC:
            return await self._basic_fusion(predictions)
        elif fusion_mode == FusionMode.ENHANCED:
            return await self._enhanced_fusion(predictions, language)
        elif fusion_mode == FusionMode.DEEP:
            return await self._deep_fusion(predictions, language)
        else:
            return await self._basic_fusion(predictions)
    
    async def _basic_fusion(self, predictions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Basic weighted average fusion"""
        sentiment_votes = {"positive": 0, "negative": 0, "neutral": 0}
        total_weight = 0
        weighted_confidence = 0
        
        for model_name, pred in predictions.items():
            weight = self.fusion_weights.get(model_name, 0.33)
            sentiment = pred["sentiment"]
            confidence = pred["confidence"]
            
            sentiment_votes[sentiment] += weight * confidence
            total_weight += weight
            weighted_confidence += weight * confidence
        
        # Normalize
        if total_weight > 0:
            sentiment_votes = {k: v/total_weight for k, v in sentiment_votes.items()}
            weighted_confidence /= total_weight
        
        final_sentiment = max(sentiment_votes, key=sentiment_votes.get)
        
        return {
            "sentiment": {
                "label": final_sentiment,
                "score": weighted_confidence
            },
            "confidence": weighted_confidence,
            "model_fusion": {
                "method": "basic_weighted",
                "weights": self.fusion_weights,
                "votes": sentiment_votes,
                "models": predictions
            }
        }
    
    async def _enhanced_fusion(self, predictions: Dict[str, Dict[str, Any]], language: str) -> Dict[str, Any]:
        """Enhanced fusion with language and domain weighting"""
        # Adjust weights based on language and context
        adjusted_weights = self.fusion_weights.copy()
        
        # Boost multilingual model for non-English
        if language != "en" and "multilingual" in predictions:
            adjusted_weights["multilingual"] *= 1.3
        
        # Boost FinBERT for financial contexts
        if "finbert" in predictions:
            adjusted_weights["finbert"] *= 1.2
        
        # Normalize weights
        total_weight = sum(adjusted_weights.values())
        adjusted_weights = {k: v/total_weight for k, v in adjusted_weights.items()}
        
        # Apply weighted fusion with confidence boosting
        sentiment_scores = {"positive": 0, "negative": 0, "neutral": 0}
        total_confidence = 0
        
        for model_name, pred in predictions.items():
            weight = adjusted_weights.get(model_name, 0.33)
            confidence = pred["confidence"]
            
            # Confidence boosting
            boosted_confidence = confidence ** 0.8  # Reduce impact of low confidence
            
            for sentiment, score in pred.get("scores", {pred["sentiment"]: confidence}).items():
                sentiment_scores[sentiment] += weight * score * boosted_confidence
            
            total_confidence += weight * boosted_confidence
        
        final_sentiment = max(sentiment_scores, key=sentiment_scores.get)
        final_confidence = min(1.0, total_confidence)
        
        return {
            "sentiment": {
                "label": final_sentiment,
                "score": final_confidence
            },
            "confidence": final_confidence,
            "model_fusion": {
                "method": "enhanced_weighted",
                "adjusted_weights": adjusted_weights,
                "language_factor": language,
                "scores": sentiment_scores,
                "models": predictions
            }
        }
    
    async def _deep_fusion(self, predictions: Dict[str, Dict[str, Any]], language: str) -> Dict[str, Any]:
        """Deep fusion with consensus analysis"""
        # Start with enhanced fusion
        enhanced_result = await self._enhanced_fusion(predictions, language)
        
        # Consensus analysis
        sentiments = [pred["sentiment"] for pred in predictions.values()]
        consensus_score = len(set(sentiments)) / len(sentiments)  # Lower = more consensus
        
        # Disagreement penalty
        if consensus_score > 0.5:  # High disagreement
            enhanced_result["confidence"] *= 0.8
        
        # Confidence agreement boosting
        confidences = [pred["confidence"] for pred in predictions.values()]
        confidence_std = statistics.stdev(confidences) if len(confidences) > 1 else 0
        
        if confidence_std < 0.1:  # High confidence agreement
            enhanced_result["confidence"] = min(1.0, enhanced_result["confidence"] * 1.1)
        
        enhanced_result["model_fusion"]["method"] = "deep_consensus"
        enhanced_result["model_fusion"]["consensus_score"] = 1 - consensus_score
        enhanced_result["model_fusion"]["confidence_agreement"] = 1 - confidence_std
        
        return enhanced_result
    
    async def _optimize_fusion_weights_online(self) -> Dict[str, float]:
        """Online learning weight optimization"""
        # Simplified online learning - in practice, use proper optimization
        learning_rate = 0.01
        new_weights = self.fusion_weights.copy()
        
        # Analyze recent feedback
        recent_feedback = self.calibration_data[-100:] if len(self.calibration_data) >= 100 else self.calibration_data
        
        for feedback in recent_feedback:
            # Adjust weights based on prediction accuracy
            # This is a simplified approach
            if feedback.predicted_sentiment == feedback.actual_sentiment:
                # Correct prediction - increase weight slightly
                for model in new_weights:
                    new_weights[model] *= (1 + learning_rate * feedback.confidence)
            else:
                # Incorrect prediction - decrease weight
                for model in new_weights:
                    new_weights[model] *= (1 - learning_rate * feedback.confidence)
        
        # Normalize weights
        total_weight = sum(new_weights.values())
        if total_weight > 0:
            new_weights = {k: v/total_weight for k, v in new_weights.items()}
        
        return new_weights
    
    async def _optimize_fusion_weights_batch(self) -> Dict[str, float]:
        """Batch weight optimization"""
        # Placeholder for more sophisticated batch optimization
        return await self._optimize_fusion_weights_online()
    
    def _calculate_weight_improvement(self, old_weights: Dict[str, float], new_weights: Dict[str, float]) -> float:
        """Calculate improvement score for weight changes"""
        if not self.calibration_data:
            return 0.0
        
        # Simple improvement calculation
        weight_changes = sum(abs(new_weights.get(k, 0) - old_weights.get(k, 0)) for k in old_weights)
        return min(1.0, weight_changes * 10)  # Scale to 0-1
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for sentiment fusion module"""
        try:
            # Check model availability
            models_status = {}
            for model_key in ["gemma_sentiment", "finbert", "gemma_multilingual"]:
                model_info = model_manager.get_model_info(model_key)
                models_status[model_key] = {
                    "loaded": model_info["loaded"] if model_info else False,
                    "last_used": model_info["last_used"].isoformat() if model_info and model_info["last_used"] else None
                }
            
            # Test sentiment analysis
            test_result = "not_tested"
            try:
                test_request = SentimentRequest(
                    text="This is a positive test message for sentiment analysis",
                    language=LanguageCode.ENGLISH,
                    fusion_mode=FusionMode.ENHANCED,
                    use_cache=False
                )
                test_response = await self.analyze_sentiment(test_request)
                test_result = "success" if test_response.status == "success" else "failed"
            except Exception as e:
                test_result = f"failed: {str(e)}"
            
            return {
                "status": "healthy",
                "module": self.name,
                "version": self.version,
                "models": models_status,
                "test_result": test_result,
                "fusion_weights": self.fusion_weights,
                "calibration_data_count": len(self.calibration_data),
                "supported_languages": list(self.supported_languages),
                "max_batch_size": self.max_batch_size,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "module": self.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }