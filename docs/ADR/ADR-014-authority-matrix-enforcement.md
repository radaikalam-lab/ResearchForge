# ADR-014: Authority Matrix Enforcement

## Status
Accepted

## Context
Epistemic boundaries must not rely on passive documentation. Without programmatic enforcement at the transition layer, unauthorized transitions could occur.

## Decision
Implement `TransitionEngine` which validates the acting `EpistemicTier`, checks executable guards, and verifies required artifacts before executing state mutations.

## Consequences
- Transitions to `ACCEPTED` or `CONCLUSION_ACCEPTED` strictly fail without Tier 3 Human Authority.
