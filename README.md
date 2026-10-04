# context-packer

Pack documents into an LLM context-window budget — without overflowing it and without silently losing content.

Retrieval pipelines usually do one of two bad things: concatenate everything and blow past the window (API error), or hard-truncate the tail (quietly dropping the chunk that might have mattered most). `context-packer` selects documents by priority, shrinks the oversized ones with a pluggable strategy, reserves room for the system prompt and the reply, and reports exactly what fit, what was shrunk, and what was dropped.

No API keys needed — everything runs locally.

## Install

```bash
pip install -r requirements.txt
```

`tiktoken` gives exact token counts. If it isn't installed, a chars÷4 estimate is used instead and every report says so.

## Quick start

```python
from context_packer import ContextPacker, Document

docs = [
    Document("architecture.md", open("architecture.md").read(), priority=3.0),
    Document("server-log.txt", open("server-log.txt").read(), priority=1.0),
]

packer = ContextPacker(
    budget=8000,
    strategy="head-tail",   # or "truncate", "proportional"
    reserve=1000,           # system prompt
    output_reserve=2000,    # room for the reply
)
packed = packer.pack(docs)

print(packed.render())   # prompt-ready string, <= budget tokens
print(packer.report(packed))  # markdown: what fit / shrank / dropped
```

## CLI

```bash
python -m context_packer.cli --budget 8000 --strategy head-tail \
    --reserve 1000 --output-reserve 2000 --report \
    --priority architecture.md:3.0 \
    -o packed.txt docs/*.md
```

## Strategies

| Strategy | Behavior | Best for |
|----------|----------|----------|
| `truncate` | Hard cut at the budget | Fixed-format records |
| `head-tail` *(default)* | Keep the head and tail, mark the cut | Logs, transcripts, long docs |
| `proportional` | Shrink every doc fair-share by size | Mixed batches, no priorities |

Selection is greedy by priority: highest-priority documents are placed first, then oversized leftovers are shrunk to fit the remaining budget. Anything that still doesn't fit is dropped — and named in the report.

## Architecture

```mermaid
flowchart LR
    D[Documents<br/>id, text, priority] --> P[ContextPacker]
    P --> C{TokenCounter<br/>tiktoken / fallback}
    C -->|counts| S{Strategy<br/>truncate · head-tail · proportional}
    S -->|shrunk docs| G[Greedy selection<br/>priority order, budget check]
    G --> O[PackedContext<br/>render() → prompt string]
    G --> R[report()<br/>fit · shrunk · dropped]
    P -.->|reserve| B[(Budget<br/>system + output<br/>reserved first)]
```

## Demo

```bash
python demo.py
```

Packs the sample files in `examples/` (an architecture doc, meeting notes, and a 400-line server log) into a 600-token budget and prints the packing report. Zero API keys, runs offline.

## Tests

```bash
pytest tests/ -q
```

## License

MIT — see [LICENSE](LICENSE).
