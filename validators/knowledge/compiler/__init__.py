"""Deterministic source-to-IR compiler frontend."""

from .ir import CompilerIR, DiagnosticIR, EdgeIR, SymbolIR
from .pydantic_compiler import augment_parsed_files as augment_pydantic_files
from .fastapi_compiler import augment_parsed_files as augment_fastapi_files
from .sqlalchemy_compiler import augment_parsed_files as augment_sqlalchemy_files
from .django_compiler import augment_parsed_files as augment_django_files
from .celery_compiler import augment_parsed_files as augment_celery_files
from .alembic_compiler import augment_parsed_files as augment_alembic_files
from .resolve import compile_project

__all__ = [
    'CompilerIR',
    'DiagnosticIR',
    'EdgeIR',
    'SymbolIR',
    'augment_fastapi_files',
    'augment_django_files',
    'augment_pydantic_files',
    'augment_sqlalchemy_files',
    'augment_celery_files',
    'augment_alembic_files',
    'compile_project',
]
