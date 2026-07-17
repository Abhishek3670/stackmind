"""Deterministic source-to-IR compiler frontend."""

from .ir import CompilerIR, DiagnosticIR, EdgeIR, SymbolIR
from .resolve import compile_project

__all__ = [
    "CompilerIR",
    "DiagnosticIR",
    "EdgeIR",
    "SymbolIR",
    "compile_project",
]
