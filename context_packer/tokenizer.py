"""Token counting with tiktoken when available, heuristic fallback otherwise."""

from __future__ import annotations


class TokenCounter:
    """Counts tokens for a model encoding, falling back to a chars/4 heuristic.

    The fallback keeps the library usable in environments without tiktoken.
    It is clearly marked as approximate in every report.
    """

    FALLBACK_CHARS_PER_TOKEN = 4.0

    def __init__(self, model: str = "gpt-4o") -> None:
        self.model = model
        self.exact = False
        self._enc = None
        try:
            import tiktoken

            try:
                self._enc = tiktoken.encoding_for_model(model)
            except KeyError:
                self._enc = tiktoken.get_encoding("cl100k_base")
            self.exact = True
        except ImportError:
            self._enc = None

    def count(self, text: str) -> int:
        if self._enc is not None:
            return len(self._enc.encode(text))
        return max(1, round(len(text) / self.FALLBACK_CHARS_PER_TOKEN))

    def truncate(self, text: str, max_tokens: int) -> str:
        """Truncate text to at most max_tokens."""
        if max_tokens <= 0:
            return ""
        if self._enc is not None:
            ids = self._enc.encode(text)[:max_tokens]
            return self._enc.decode(ids)
        approx_chars = int(max_tokens * self.FALLBACK_CHARS_PER_TOKEN)
        return text[:approx_chars]

    def head_tail(self, text: str, max_tokens: int, head_ratio: float = 0.7) -> str:
        """Keep the head and tail of a long document, marking the cut."""
        if max_tokens <= 0:
            return ""
        if self.count(text) <= max_tokens:
            return text
        marker = "\n\n[... truncated middle ...]\n\n"
        marker_tokens = self.count(marker)
        body = max(1, max_tokens - marker_tokens)
        head_tokens = max(1, int(body * head_ratio))
        tail_tokens = max(0, body - head_tokens)
        head = self.truncate(text, head_tokens)
        tail = self._tail(text, tail_tokens)
        return head + marker + tail

    def _tail(self, text: str, max_tokens: int) -> str:
        if max_tokens <= 0:
            return ""
        if self._enc is not None:
            ids = self._enc.encode(text)[-max_tokens:]
            return self._enc.decode(ids)
        approx_chars = int(max_tokens * self.FALLBACK_CHARS_PER_TOKEN)
        return text[-approx_chars:]
