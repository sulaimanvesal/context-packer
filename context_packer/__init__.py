"""context-packer: fit documents into an LLM context window budget."""

from .document import Document
from .packer import ContextPacker, PackedContext, PackedDocument
from .strategies import STRATEGIES, Strategy
from .tokenizer import TokenCounter

__all__ = [
    "ContextPacker",
    "Document",
    "PackedContext",
    "PackedDocument",
    "STRATEGIES",
    "Strategy",
    "TokenCounter",
]
__version__ = "0.1.0"
