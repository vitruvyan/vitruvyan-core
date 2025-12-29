# core/leo/import_seed_dataset.py
"""
Seed Dataset Importer for Conversations Embeddings
--------------------------------------------------

This script loads a JSON dataset of synthetic conversation phrases
(e.g. greetings, portfolio questions, clarifications) and inserts them
directly into Qdrant under the collection `conversations_embeddings`.

Why?
- Real user conversations are logged in PostgreSQL (table `conversations`)
  and embedded in real-time.
- Synthetic seed datasets (multilingual, intent-focused) should NOT pollute
  the production `conversations` table.
- Instead, we enrich the semantic memory by inserting them directly into Qdrant.

How it works:
1. Load a JSON file containing a list of objects with at least:
   - phrase_text (str)
   - language (str: it/en/es)
   - context_type (str)
   - tone (str)
   - source (str)
2. Compute embeddings with SentenceTransformers (all-MiniLM-L6-v2).
3. Upsert each phrase as a new point in Qdrant, with a UUID as ID.
4. Payload stored in Qdrant contains all metadata, so the dataset
   remains auditable.

Usage:
    python3 core/leo/import_seed_dataset.py --file conversations_seed.json
"""

import os
import uuid
import json
import argparse
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

# Load environment variables
load_dotenv()

# Embedding model
MODEL_NAME = "all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)

# Qdrant client
QDRANT_HOST = os.getenv("QDRANT_HOST", "vitruvyan_qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
COLLECTION = "conversations_embeddings"
VECTOR_SIZE = model.get_sentence_embedding_dimension()


def ensure_collection():
    """Ensure the conversations_embeddings collection exists in Qdrant."""
    collections = [c.name for c in qdrant.get_collections().collections]
    if COLLECTION not in collections:
        print(f"🛠 Creating collection '{COLLECTION}' in Qdrant...")
        from qdrant_client.http.models import VectorParams, Distance
        qdrant.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )


def import_seed_dataset(file_path: str):
    """Load a JSON dataset and upsert phrases into Qdrant."""
    ensure_collection()

    with open(file_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    if not isinstance(dataset, list):
        raise ValueError("Dataset must be a list of JSON objects")

    points = []
    for item in dataset:
        text = item.get("phrase_text")
        if not text:
            continue

        vector = model.encode(text).tolist()
        qid = str(uuid.uuid4())

        payload = {
            "phrase_text": text,
            "language": item.get("language", "en"),
            "context_type": item.get("context_type", "unknown"),
            "tone": item.get("tone", "neutral"),
            "source": item.get("source", "seed_dataset"),
            "seed": True,  # extra flag to identify synthetic data
        }

        points.append({"id": qid, "vector": vector, "payload": payload})

    if points:
        qdrant.upsert(collection_name=COLLECTION, points=points)
        print(f"✅ Imported {len(points)} seed phrases into '{COLLECTION}'")
    else:
        print("⚠️ No valid phrases found in dataset.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import seed dataset into conversations_embeddings")
    parser.add_argument("--file", required=True, help="Path to the JSON dataset file")
    args = parser.parse_args()

    import_seed_dataset(args.file)
