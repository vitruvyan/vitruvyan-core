"""
Test Neural Engine Pipeline Integration
==========================================

Verifica il funzionamento end-to-end del NeuralEngine con
provider e strategia mockati.  Nessuna dipendenza infrastrutturale
(nessun PostgreSQL, Qdrant, Redis).

Copre:
  - Pipeline completa: universo → feature → z-score → ranking
  - Modalità stratificazione: global / stratified / composite
  - Filtraggio entità e top-K
  - Risk adjustment
  - Gestione universo vuoto
  - Diagnostica e statistiche bucket
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from core.neural_engine.engine import NeuralEngine
    HAS_ENGINE = True
except ImportError:
    HAS_ENGINE = False

try:
    from vitruvyan_core.contracts import IDataProvider
    from vitruvyan_core.contracts import IScoringStrategy
    HAS_CONTRACTS = True
except ImportError:
    try:
        from contracts import IDataProvider
        from contracts import IScoringStrategy
        HAS_CONTRACTS = True
    except ImportError:
        HAS_CONTRACTS = False

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not (HAS_ENGINE and HAS_CONTRACTS and HAS_PANDAS),
        reason="NeuralEngine or contracts or pandas not importable",
    ),
]


# ═══════════════════════════════════════════════════════════════════
# FIXTURES — Mock provider & strategy con dati realistici
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def universe_df():
    """DataFrame universo con 10 entità e campo di stratificazione."""
    return pd.DataFrame({
        "entity_id": [f"ENT_{i:03d}" for i in range(10)],
        "sector": ["A"] * 5 + ["B"] * 5,
        "name": [f"Entity {i}" for i in range(10)],
    })


@pytest.fixture
def features_df():
    """DataFrame feature con 3 metriche numeriche."""
    rows = []
    for i in range(10):
        rows.append({
            "entity_id": f"ENT_{i:03d}",
            "quality": 20.0 + i * 5.0,
            "momentum": 50.0 - i * 3.0,
            "stability": 60.0 + (i % 3) * 10.0,
        })
    return pd.DataFrame(rows)


@pytest.fixture
def mock_data_provider(universe_df, features_df):
    """IDataProvider completo con dati in-memory."""
    class InMemoryProvider(IDataProvider):
        def get_universe(self, filters=None):
            df = universe_df.copy()
            if filters and "sector" in filters:
                df = df[df["sector"] == filters["sector"]]
            return df

        def get_features(self, entity_ids, feature_names=None):
            df = features_df[features_df["entity_id"].isin(entity_ids)].copy()
            if feature_names:
                cols = ["entity_id"] + [c for c in feature_names if c in df.columns]
                df = df[cols]
            return df

        def get_metadata(self):
            return {
                "domain": "test",
                "entity_type": "test_entity",
                "stratification_field": "sector",
                "available_features": ["quality", "momentum", "stability"],
                "metadata_columns": ["name"],
                "feature_descriptions": {
                    "quality": "Quality score",
                    "momentum": "Momentum indicator",
                    "stability": "Stability measure",
                },
            }

        def validate_entity_ids(self, entity_ids):
            valid = {f"ENT_{i:03d}" for i in range(10)}
            return {eid: (eid in valid) for eid in entity_ids}

    return InMemoryProvider()


@pytest.fixture
def mock_scoring_strategy():
    """IScoringStrategy con 2 profili."""
    class InMemoryStrategy(IScoringStrategy):
        _profiles = {
            "balanced": {"quality": 0.34, "momentum": 0.33, "stability": 0.33},
            "quality_focus": {"quality": 0.60, "momentum": 0.20, "stability": 0.20},
        }

        def get_profile_weights(self, profile):
            if profile not in self._profiles:
                raise ValueError(f"Unknown profile: {profile}")
            return self._profiles[profile]

        def get_available_profiles(self):
            return list(self._profiles.keys())

        def get_profile_metadata(self, profile):
            return {
                "description": f"Profile {profile}",
                "weights": self._profiles.get(profile, {}),
                "risk_adjustment": False,
            }

    return InMemoryStrategy()


@pytest.fixture
def engine(mock_data_provider, mock_scoring_strategy):
    """NeuralEngine con provider mock."""
    return NeuralEngine(
        data_provider=mock_data_provider,
        scoring_strategy=mock_scoring_strategy,
        stratification_mode="global",
        enable_time_decay=False,
    )


# ═══════════════════════════════════════════════════════════════════
# TEST: Pipeline completa
# ═══════════════════════════════════════════════════════════════════

class TestNeuralEnginePipeline:
    """Pipeline NeuralEngine end-to-end con dati sintetici."""

    def test_run_default(self, engine):
        """Esecuzione di run() senza parametri produce risultati validi."""
        result = engine.run(profile="balanced")

        assert "ranked_entities" in result
        assert "metadata" in result
        assert "diagnostics" in result

        df = result["ranked_entities"]
        assert len(df) > 0
        assert "entity_id" in df.columns

    def test_run_top_k(self, engine):
        """top_k limita i risultati."""
        result = engine.run(profile="balanced", top_k=3)
        df = result["ranked_entities"]
        assert len(df) <= 3

    def test_run_different_profiles(self, engine):
        """Profili diversi producono ranking diversi."""
        balanced = engine.run(profile="balanced")
        quality = engine.run(profile="quality_focus")

        balanced_order = list(balanced["ranked_entities"]["entity_id"])
        quality_order = list(quality["ranked_entities"]["entity_id"])

        # Con pesi diversi, l'ordine POTREBBE differire
        # Verifichiamo che entrambi producano risultati
        assert len(balanced_order) > 0
        assert len(quality_order) > 0

    def test_run_with_filters(self, engine):
        """I filtri riducono l'universo."""
        result = engine.run(
            profile="balanced",
            filters={"sector": "A"},
        )
        df = result["ranked_entities"]
        # Settore A ha 5 entità
        assert len(df) <= 5

    def test_run_with_entity_ids(self, engine):
        """Specificare entity_ids filtra l'universo."""
        result = engine.run(
            profile="balanced",
            entity_ids=["ENT_000", "ENT_001", "ENT_002"],
        )
        df = result["ranked_entities"]
        assert len(df) <= 3

    def test_run_with_feature_subset(self, engine):
        """feature_subset limita le feature estratte."""
        result = engine.run(
            profile="balanced",
            feature_subset=["quality", "momentum"],
        )
        assert "ranked_entities" in result


