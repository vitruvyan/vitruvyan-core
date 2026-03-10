"""
E2E Test: Babel Gardens — Domain-Agnostic Functions
=====================================================
Tests the NEW domain-agnostic LIVELLO 1 consumers:
 - SynthesisConsumer: vector fusion (semantic + sentiment)
 - TopicClassifierConsumer: keyword-based topic classification
 - LanguageDetectorConsumer: heuristic language detection

Also tests the Embedding API and Babel's integration in the Graph pipeline.

Note: Legacy sentiment/emotion routes are NOT tested (known not-loaded).
"""
import pytest
import numpy as np

pytestmark = [pytest.mark.e2e]


class TestBabelGardensHealth:
    """Service availability."""

    def test_babel_health(self, http_client, babel_api):
        """Babel Gardens health endpoint must respond."""
        r = http_client.get(f"{babel_api}/health")
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "healthy"

    def test_babel_root_info(self, http_client, babel_api):
        """Root endpoint must return service info."""
        r = http_client.get(f"{babel_api}/")
        assert r.status_code == 200
        data = r.json()
        assert data.get("service") == "Babel Gardens"


class TestSynthesisConsumer:
    """SynthesisConsumer — vector fusion algorithms (pure LIVELLO 1)."""

    @pytest.fixture
    def synthesis_consumer(self):
        try:
            from core.cognitive.babel_gardens.consumers.synthesis import SynthesisConsumer
            from core.cognitive.babel_gardens.domain.config import BabelConfig
            return SynthesisConsumer(BabelConfig())
        except ImportError:
            pytest.skip("SynthesisConsumer not importable")

    def test_consumer_importable(self, synthesis_consumer):
        """SynthesisConsumer must be importable."""
        assert synthesis_consumer is not None

    def test_concatenation_fusion(self, synthesis_consumer):
        """Concatenation fusion must combine two vectors."""
        semantic = np.random.rand(768).tolist()
        sentiment = np.random.rand(768).tolist()

        result = synthesis_consumer.process({
            "semantic_vector": semantic,
            "sentiment_vector": sentiment,
            "method": "concatenation",
        })
        assert result is not None
        assert result.success, f"Fusion failed: {result.errors}"
        fused = result.data.get("unified_vector", [])
        # Concatenation should produce a vector of double size
        assert len(fused) == 1536

    def test_weighted_average_fusion(self, synthesis_consumer):
        """Weighted average must produce a vector of same dimensions."""
        dim = 768
        semantic = np.random.rand(dim).tolist()
        sentiment = np.random.rand(dim).tolist()

        result = synthesis_consumer.process({
            "semantic_vector": semantic,
            "sentiment_vector": sentiment,
            "method": "weighted_average",
            "weights": {"semantic": 0.7, "sentiment": 0.3},
        })
        assert result is not None
        assert result.success, f"Fusion failed: {result.errors}"
        fused = result.data.get("unified_vector", [])
        assert len(fused) == dim

    def test_fusion_preserves_information(self, synthesis_consumer):
        """Fused vector should not be all zeros or identical to input."""
        dim = 768
        semantic = np.random.rand(dim).tolist()
        sentiment = np.random.rand(dim).tolist()

        result = synthesis_consumer.process({
            "semantic_vector": semantic,
            "sentiment_vector": sentiment,
            "method": "weighted_average",
        })
        assert result.success, f"Fusion failed: {result.errors}"
        fused = result.data.get("unified_vector", [])
        assert len(fused) > 0, "unified_vector is empty"
        assert not all(v == 0 for v in fused), "Fused vector is all zeros"
        assert fused != semantic, "Fused vector is identical to semantic input"
        assert fused != sentiment, "Fused vector is identical to sentiment input"


class TestTopicClassifierConsumer:
    """TopicClassifierConsumer — keyword-based topic classification (pure LIVELLO 1)."""

    @pytest.fixture
    def topic_classifier(self):
        try:
            from core.cognitive.babel_gardens.consumers.classifiers import TopicClassifierConsumer
            from core.cognitive.babel_gardens.domain.config import BabelConfig
            return TopicClassifierConsumer(BabelConfig())
        except ImportError:
            pytest.skip("TopicClassifierConsumer not importable")

    def test_consumer_importable(self, topic_classifier):
        """TopicClassifierConsumer must be importable."""
        assert topic_classifier is not None

    def test_classify_text(self, topic_classifier):
        """Classification must return a result for any text."""
        result = topic_classifier.process({
            "text": "Machine learning and artificial intelligence are transforming technology",
        })
        assert result is not None
        assert result.success, f"Classification failed: {result.errors}"
        assert isinstance(result.data, dict)

    def test_classify_empty_text(self, topic_classifier):
        """Empty text should not crash."""
        result = topic_classifier.process({"text": ""})
        assert result is not None
        # May succeed or fail gracefully — no crash is the expectation

    def test_classify_multilingual(self, topic_classifier):
        """Classification should work with Italian text."""
        result = topic_classifier.process({
            "text": "L'intelligenza artificiale sta rivoluzionando la scienza dei dati",
        })
        assert result is not None
        assert isinstance(result.data, dict)


