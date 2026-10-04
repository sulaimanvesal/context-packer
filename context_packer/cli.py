"""CLI: pack text files into a token budget."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .document import Document
from .packer import ContextPacker
from .strategies import STRATEGIES


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="context-packer",
        description="Pack text documents into an LLM context-window token budget.",
    )
    p.add_argument("files", nargs="+", help="text files to pack")
    p.add_argument("--budget", type=int, required=True, help="total token budget")
    p.add_argument(
        "--strategy",
        choices=sorted(STRATEGIES),
        default="head-tail",
        help="how to shrink oversized documents (default: head-tail)",
    )
    p.add_argument("--model", default="gpt-4o", help="model for token counting")
    p.add_argument("--reserve", type=int, default=0, help="tokens reserved for system prompt")
    p.add_argument(
        "--output-reserve", type=int, default=0, help="tokens reserved for the reply"
    )
    p.add_argument(
        "--priority",
        action="append",
        default=[],
        metavar="FILE:PRIORITY",
        help="per-file priority, e.g. --priority notes.txt:2.0 (repeatable)",
    )
    p.add_argument("--report", action="store_true", help="print a markdown report")
    p.add_argument("-o", "--output", help="write packed text to this file")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    priorities = {}
    for item in args.priority:
        try:
            name, value = item.rsplit(":", 1)
            priorities[name] = float(value)
        except ValueError:
            print(f"error: bad --priority value {item!r}, expected FILE:NUMBER", file=sys.stderr)
            return 2

    documents = []
    for raw in args.files:
        path = Path(raw)
        if not path.is_file():
            print(f"error: not a file: {raw}", file=sys.stderr)
            return 2
        documents.append(
            Document(
                id=path.name,
                text=path.read_text(encoding="utf-8", errors="replace"),
                priority=priorities.get(path.name, priorities.get(raw, 1.0)),
            )
        )

    packer = ContextPacker(
        budget=args.budget,
        strategy=args.strategy,
        model=args.model,
        reserve=args.reserve,
        output_reserve=args.output_reserve,
    )
    packed = packer.pack(documents)

    if args.report or not args.output:
        print(packer.report(packed))
    if args.output:
        Path(args.output).write_text(packed.render(), encoding="utf-8")
        print(f"wrote {args.output} ({packed.total_tokens} tokens)")
    if packed.dropped:
        print(f"warning: dropped {len(packed.dropped)} document(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
