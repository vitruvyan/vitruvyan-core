"""Neural Engine — Centralized Configuration"""
import os


PORT = int(os.getenv("PORT", "8003"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DOMAIN = os.getenv("DOMAIN", "mock").strip().lower()
NE_CACHE_TTL_SECONDS = int(os.getenv("NE_CACHE_TTL_SECONDS", "30"))

_RAW_STRATIFICATION = os.getenv("NE_STRATIFICATION_MODE", "global").strip().lower()
if _RAW_STRATIFICATION == "sector":
    _RAW_STRATIFICATION = "stratified"
DEFAULT_STRATIFICATION_MODE = (
    _RAW_STRATIFICATION
    if _RAW_STRATIFICATION in {"global", "stratified", "composite"}
    else "global"
)

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
