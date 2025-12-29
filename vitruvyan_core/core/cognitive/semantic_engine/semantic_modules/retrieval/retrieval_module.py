# core/logic/semantic_modules/retrieval/retrieval_module.py

import os
import argparse
from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

# ✅ Config
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = "phrases_embeddings"
MODEL_NAME = "all-MiniLM-L6-v2"

# ✅ Init Qdrant client + embedding model
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, prefer_grpc=False)
model = SentenceTransformer(MODEL_NAME)


def find_similar_phrases(query: str, language: str = "en", top_k: int = 5) -> List[Dict]:
    """
    Cerca frasi semanticamente simili in Qdrant per una lingua specifica.
    Ritorna: [{"text": ..., "score": ..., "source": ...}, ...]
    """
    try:
        query_vector = model.encode(query).tolist()

        search_filter = Filter(
            must=[FieldCondition(key="language", match=MatchValue(value=language))]
        )

        results = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=search_filter,
            limit=top_k,
            with_payload=True,
        )

        matches = []
        for r in results:
            matches.append({
                "text": r.payload.get("phrase_text", "N/A"),
                "score": round(r.score, 4),
                "source": r.payload.get("source", "unknown")
            })

        return matches

    except Exception as e:
        print(f"❌ Errore in find_similar_phrases: {e}")
        return []


# ✅ CLI
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="🔎 Modulo di retrieval semantico (Vitruvyan)")
    parser.add_argument("--query", type=str, required=True, help="Testo della query")
    parser.add_argument("--language", type=str, default="en", help="Lingua (en, it, es)")
    parser.add_argument("--top-k", type=int, default=5, help="Numero di risultati da mostrare")

    args = parser.parse_args()

    print(f"\n🚀 Query: {args.query} (lang={args.language}, top_k={args.top_k})")

    matches = find_similar_phrases(args.query, args.language, args.top_k)

    if not matches:
        print("⚠️ Nessun risultato trovato.")
    else:
        for m in matches:
            print(f"\n🔎 Score: {m['score']} | Fonte: {m['source']}\n   Testo: {m['text']}")
