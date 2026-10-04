"""The packer: select and shrink documents to fit a token budget."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .document import Document
from .strategies import STRATEGIES
from .tokenizer import TokenCounter


@dataclass
class PackedDocument:
    id: str
    text: str
    tokens: int
    priority: float
    truncated: bool


@dataclass
class PackedContext:
    documents: List[PackedDocument]
    dropped: List[str]
    total_tokens: int
    budget: int
    exact_tokens: bool

    @property
    def utilization(self) -> float:
        return self.total_tokens / self.budget if self.budget else 0.0

    def render(self, separator: str = "\n\n---\n\n") -> str:
        """Render the packed documents as a single prompt-ready string."""
        return separator.join(d.text for d in self.documents)


class ContextPacker:
    """Pack documents into an LLM context window.

    Args:
        budget: total token budget for the packed documents.
        strategy: one of "truncate", "head-tail", "proportional".
        model: model name used for tiktoken encoding.
        reserve: tokens reserved for the system prompt (subtracted from budget).
        output_reserve: tokens reserved for the model's reply.
        counter: optional pre-built TokenCounter.
    """

    def __init__(
        self,
        budget: int,
        strategy: str = "head-tail",
        model: str = "gpt-4o",
        reserve: int = 0,
        output_reserve: int = 0,
        counter: Optional[TokenCounter] = None,
    ) -> None:
        if strategy not in STRATEGIES:
            raise ValueError(f"unknown strategy {strategy!r}; choose from {sorted(STRATEGIES)}")
        if budget <= 0:
            raise ValueError("budget must be positive")
        self.budget = budget
        self.strategy = STRATEGIES[strategy]
        self.strategy_name = strategy
        self.counter = counter or TokenCounter(model)
        self.reserve = reserve
        self.output_reserve = output_reserve

    @property
    def usable_budget(self) -> int:
        return max(0, self.budget - self.reserve - self.output_reserve)

    def pack(self, documents: List[Document]) -> PackedContext:
        usable = self.usable_budget
        # Highest priority first; stable order breaks ties.
        ordered = sorted(documents, key=lambda d: d.priority, reverse=True)

        # Greedy selection: keep adding docs (in priority order) that fit,
        # then shrink the oversized leftovers with the strategy if they can
        # contribute at least a minimal chunk.
        counts = {d.id: self.counter.count(d.text) for d in ordered}
        selected: List[Document] = []
        dropped: List[str] = []
        used = 0
        for d in ordered:
            c = counts[d.id]
            if used + c <= usable:
                selected.append(d)
                used += c
            else:
                remaining = usable - used
                if remaining >= 32 and c > remaining:
                    shrunk = self.strategy([d], self.counter, remaining)
                    s = shrunk[0]
                    sc = self.counter.count(s.text)
                    if sc <= remaining:
                        selected.append(s)
                        used += sc
                    else:
                        dropped.append(d.id)
                else:
                    dropped.append(d.id)

        packed: List[PackedDocument] = []
        total = 0
        for d in selected:
            tokens = self.counter.count(d.text)
            total += tokens
            packed.append(
                PackedDocument(
                    id=d.id,
                    text=d.text,
                    tokens=tokens,
                    priority=d.priority,
                    truncated=tokens < counts[d.id],
                )
            )

        return PackedContext(
            documents=packed,
            dropped=dropped,
            total_tokens=total,
            budget=self.budget,
            exact_tokens=self.counter.exact,
        )

    def report(self, packed: PackedContext) -> str:
        """Human-readable markdown report of the packing result."""
        lines = [
            "# Context packing report",
            "",
            f"- Budget: **{packed.budget}** tokens "
            f"(usable {self.usable_budget} after {self.reserve + self.output_reserve} reserved)",
            f"- Used: **{packed.total_tokens}** tokens "
            f"({packed.utilization:.1%} of budget)",
            f"- Strategy: `{self.strategy_name}`",
            f"- Token counts: {'exact (tiktoken)' if packed.exact_tokens else 'approximate (chars/4 fallback)'}",
            "",
            "## Included",
            "",
            "| document | tokens | priority | truncated |",
            "|----------|--------|----------|-----------|",
        ]
        for d in packed.documents:
            lines.append(
                f"| `{d.id}` | {d.tokens} | {d.priority:g} | "
                f"{'yes' if d.truncated else 'no'} |"
            )
        lines += ["", "## Dropped", ""]
        if packed.dropped:
            for doc_id in packed.dropped:
                lines.append(f"- `{doc_id}` (did not fit)")
        else:
            lines.append("None — everything fit.")
        return "\n".join(lines) + "\n"