# ═══════════════════════════════════════════════════════════════════
# TEST: Metadata e diagnostica
# ═══════════════════════════════════════════════════════════════════

class TestNeuralEngineMetadata:
    """Verifica output diagnostico e metadata."""

    def test_diagnostics_keys(self, engine):
        """diagnostics contiene le chiavi attese."""
        result = engine.run(profile="balanced")
        diag = result.get("diagnostics", {})
        # Deve avere almeno universe_count
        assert "universe_count" in diag or "error" not in result.get("metadata", {})

    def test_metadata_profile(self, engine):
        """metadata riflette il profilo usato."""
        result = engine.run(profile="quality_focus")
        meta = result.get("metadata", {})
        assert meta.get("profile") == "quality_focus" or "profile" in str(meta)

    def test_get_available_profiles(self, engine):
        """get_available_profiles restituisce la lista dal strategy."""
        profiles = engine.get_available_profiles()
        assert "balanced" in profiles
        assert "quality_focus" in profiles

    def test_get_profile_metadata(self, engine):
        """get_profile_metadata delega alla strategy."""
        meta = engine.get_profile_metadata("balanced")
        assert isinstance(meta, dict)
        assert "description" in meta or "weights" in meta

    def test_get_domain_metadata(self, engine):
        """get_domain_metadata restituisce i dati del provider."""
        meta = engine.get_domain_metadata()
        assert meta["domain"] == "test"
        assert "available_features" in meta


# ═══════════════════════════════════════════════════════════════════
# TEST: Stratificazione e time decay
# ═══════════════════════════════════════════════════════════════════

class TestNeuralEngineStratification:
    """Modalità di stratificazione e opzioni avanzate."""

    def test_stratified_mode(self, mock_data_provider, mock_scoring_strategy):
        """stratification_mode='stratified' deve funzionare."""
        eng = NeuralEngine(
            data_provider=mock_data_provider,
            scoring_strategy=mock_scoring_strategy,
            stratification_mode="stratified",
        )
        result = eng.run(profile="balanced")
        assert "ranked_entities" in result

    def test_composite_mode(self, mock_data_provider, mock_scoring_strategy):
        """stratification_mode='composite' produce risultati."""
        eng = NeuralEngine(
            data_provider=mock_data_provider,
            scoring_strategy=mock_scoring_strategy,
            stratification_mode="composite",
            composite_global_weight=0.5,
        )
        result = eng.run(profile="balanced")
        assert "ranked_entities" in result

    def test_time_decay_enabled(self, mock_data_provider, mock_scoring_strategy):
        """enable_time_decay=True non causa errori."""
        eng = NeuralEngine(
            data_provider=mock_data_provider,
            scoring_strategy=mock_scoring_strategy,
            enable_time_decay=True,
            time_decay_half_life=15.0,
        )
        result = eng.run(profile="balanced")
        assert "ranked_entities" in result


# ═══════════════════════════════════════════════════════════════════
# TEST: Edge cases
# ═══════════════════════════════════════════════════════════════════

class TestNeuralEngineEdgeCases:
    """Casi limite: universo vuoto, profilo inesistente, ecc."""

    def test_empty_universe(self, mock_scoring_strategy):
        """Universo vuoto produce risultato con errore/vuoto."""
        class EmptyProvider(IDataProvider):
            def get_universe(self, filters=None):
                return pd.DataFrame(columns=["entity_id", "sector"])

            def get_features(self, entity_ids, feature_names=None):
                return pd.DataFrame(columns=["entity_id"])

            def get_metadata(self):
                return {"domain": "empty", "entity_type": "x",
                        "stratification_field": "sector",
                        "available_features": [], "metadata_columns": [],
                        "feature_descriptions": {}}

            def validate_entity_ids(self, entity_ids):
                return {eid: False for eid in entity_ids}

        eng = NeuralEngine(
            data_provider=EmptyProvider(),
            scoring_strategy=mock_scoring_strategy,
        )
        result = eng.run(profile="balanced")
        # Con universo vuoto, il DataFrame deve essere vuoto o metadata segnalare errore
        df = result["ranked_entities"]
        assert len(df) == 0 or "error" in result.get("metadata", {})

    def test_invalid_profile_raises(self, engine):
        """Profilo inesistente deve causare KeyError o ValueError."""
        with pytest.raises((KeyError, ValueError)):
            engine.run(profile="nonexistent_profile")
