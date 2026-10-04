"""Packing strategies: how to shrink documents when the budget is tight."""

from __future__ import annotations

from typing import Callable, Dict, List

from .document import Document
from .tokenizer import TokenCounter

Strategy = Callable[[List[Document], TokenCounter, int], List[Document]]
"""A strategy maps (documents, counter, per-doc token budget) to shrunk documents."""


def truncate_strategy(
    docs: List[Document], counter: TokenCounter, per_doc_budget: int
) -> List[Document]:
    """Hard-truncate every document that exceeds the per-doc budget."""
    out = []
    for d in docs:
        text = d.text
        if counter.count(text) > per_doc_budget:
            text = counter.truncate(text, per_doc_budget)
        out.append(Document(d.id, text, d.priority, d.metadata))
    return out


def head_tail_strategy(
    docs: List[Document], counter: TokenCounter, per_doc_budget: int
) -> List[Document]:
    """Keep the head and tail of long documents (good for logs and transcripts)."""
    out = []
    for d in docs:
        text = d.text
        if counter.count(text) > per_doc_budget:
            text = counter.head_tail(text, per_doc_budget)
        out.append(Document(d.id, text, d.priority, d.metadata))
    return out


def proportional_strategy(
    docs: List[Document], counter: TokenCounter, per_doc_budget: int
) -> List[Document]:
    """Shrink each document proportionally to its size (fair-share)."""
    counts = [counter.count(d.text) for d in docs]
    total = sum(counts) or 1
    out = []
    for d, c in zip(docs, counts):
        share = max(1, int(per_doc_budget * len(docs) * (c / total)))
        text = d.text
        if c > share:
            text = counter.head_tail(text, share)
        out.append(Document(d.id, text, d.priority, d.metadata))
    return out


STRATEGIES: Dict[str, Strategy] = {
    "truncate": truncate_strategy,
    "head-tail": head_tail_strategy,
    "proportional": proportional_strategy,
}
