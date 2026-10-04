# Meeting notes — 2026-09-22

Attendees: Sulaiman, Priya, Marco.

## Decisions
1. Ship the packing tool as a standalone library first; CLI second.
2. Default strategy is head-tail: keeps the intro and the conclusion of
   long documents, which is where the signal usually is.
3. Token counts must be exact when tiktoken is installed; otherwise fall
   back to a chars/4 estimate and say so loudly in the report.

## Action items
- [ ] Benchmark packing strategies on the support-ticket dataset.
- [ ] Add a "recency" ordering mode for chat transcripts.
- [ ] Write the README with a Mermaid diagram (Sulaiman's quality bar).

## Open questions
- Should dropped documents be retried with a smaller per-doc budget
  before being dropped entirely? (Deferred to v0.2.)