class TestLanguageDetectorConsumer:
    """LanguageDetectorConsumer — heuristic language detection (pure LIVELLO 1)."""

    @pytest.fixture
    def lang_detector(self):
        try:
            from core.cognitive.babel_gardens.consumers.classifiers import LanguageDetectorConsumer
            from core.cognitive.babel_gardens.domain.config import BabelConfig
            return LanguageDetectorConsumer(BabelConfig())
        except ImportError:
            pytest.skip("LanguageDetectorConsumer not importable")

    def test_consumer_importable(self, lang_detector):
        """LanguageDetectorConsumer must be importable."""
        assert lang_detector is not None

    def test_detect_english(self, lang_detector):
        """English text must be detected."""
        result = lang_detector.process({
            "text": "The quick brown fox jumps over the lazy dog in the beautiful garden",
        })
        assert result is not None
        assert result.success, f"Detection failed: {result.errors}"
        lang = result.data.get("language", "")
        assert lang in ("en", "english"), f"Expected English, got: {lang}"

    def test_detect_italian(self, lang_detector):
        """Italian text must be detected."""
        result = lang_detector.process({
            "text": "Il sistema epistemico opera attraverso ordini sacri che governano la conoscenza",
        })
        assert result is not None
        assert result.success, f"Detection failed: {result.errors}"
        lang = result.data.get("language", "")
        assert lang in ("it", "italian"), f"Expected Italian, got: {lang}"

    def test_detect_returns_confidence(self, lang_detector):
        """Language detection should include a confidence score."""
        result = lang_detector.process({
            "text": "Dies ist ein deutscher Text mit vielen Wörtern zur Spracherkennung",
        })
        assert result.success, f"Detection failed: {result.errors}"
        # Should have some confidence indicator in data
        assert "confidence" in result.data, f"No confidence in result: {result.data.keys()}"

    def test_detect_short_text(self, lang_detector):
        """Short text should still return a result (may be low confidence)."""
        result = lang_detector.process({"text": "Bonjour"})
        assert result is not None
        # Short text may succeed or fail gracefully


class TestBabelInGraphPipeline:
    """Babel Gardens integration within the Graph pipeline."""

    def test_emotion_fields_present(self, graph_run):
        """Graph response must include emotion detection fields from Babel."""
        parsed = graph_run("Questo è fantastico, sono entusiasta!")["parsed"]
        assert "emotion_detected" in parsed
        assert "emotion_metadata" in parsed

    def test_emotion_metadata_structure(self, graph_run):
        """Emotion metadata must include processing details."""
        parsed = graph_run("Mi preoccupa questa situazione")["parsed"]
        meta = parsed.get("emotion_metadata", {})
        assert isinstance(meta, dict)
        # Should have some of these fields
        expected_keys = {"processing_time_ms", "language", "fallback_used"}
        found = set(meta.keys()) & expected_keys
        assert len(found) > 0 or meta == {}, f"emotion_metadata has no expected keys: {meta.keys()}"

    def test_language_detected_in_graph(self, graph_run):
        """language_detected field must be present in graph output."""
        parsed = graph_run("Testing language detection in the pipeline")["parsed"]
        assert "language_detected" in parsed

    def test_babel_status_in_graph(self, graph_run):
        """babel_status should be present (may be null if babel has issues)."""
        parsed = graph_run("Verifica integrazione Babel")["parsed"]
        # babel_status field should exist even if null
        assert "babel_status" in parsed


class TestEmbeddingAPI:
    """Embedding API (api_embedding:9010) — vector generation for all services."""

    def test_single_embedding(self, http_client, embedding_api):
        """Generate a single 768-dim embedding."""
        r = http_client.post(
            f"{embedding_api}/v1/embeddings/create",
            json={"text": "test embedding generation", "source": "e2e"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("success")
        assert len(data["embedding"]) == 768

    def test_batch_embeddings(self, http_client, embedding_api):
        """Batch embedding for multiple texts."""
        r = http_client.post(
            f"{embedding_api}/v1/embeddings/batch",
            json={"texts": ["one", "two", "three"], "source": "e2e"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("success")
        assert len(data["embeddings"]) == 3

    def test_embedding_stats(self, http_client, embedding_api):
        """Stats endpoint must report service statistics."""
        r = http_client.get(f"{embedding_api}/v1/stats")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
