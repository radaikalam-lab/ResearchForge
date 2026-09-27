# ADR-010: AI/LLM Authority Boundary

## Status
Accepted

## Context
LLMs frequently exhibit overconfidence, hallucinations, and sycophantic behavior. Granting LLMs authority to declare scientific truths or approve transitions leads to corrupted scientific records.

## Decision
LLM reasoning is treated as an unverified proposal mechanism (Tier 0). Every LLM assertion must carry model ID, prompt hash, and output hash. No LLM output can directly approve a hypothesis or conclude a research finding.

## Consequences
- AI acts purely as an assistive synthesizer, preserving rigorous human validation.
