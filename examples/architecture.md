# Context Packer — architecture

We are building a RAG assistant that answers questions about this project.

## Components
- The retriever fetches candidate chunks from the vector store.
- The reranker scores them for relevance to the user query.
- The packer (this tool) selects chunks that fit the context window.
- The LLM receives the packed prompt and generates an answer.

## Token budget policy
- Total window: 128k tokens (gpt-4o class).
- System prompt: 1k tokens reserved.
- Output: 2k tokens reserved for the reply.
- Retrieval candidates: up to 20 chunks, ~800 tokens each.

## Why packing matters
Naive concatenation either overflows the window (API error) or silently
truncates the tail (loses the most relevant chunk if it was last). A packer
with priorities and head-tail shrinking keeps the important content and
reports exactly what was dropped, so the pipeline is observable.
