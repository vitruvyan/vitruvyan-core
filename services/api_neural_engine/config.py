"""Neural Engine — Centralized Configuration"""
import os


PORT = int(os.getenv("PORT", "8003"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
