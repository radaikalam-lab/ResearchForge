"""Reasoning and AI/LLM provider protocol contract."""

from typing import Protocol, runtime_checkable

from researchforge.domain.models.evidence import Claim, EvidenceFragment
from researchforge.domain.models.hypothesis import Hypothesis


@runtime_checkable
class ReasoningProvider(Protocol):
    """Contract for LLMs and heuristic reasoning engines (strictly Tier 0 Proposal)."""

    provider_name: str

    async def propose(self, prompt: str, context_refs: list[str]) -> str:
        """Generate exploratory propositions, hypotheses, or summaries."""
        ...

    async def critique(self, hypothesis: Hypothesis, evidence: list[EvidenceFragment]) -> str:
        """Generate critical counter-arguments and identify unstated assumptions."""
        ...

    async def extract(self, raw_text: str, target_schema_name: str) -> dict[str, str]:
        """Extract structured JSON entities from raw literature text."""
        ...

    async def synthesize(self, claims: list[Claim]) -> str:
        """Synthesize multiple domain claims into an exploratory overview."""
        ...
