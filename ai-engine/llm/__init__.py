"""
LLM Module
Language Model işlemleri için modüller
"""

from .function_calling import FunctionCallingEngine, function_engine
from .slot_filling import SlotFillingEngine, slot_engine

__all__ = [
    "FunctionCallingEngine", 
    "function_engine",
    "SlotFillingEngine",
    "slot_engine"
]
