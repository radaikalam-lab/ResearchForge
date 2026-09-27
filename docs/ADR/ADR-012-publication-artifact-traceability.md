# ADR-012: Publication Artifact Traceability

## Status
Accepted

## Context
Scientific manuscripts commonly suffer from untraceable citations, disconnected claims, and unreproducible figures/tables.

## Decision
All generated publication artifacts (Markdown, Quarto, LaTeX) must maintain explicit traceability back to underlying primary evidence fragments, statistical analyses, simulation seeds, and provenance hashes. Pre-export checks verify citation integrity and claim grounding.

## Consequences
- Every paragraph, claim, table, and figure in an exported manuscript is mathematically traceable to underlying computational evidence.
