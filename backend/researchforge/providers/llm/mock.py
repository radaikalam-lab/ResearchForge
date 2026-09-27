"""Mock reasoning / LLM provider."""

from researchforge.domain.contracts.reasoning import ReasoningProvider
from researchforge.domain.models.evidence import Claim, EvidenceFragment
from researchforge.domain.models.hypothesis import Hypothesis


class MockReasoningProvider(ReasoningProvider):
    """Mock implementation of ReasoningProvider (strictly Tier 0)."""

    provider_name: str = "mock-reasoning-llm-v1"

    async def propose(self, prompt: str, context_refs: list[str]) -> str:
        """Propose exploratory idea."""
        return f"Proposed scientific hypothesis regarding '{prompt}' with context {context_refs}."

    async def critique(self, hypothesis: Hypothesis, evidence: list[EvidenceFragment]) -> str:
        """Generate critical counter-perspective."""
        return (
            f"Critical analysis of hypothesis '{hypothesis.statement}': "
            f"Ensure boundary conditions and unmeasured covariates are controlled."
        )

    async def extract(self, raw_text: str, target_schema_name: str) -> dict[str, str]:
        """Extract mock structured key-value pairs."""
        return {
            "schema": target_schema_name,
            "extracted_claim": "Observation of non-linear state variation",
            "confidence": "0.85",
        }

    async def synthesize(self, claims: list[Claim]) -> str:
        """Synthesize overview."""
        return f"Synthesized overview of {len(claims)} empirical claims."
