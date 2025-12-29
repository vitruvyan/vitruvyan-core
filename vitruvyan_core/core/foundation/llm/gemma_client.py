import os
import requests
from typing import Any, Dict

# In container vitruvyan_api usa il service name docker; fuori, usa localhost
DEFAULT_BASE = os.getenv("GEMMA_BASE_URL", "http://vitruvyan_api_gemma:8007")

def gemma_predict(
    text: str,
    timeout: float = 90.0,
) -> Dict[str, Any]:
    """
    Chiama l’endpoint Gemma /predict e ritorna il JSON.
    Non solleva: in caso di errore ritorna un dict con 'error'.
    """
    url = f"{DEFAULT_BASE}/predict"
    payload = {"text": text}

    try:
        r = requests.post(url, json=payload, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"intent": "unknown", "error": str(e), "payload": payload, "base_url": DEFAULT_BASE}
