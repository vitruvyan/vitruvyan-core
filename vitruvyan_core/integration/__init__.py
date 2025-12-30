"""
Vitruvyan Core Integration Utilities

Helper classes and patterns for vertical implementations to orchestrate
the complete cognitive pipeline: Neural Engine → VWRE → VARE → VEE

These are OPTIONAL convenience layers - verticals can implement
their own orchestration patterns if preferred.
"""

from typing import Dict, List, Any, Optional, Protocol
from datetime import datetime
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Core imports
from vitruvyan_core.core.cognitive.neural_engine import EvaluationOrchestrator
from vitruvyan_core.core.cognitive.vitruvyan_proprietary.vwre_engine import VWREngine
from vitruvyan_core.core.cognitive.vitruvyan_proprietary.vare_engine import VAREngine
from vitruvyan_core.core.cognitive.vitruvyan_proprietary.vee.vee_engine import VEEEngine

# Domain contracts
from vitruvyan_core.domains import (
    AggregationProvider, RiskProvider, ExplainabilityProvider
)


@dataclass
class PipelineResult:
    """Structured result from complete pipeline execution"""
    entity_id: str
    timestamp: datetime

    # Component results
    neural_result: Any
    attribution_result: Any
    risk_result: Any
    explanation_result: Any

    # Metadata
    pipeline_version: str = "3.0"
    execution_time_ms: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None


