# ADR-003: Provider Architecture

## Status
Accepted

## Context
ResearchForge must interact with diverse external systems: literature databases (OpenAlex, Crossref), simulation drivers, statistics engines, vector stores, and LLMs. Hardcoding specific SDKs into domain entities violates clean architecture and hinders offline capability.

## Decision
Define all external capabilities as structural typing `Protocol` interfaces in `researchforge.domain.contracts`. All implementations reside in `researchforge.providers` and register through a central `ProviderRegistry`.

## Consequences
- 100% offline testing via mock providers.
- Providers can be upgraded or swapped with zero changes to domain models.
