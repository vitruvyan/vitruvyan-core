# core/logic/vitruvyan_proprietary/vee/__init__.py
"""
🧠 Vitruvyan Explainability Engine 2.0 (VEE 2.0)

Sistema multilivello di ragionamento e spiegazione per analisi finanziarie.
Trasforma dati tecnici in spiegazioni stratificate, chiare e auditabili.

Moduli:
- vee_analyzer: Analisi KPI e identificazione pattern
- vee_generator: Generazione spiegazioni multilivello
- vee_memory_adapter: Recupero memoria storica
- vee_engine: Orchestratore principale (aggiornato)
"""

from .vee_analyzer import analyze_kpi, AnalysisResult
from .vee_generator import generate_explanation, ExplanationLevels
from .vee_memory_adapter import retrieve_similar_explanations, store_explanation
from .vee_engine import explain_entity, VEEEngine

__all__ = [
    'analyze_kpi',
    'AnalysisResult', 
    'generate_explanation',
    'ExplanationLevels',
    'retrieve_similar_explanations',
    'store_explanation',
    'explain_entity',
    'VEEEngine'
]

__version__ = "2.0.0"
__author__ = "Vitruvyan AI Team"