class VerticalOrchestrator(ABC):
    """
    Abstract base class for vertical orchestrators

    Provides common pipeline orchestration logic while allowing
    verticals to customize domain-specific behavior.
    """

    def __init__(self):
        # Initialize core engines (domain-agnostic)
        self.neural_orchestrator = EvaluationOrchestrator()
        self.vwre_engine = VWREngine()
        self.vare_engine = VAREngine()
        self.vee_engine = VEEEngine()

        # Domain providers (must be set by concrete implementations)
        self.aggregation_provider: Optional[AggregationProvider] = None
        self.risk_provider: Optional[RiskProvider] = None
        self.explainability_provider: Optional[ExplainabilityProvider] = None

    @abstractmethod
    def get_domain_factors(self) -> List[Any]:
        """Return domain-specific factors for Neural Engine"""
        pass

    @abstractmethod
    def get_normalizer(self) -> Any:
        """Return domain-appropriate normalizer"""
        pass

    @abstractmethod
    def get_aggregation_profile(self, entity_id: str) -> Any:
        """Return appropriate aggregation profile for entity"""
        pass

    def execute_pipeline(self, entity_id: str, entity_data: Dict[str, Any]) -> PipelineResult:
        """
        Execute complete cognitive pipeline

        Args:
            entity_id: Entity identifier
            entity_data: Raw entity data

        Returns:
            Structured pipeline result
        """
        start_time = datetime.now()

        try:
            # Validate providers are set
            if not all([self.aggregation_provider, self.risk_provider, self.explainability_provider]):
                raise ValueError("All domain providers must be set before pipeline execution")

            # Step 1: Neural Engine evaluation
            neural_result = self._execute_neural_evaluation(entity_id, entity_data)

            # Step 2: VWRE attribution
            attribution_result = self._execute_attribution_analysis(neural_result)

            # Step 3: VARE risk assessment
            risk_result = self._execute_risk_assessment(attribution_result)

            # Step 4: VEE explanation
            explanation_result = self._execute_explanation_generation(risk_result)

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            return PipelineResult(
                entity_id=entity_id,
                timestamp=datetime.now(),
                neural_result=neural_result,
                attribution_result=attribution_result,
                risk_result=risk_result,
                explanation_result=explanation_result,
                execution_time_ms=execution_time,
                success=True
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            return PipelineResult(
                entity_id=entity_id,
                timestamp=datetime.now(),
                neural_result=None,
                attribution_result=None,
                risk_result=None,
                explanation_result=None,
                execution_time_ms=execution_time,
                success=False,
                error_message=str(e)
            )

    def _execute_neural_evaluation(self, entity_id: str, entity_data: Dict[str, Any]) -> Any:
        """Execute Neural Engine evaluation"""
        # Implementation depends on Neural Engine interface
        # This is a placeholder - actual implementation would use
        # the EvaluationOrchestrator with domain factors
        raise NotImplementedError("Neural evaluation must be implemented by vertical")

    def _execute_attribution_analysis(self, neural_result: Any) -> Any:
        """Execute VWRE attribution analysis"""
        # Extract factor scores from neural result
        factor_scores = self._extract_factor_scores(neural_result)

        return self.vwre_engine.analyze_attribution(
            entity_id=neural_result.entity_id,
            composite_score=neural_result.composite_score,
            factors=factor_scores,
            aggregation_provider=self.aggregation_provider
        )

    def _execute_risk_assessment(self, attribution_result: Any) -> Any:
        """Execute VARE risk assessment"""
        # Create appropriate data structure for VARE
        # This may require domain-specific data preparation
        risk_data = self._prepare_risk_data(attribution_result)

        return self.vare_engine.analyze_entity(
            entity_id=attribution_result.entity_id,
            data=risk_data,
            risk_provider=self.risk_provider,
            profile_name="balanced"  # Default, can be made configurable
        )

    def _execute_explanation_generation(self, risk_result: Any) -> Any:
        """Execute VEE explanation generation"""
        # Prepare metrics for explanation
        metrics = self._prepare_explanation_metrics(risk_result)

        return self.vee_engine.explain_entity(
            entity_id=risk_result.entity_id,
            metrics=metrics,
            explainability_provider=self.explainability_provider
        )

    @abstractmethod
    def _extract_factor_scores(self, neural_result: Any) -> Dict[str, float]:
        """Extract factor scores from neural result for VWRE"""
        pass

    @abstractmethod
    def _prepare_risk_data(self, attribution_result: Any) -> Any:
        """Prepare data structure needed for VARE risk assessment"""
        pass

    @abstractmethod
    def _prepare_explanation_metrics(self, risk_result: Any) -> Dict[str, Any]:
        """Prepare metrics dictionary for VEE explanation"""
        pass


class BatchProcessor:
    """
    Utility for processing multiple entities in batch

    Provides parallel processing capabilities and result aggregation.
    """

    def __init__(self, orchestrator: VerticalOrchestrator, max_workers: int = 4):
        self.orchestrator = orchestrator
        self.max_workers = max_workers

    def process_batch(self, entities: List[Dict[str, Any]]) -> List[PipelineResult]:
        """
        Process multiple entities in batch

        Args:
            entities: List of entity data dictionaries, each containing 'entity_id'

        Returns:
            List of pipeline results
        """
        results = []

        for entity_data in entities:
            entity_id = entity_data.get('entity_id')
            if not entity_id:
                continue

            result = self.orchestrator.execute_pipeline(entity_id, entity_data)
            results.append(result)

        return results

    def get_batch_summary(self, results: List[PipelineResult]) -> Dict[str, Any]:
        """Generate summary statistics for batch processing"""
        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful

        avg_execution_time = sum(r.execution_time_ms or 0 for r in results if r.success) / successful if successful > 0 else 0

        return {
            'total_entities': total,
            'successful': successful,
            'failed': failed,
            'success_rate': successful / total if total > 0 else 0,
            'average_execution_time_ms': avg_execution_time,
            'timestamp': datetime.now().isoformat()
        }


class ResultAggregator:
    """
    Utility for aggregating and analyzing pipeline results

    Provides domain-agnostic aggregation capabilities that verticals
    can use for portfolio-level analysis, ranking, etc.
    """

    @staticmethod
    def rank_by_neural_score(results: List[PipelineResult]) -> List[PipelineResult]:
        """Rank results by neural engine composite score"""
        successful_results = [r for r in results if r.success and r.neural_result]
        return sorted(successful_results,
                     key=lambda r: r.neural_result.composite_score,
                     reverse=True)

    @staticmethod
    def rank_by_risk(results: List[PipelineResult]) -> List[PipelineResult]:
        """Rank results by risk score (lower risk first)"""
        successful_results = [r for r in results if r.success and r.risk_result]
        return sorted(successful_results,
                     key=lambda r: r.risk_result.overall_risk)

    @staticmethod
    def filter_by_risk_category(results: List[PipelineResult], category: str) -> List[PipelineResult]:
        """Filter results by risk category"""
        return [r for r in results
                if r.success and r.risk_result and r.risk_result.risk_category == category]

    @staticmethod
    def get_portfolio_summary(results: List[PipelineResult]) -> Dict[str, Any]:
        """Generate portfolio-level summary statistics"""
        successful_results = [r for r in results if r.success]

        if not successful_results:
            return {'error': 'No successful results to summarize'}

        # Neural score statistics
        neural_scores = [r.neural_result.composite_score for r in successful_results if r.neural_result]
        avg_neural = sum(neural_scores) / len(neural_scores) if neural_scores else 0

        # Risk statistics
        risk_scores = [r.risk_result.overall_risk for r in successful_results if r.risk_result]
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0

        # Risk category distribution
        risk_categories = {}
        for r in successful_results:
            if r.risk_result:
                cat = r.risk_result.risk_category
                risk_categories[cat] = risk_categories.get(cat, 0) + 1

        return {
            'entity_count': len(successful_results),
            'average_neural_score': avg_neural,
            'average_risk_score': avg_risk,
            'risk_category_distribution': risk_categories,
            'neural_score_range': (min(neural_scores), max(neural_scores)) if neural_scores else None,
            'risk_score_range': (min(risk_scores), max(risk_scores)) if risk_scores else None
        }


# Export public API
__all__ = [
    'PipelineResult',
    'VerticalOrchestrator',
    'BatchProcessor',
    'ResultAggregator'
]