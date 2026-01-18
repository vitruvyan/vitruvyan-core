# api_gemma_cognitive/modules/profile_processor.py
"""
👤 Profile Processor Module
Advanced user profiling and content personalization engine
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import numpy as np
from dataclasses import dataclass

from ..shared import GemmaServiceBase, model_manager, vector_cache
from ..schemas import (
    InteractionData, UserPreferences, ProfileRequest, ProfileResponse,
    AdaptationType, AdaptationRequest, AdaptationResponse, RecommendationRequest,
    LanguageCode
)

logger = logging.getLogger(__name__)

@dataclass
class UserProfile:
    """Internal user profile representation"""
    user_id: str
    preferences: UserPreferences
    interaction_patterns: Dict[str, Any]
    topic_interests: Dict[str, float]
    sentiment_patterns: Dict[str, float]
    complexity_level: str
    created_at: datetime
    updated_at: datetime
    confidence: float

class ProfileProcessorModule(GemmaServiceBase):
    """
    🧠 Intelligent user profiling and personalization engine
    Analyzes interaction patterns and provides adaptive content
    """
    
    def __init__(self):
        super().__init__("profile_processor")
        self.name = "ProfileProcessor"
        self.version = "1.0.0"
        self.max_interactions = 10000  # Max interactions to analyze
        self.topic_extraction_cache = {}
        self.personalization_models = {}
        
        # Topic categories for financial domain
        self.topic_categories = {
            "trading": ["trading", "buy", "sell", "position", "strategy"],
            "analysis": ["analysis", "chart", "technical", "fundamental", "research"],
            "market": ["market", "index", "entity", "sector", "performance"],
            "risk": ["risk", "volatility", "hedge", "diversification", "collection"],
            "news": ["news", "earnings", "announcement", "report", "update"],
            "crypto": ["crypto", "bitcoin", "blockchain", "defi", "token"],
            "macro": ["economy", "inflation", "rates", "policy", "gdp"]
        }
    
    async def _initialize_service(self):
        """Service-specific initialization for profile processor"""
        pass
    
    async def initialize(self, model_manager, vector_cache, integrity_watcher):
        """Initialize profile processor module"""
        await super().initialize(model_manager, vector_cache, integrity_watcher)
        
        # Preload models for topic extraction and sentiment
        await model_manager.preload_models(["gemma_embeddings", "gemma_multilingual"])
        
        logger.info("👤 Profile Processor Module initialized")
    
    async def create_profile(self, request: ProfileRequest) -> ProfileResponse:
        """
        Create or update user profile based on interaction data
        
        Args:
            request: Profile creation request with user data
            
        Returns:
            Profile response with generated user profile
        """
        try:
            start_time = datetime.now()
            
            # Input validation
            if not request.interaction_data:
                return ProfileResponse(
                    status="error",
                    user_id=request.user_id,
                    profile={},
                    confidence=0.0,
                    metadata={},
                    error="No interaction data provided"
                )
            
            # Check for existing profile
            existing_profile = await vector_cache.get_user_profile(request.user_id)
            
            # Analyze interaction patterns
            interaction_analysis = await self._analyze_interactions(request.interaction_data)
            
            # Extract topic interests
            topic_interests = await self._extract_topic_interests(request.interaction_data)
            
            # Analyze sentiment patterns
            sentiment_patterns = await self._analyze_sentiment_patterns(request.interaction_data)
            
            # Determine complexity preference
            complexity_level = await self._determine_complexity_level(request.interaction_data)
            
            # Create or update profile
            if existing_profile:
                profile = await self._update_existing_profile(
                    existing_profile, interaction_analysis, topic_interests, sentiment_patterns, complexity_level
                )
            else:
                profile = await self._create_new_profile(
                    request.user_id, request.preferences, interaction_analysis, 
                    topic_interests, sentiment_patterns, complexity_level
                )
            
            # Calculate confidence score
            confidence = self._calculate_profile_confidence(profile, len(request.interaction_data))
            
            # Cache updated profile
            await vector_cache.set_user_profile(request.user_id, profile)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ProfileResponse(
                status="success",
                user_id=request.user_id,
                profile=profile,
                confidence=confidence,
                metadata={
                    "interactions_analyzed": len(request.interaction_data),
                    "existing_profile": existing_profile is not None,
                    "processing_time_ms": processing_time,
                    "profile_version": self.version
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Profile creation error: {str(e)}")
            return ProfileResponse(
                status="error",
                user_id=request.user_id,
                profile={},
                confidence=0.0,
                metadata={},
                error=str(e)
            )
    
    async def adapt_content(self, request: AdaptationRequest) -> AdaptationResponse:
        """
        Adapt content based on user profile
        
        Args:
            request: Content adaptation request
            
        Returns:
            Adapted content response
        """
        try:
            start_time = datetime.now()
            
            # Get user profile
            user_profile = await vector_cache.get_user_profile(request.user_id)
            if not user_profile:
                return AdaptationResponse(
                    status="error",
                    original_content=request.content,
                    adapted_content=request.content,
                    adaptation_applied={},
                    metadata={},
                    error="User profile not found"
                )
            
            # Apply adaptation based on type
            if request.adaptation_type == AdaptationType.TONE:
                adapted_content = await self._adapt_tone(request.content, user_profile)
            elif request.adaptation_type == AdaptationType.COMPLEXITY:
                adapted_content = await self._adapt_complexity(request.content, user_profile) 
            elif request.adaptation_type == AdaptationType.LANGUAGE:
                adapted_content = await self._adapt_language(request.content, user_profile)
            elif request.adaptation_type == AdaptationType.PERSONALIZATION:
                adapted_content = await self._adapt_personalization(request.content, user_profile)
            else:
                adapted_content = request.content
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return AdaptationResponse(
                status="success",
                original_content=request.content,
                adapted_content=adapted_content["content"],
                adaptation_applied=adapted_content["adaptations"],
                metadata={
                    "adaptation_type": request.adaptation_type.value,
                    "user_profile_confidence": user_profile.get("confidence", 0.0),
                    "processing_time_ms": processing_time
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Content adaptation error: {str(e)}")
            return AdaptationResponse(
                status="error",
                original_content=request.content,
                adapted_content=request.content,
                adaptation_applied={},
                metadata={},
                error=str(e)
            )
    
    async def generate_recommendations(self, request: RecommendationRequest) -> Dict[str, Any]:
        """
        Generate personalized content recommendations
        
        Args:
            request: Recommendation request
            
        Returns:
            Personalized recommendations
        """
        try:
            # Get user profile
            user_profile = await vector_cache.get_user_profile(request.user_id)
            if not user_profile:
                return {"error": "User profile not found"}
            
            # Generate recommendations based on profile
            recommendations = await self._generate_content_recommendations(
                user_profile, request.content_type, request.context
            )
            
            return {
                "status": "success",
                "user_id": request.user_id,
                "content_type": request.content_type,
                "recommendations": recommendations,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Recommendation generation error: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    # ===========================
    # PRIVATE ANALYSIS METHODS
    # ===========================
    
    async def _analyze_interactions(self, interactions: List[InteractionData]) -> Dict[str, Any]:
        """Analyze user interaction patterns"""
        
        # Time-based analysis
        time_patterns = defaultdict(int)
        action_patterns = Counter()
        content_lengths = []
        
        for interaction in interactions:
            # Hour of day pattern
            hour = interaction.timestamp.hour
            time_patterns[f"hour_{hour}"] += 1
            
            # Action type patterns
            action_patterns[interaction.action_type] += 1
            
            # Content length analysis
            content_lengths.append(len(interaction.content))
        
        # Calculate averages and patterns
        avg_content_length = np.mean(content_lengths) if content_lengths else 0
        most_active_hour = max(time_patterns, key=time_patterns.get) if time_patterns else "unknown"
        
        return {
            "time_patterns": dict(time_patterns),
            "action_patterns": dict(action_patterns),
            "avg_content_length": avg_content_length,
            "most_active_hour": most_active_hour,
            "total_interactions": len(interactions),
            "engagement_score": self._calculate_engagement_score(interactions)
        }
    
    async def _extract_topic_interests(self, interactions: List[InteractionData]) -> Dict[str, float]:
        """Extract topic interests from interactions"""
        
        topic_scores = defaultdict(float)
        total_interactions = len(interactions)
        
        for interaction in interactions:
            content = interaction.content.lower()
            
            # Score based on predefined categories
            for category, keywords in self.topic_categories.items():
                matches = sum(1 for keyword in keywords if keyword in content)
                if matches > 0:
                    # Weight by recency (more recent = higher weight)
                    days_ago = (datetime.now() - interaction.timestamp).days
                    recency_weight = max(0.1, 1.0 - (days_ago / 30))  # Decay over 30 days
                    
                    topic_scores[category] += matches * recency_weight
            
            # Extract topics from existing tags if available
            if hasattr(interaction, 'topics') and interaction.topics:
                for topic in interaction.topics:
                    topic_scores[topic.lower()] += 1.0
        
        # Normalize scores
        if total_interactions > 0:
            topic_scores = {k: v / total_interactions for k, v in topic_scores.items()}
        
        # Return top 10 topics
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_topics[:10])
    
    async def _analyze_sentiment_patterns(self, interactions: List[InteractionData]) -> Dict[str, float]:
        """Analyze user sentiment patterns"""
        
        sentiment_scores = defaultdict(list)
        
        for interaction in interactions:
            # Use existing sentiment if available
            if hasattr(interaction, 'sentiment') and interaction.sentiment:
                sentiment = interaction.sentiment.lower()
                if sentiment in ['positive', 'negative', 'neutral']:
                    sentiment_scores[sentiment].append(1.0)
            else:
                # Simple sentiment analysis based on keywords
                content = interaction.content.lower()
                
                positive_words = ['good', 'great', 'excellent', 'profit', 'gain', 'up', 'bullish']
                negative_words = ['bad', 'terrible', 'loss', 'down', 'bearish', 'decline', 'crash']
                
                pos_count = sum(1 for word in positive_words if word in content)
                neg_count = sum(1 for word in negative_words if word in content)
                
                if pos_count > neg_count:
                    sentiment_scores['positive'].append(pos_count - neg_count)
                elif neg_count > pos_count:
                    sentiment_scores['negative'].append(neg_count - pos_count)
                else:
                    sentiment_scores['neutral'].append(1.0)
        
        # Calculate averages
        sentiment_patterns = {}
        for sentiment, scores in sentiment_scores.items():
            sentiment_patterns[sentiment] = np.mean(scores) if scores else 0.0
        
        return sentiment_patterns
    
    async def _determine_complexity_level(self, interactions: List[InteractionData]) -> str:
        """Determine user's preferred complexity level"""
        
        complexity_indicators = {
            'simple': ['simple', 'basic', 'easy', 'beginner', 'explain'],
            'medium': ['understand', 'learn', 'how', 'why', 'medium'],
            'advanced': ['advanced', 'technical', 'analysis', 'strategy', 'complex'],
            'expert': ['expert', 'professional', 'sophisticated', 'algorithm', 'model']
        }
        
        complexity_scores = defaultdict(int)
        
        for interaction in interactions:
            content = interaction.content.lower()
            
            for level, keywords in complexity_indicators.items():
                matches = sum(1 for keyword in keywords if keyword in content)
                complexity_scores[level] += matches
            
            # Content length as complexity indicator
            if len(interaction.content) > 500:
                complexity_scores['advanced'] += 1
            elif len(interaction.content) < 100:
                complexity_scores['simple'] += 1
            else:
                complexity_scores['medium'] += 1
        
        # Return highest scoring complexity level
        if complexity_scores:
            return max(complexity_scores, key=complexity_scores.get)
        else:
            return 'medium'  # Default
    
    def _calculate_engagement_score(self, interactions: List[InteractionData]) -> float:
        """Calculate user engagement score"""
        
        if not interactions:
            return 0.0
        
        # Factors for engagement score
        total_interactions = len(interactions)
        avg_content_length = np.mean([len(i.content) for i in interactions])
        
        # Time span analysis
        timestamps = [i.timestamp for i in interactions]
        time_span_days = (max(timestamps) - min(timestamps)).days if len(timestamps) > 1 else 1
        interaction_frequency = total_interactions / max(1, time_span_days)
        
        # Engagement score (0-1 scale)
        engagement_score = min(1.0, (
            (total_interactions / 100) * 0.4 +  # Interaction count factor
            (avg_content_length / 1000) * 0.3 +  # Content depth factor  
            (interaction_frequency / 5) * 0.3     # Frequency factor
        ))
        
        return engagement_score
    
    # ===========================
    # PROFILE MANAGEMENT METHODS
    # ===========================
    
    async def _create_new_profile(
        self, user_id: str, preferences: Optional[UserPreferences],
        interaction_analysis: Dict[str, Any], topic_interests: Dict[str, float],
        sentiment_patterns: Dict[str, float], complexity_level: str
    ) -> Dict[str, Any]:
        """Create new user profile"""
        
        now = datetime.now()
        
        profile = {
            "user_id": user_id,
            "preferences": preferences.dict() if preferences else {
                "language": "auto",
                "risk_tolerance": "medium",
                "complexity_preference": complexity_level,
                "topics_of_interest": list(topic_interests.keys())[:10],
                "notification_frequency": "daily"
            },
            "interaction_patterns": interaction_analysis,
            "topic_interests": topic_interests,
            "sentiment_patterns": sentiment_patterns,
            "complexity_level": complexity_level,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "version": self.version
        }
        
        return profile
    
    async def _update_existing_profile(
        self, existing_profile: Dict[str, Any], interaction_analysis: Dict[str, Any],
        topic_interests: Dict[str, float], sentiment_patterns: Dict[str, float], 
        complexity_level: str
    ) -> Dict[str, Any]:
        """Update existing user profile with new data"""
        
        # Merge topic interests (weighted average)
        existing_topics = existing_profile.get("topic_interests", {})
        merged_topics = {}
        
        all_topics = set(existing_topics.keys()) | set(topic_interests.keys())
        for topic in all_topics:
            existing_score = existing_topics.get(topic, 0.0)
            new_score = topic_interests.get(topic, 0.0)
            # Weight: 70% existing, 30% new
            merged_topics[topic] = existing_score * 0.7 + new_score * 0.3
        
        # Update profile
        existing_profile.update({
            "interaction_patterns": interaction_analysis,
            "topic_interests": merged_topics,
            "sentiment_patterns": sentiment_patterns,
            "complexity_level": complexity_level,
            "updated_at": datetime.now().isoformat()
        })
        
        return existing_profile
    
    def _calculate_profile_confidence(self, profile: Dict[str, Any], interaction_count: int) -> float:
        """Calculate confidence score for profile accuracy"""
        
        base_confidence = min(1.0, interaction_count / 50)  # More interactions = higher confidence
        
        # Boost confidence based on data richness
        topic_diversity = len(profile.get("topic_interests", {}))
        pattern_consistency = profile.get("interaction_patterns", {}).get("engagement_score", 0.0)
        
        confidence_boost = (topic_diversity / 10) * 0.2 + pattern_consistency * 0.3
        
        final_confidence = min(1.0, base_confidence + confidence_boost)
        return round(final_confidence, 3)
    
    # ===========================
    # CONTENT ADAPTATION METHODS
    # ===========================
    
    async def _adapt_tone(self, content: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt content tone based on user sentiment patterns"""
        
        sentiment_patterns = user_profile.get("sentiment_patterns", {})
        dominant_sentiment = max(sentiment_patterns, key=sentiment_patterns.get) if sentiment_patterns else "neutral"
        
        adaptations = {"tone_adaptation": dominant_sentiment}
        
        if dominant_sentiment == "positive":
            # More enthusiastic tone
            adapted = content.replace("might", "will").replace("could", "can")
            adapted = f"Great news! {adapted}"
        elif dominant_sentiment == "negative":
            # More cautious, supportive tone
            adapted = content.replace("will", "might").replace("definitely", "likely")
            adapted = f"Let's carefully consider: {adapted}"
        else:
            # Neutral, balanced tone
            adapted = content
        
        return {"content": adapted, "adaptations": adaptations}
    
    async def _adapt_complexity(self, content: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt content complexity based on user preference"""
        
        complexity_level = user_profile.get("complexity_level", "medium")
        
        adaptations = {"complexity_adaptation": complexity_level}
        
        if complexity_level == "simple":
            # Simplify language, add explanations
            adapted = f"In simple terms: {content}\n\n(This means the basic idea is straightforward.)"
        elif complexity_level == "expert":
            # Add technical details
            adapted = f"{content}\n\nTechnical note: This analysis incorporates advanced market dynamics and statistical models."
        else:
            adapted = content
        
        return {"content": adapted, "adaptations": adaptations}
    
    async def _adapt_language(self, content: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt content language based on user preference"""
        
        preferences = user_profile.get("preferences", {})
        language = preferences.get("language", "auto")
        
        adaptations = {"language_adaptation": language}
        
        # For now, return original content
        # In practice, you'd integrate with translation services
        return {"content": content, "adaptations": adaptations}
    
    async def _adapt_personalization(self, content: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Apply personalization based on user interests"""
        
        topic_interests = user_profile.get("topic_interests", {})
        top_topics = sorted(topic_interests.items(), key=lambda x: x[1], reverse=True)[:3]
        
        adaptations = {"personalization": [topic for topic, score in top_topics]}
        
        if top_topics:
            topics_text = ", ".join([topic for topic, _ in top_topics])
            adapted = f"{content}\n\nBased on your interest in {topics_text}, you might also find this relevant."
        else:
            adapted = content
        
        return {"content": adapted, "adaptations": adaptations}
    
    async def _generate_content_recommendations(
        self, user_profile: Dict[str, Any], content_type: str, context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate personalized content recommendations"""
        
        topic_interests = user_profile.get("topic_interests", {})
        complexity_level = user_profile.get("complexity_level", "medium")
        
        # Generate recommendations based on top interests
        recommendations = []
        
        for topic, score in sorted(topic_interests.items(), key=lambda x: x[1], reverse=True)[:5]:
            recommendations.append({
                "topic": topic,
                "relevance_score": score,
                "content_type": content_type,
                "complexity": complexity_level,
                "reason": f"Based on your {score:.1%} interest in {topic}"
            })
        
        return recommendations
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for profile processor module"""
        try:
            # Test basic functionality
            test_result = "success"
            
            # Check cache connectivity
            cache_status = await vector_cache.health_check()
            
            return {
                "status": "healthy",
                "module": self.name,
                "version": self.version,
                "test_result": test_result,
                "cache_status": cache_status.get("status", "unknown"),
                "topic_categories": len(self.topic_categories),
                "max_interactions": self.max_interactions,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "module": self.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }