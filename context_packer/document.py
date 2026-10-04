"""Document model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Document:
    """A unit of content to pack into the context window.

    Attributes:
        id: stable identifier (used in reports).
        text: the document content.
        priority: higher values are kept first when the budget is tight
            (default 1.0).
        metadata: free-form info (source, recency score, etc.).
    """

    id: str
    text: str
    priority: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
