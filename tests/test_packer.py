"""Tests for context-packer."""

import pytest

from context_packer import ContextPacker, Document, TokenCounter
from context_packer.strategies import STRATEGIES


def make_docs():
    return [
        Document("a.md", "hello world " * 50, priority=3.0),
        Document("b.md", "lorem ipsum " * 200, priority=1.0),
        Document("c.md", "tiny", priority=2.0),
    ]


def test_everything_fits_when_budget_is_huge():
    packer = ContextPacker(budget=100_000)
    packed = packer.pack(make_docs())
    assert packed.dropped == []
    assert len(packed.documents) == 3
    assert packed.utilization < 1.0


def test_low_priority_doc_dropped_first():
    packer = ContextPacker(budget=120, strategy="truncate")
    packed = packer.pack(make_docs())
    # c.md (tiny, priority 2) and part of a.md must survive; b.md (priority 1) goes
    ids = [d.id for d in packed.documents]
    assert "c.md" in ids
    assert "b.md" in packed.dropped or "b.md" not in ids
    assert packed.total_tokens <= 120


def test_never_exceeds_budget():
    packer = ContextPacker(budget=500, strategy="head-tail", reserve=50, output_reserve=100)
    packed = packer.pack(make_docs())
    assert packed.total_tokens <= packer.usable_budget
    assert packer.usable_budget == 350


def test_head_tail_keeps_both_ends():
    counter = TokenCounter()
    text = "START " + ("middle " * 2000) + " END"
    shrunk = counter.head_tail(text, 40)
    assert "START" in shrunk
    assert "END" in shrunk
    assert "truncated middle" in shrunk


def test_all_strategies_shrink():
    long_doc = [Document("x.md", "word " * 5000, priority=1.0)]
    for name in STRATEGIES:
        packer = ContextPacker(budget=200, strategy=name)
        packed = packer.pack(long_doc)
        assert packed.total_tokens <= 200, name
        assert len(packed.documents) == 1, name


def test_unknown_strategy_rejected():
    with pytest.raises(ValueError):
        ContextPacker(budget=100, strategy="nope")


def test_bad_budget_rejected():
    with pytest.raises(ValueError):
        ContextPacker(budget=0)


def test_render_joins_documents():
    packer = ContextPacker(budget=100_000)
    packed = packer.pack(make_docs())
    rendered = packed.render()
    assert "tiny" in rendered
    assert "hello world" in rendered


def test_report_lists_dropped():
    packer = ContextPacker(budget=60, strategy="truncate")
    packed = packer.pack(make_docs())
    report = packer.report(packed)
    assert "## Dropped" in report
    assert "## Included" in report
    for doc_id in packed.dropped:
        assert doc_id in report


def test_fallback_counter_approximates():
    counter = TokenCounter.__new__(TokenCounter)
    counter.exact = False
    counter._enc = None
    assert counter.count("a" * 400) == 100
    assert counter.truncate("a" * 400, 50) == "a" * 200
