"""Runnable demo: pack sample documents into a 600-token budget. No API keys needed."""

from pathlib import Path

from context_packer import ContextPacker, Document

EXAMPLES = Path(__file__).parent / "examples"


def load_examples() -> list[Document]:
    docs = []
    priorities = {"architecture.md": 3.0, "meeting-notes.md": 2.0, "server-log.txt": 1.0}
    for path in sorted(EXAMPLES.glob("*")):
        docs.append(
            Document(
                id=path.name,
                text=path.read_text(encoding="utf-8"),
                priority=priorities.get(path.name, 1.0),
            )
        )
    return docs


def main() -> None:
    docs = load_examples()
    packer = ContextPacker(
        budget=600,
        strategy="head-tail",
        reserve=100,          # system prompt
        output_reserve=200,   # room for the reply
    )
    packed = packer.pack(docs)
    print(packer.report(packed))
    print("Packed prompt preview (first 400 chars):")
    print(packed.render()[:400] + "...")


if __name__ == "__main__":
    main()
