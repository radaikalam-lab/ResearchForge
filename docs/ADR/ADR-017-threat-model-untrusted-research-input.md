# ADR-017: Threat Model & Untrusted Research Input

## Status
Accepted

## Context
Ingested scholarly literature, PDFs, abstracts, and web-retrieved datasets might contain malicious prompt injections, shell commands, or attempts to manipulate execution policies.

## Decision
Establish the architectural invariant that all external scientific content is purely DATA, never instructions. Literature parsers, evidence extractors, and LLM providers have zero authority to escalate execution policies or grant capabilities.

## Consequences
- Protects computational sandbox and host system against prompt injection and malicious literature attacks.
