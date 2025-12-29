import logging
from datetime import datetime
import os

# Configura logger
logger = logging.getLogger("strategic_logger")
logger.setLevel(logging.INFO)

# Crea handler (es. file o console)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Funzione principale per registrare la conversazione strategica
def log_strategic_conversation(user_id: str, user_input: str, llm_response: str, ticker: str = None, context_tag: str = "portfolio"):
    try:
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "user_id": user_id,
            "ticker": ticker,
            "context": context_tag,
            "user_input": user_input,
            "llm_response": llm_response
        }

        # Log su console (o file in futuro)
        logger.info(f"[Strategic Log] {log_entry}")

        # TODO: Salva anche su file JSON, DB o altro se necessario
        # con open("strategic_logs.json", "a") as f:
        #     f.write(json.dumps(log_entry) + "\n")

    except Exception as e:
        logger.warning(f"Errore durante log_strategic_conversation: {e}")