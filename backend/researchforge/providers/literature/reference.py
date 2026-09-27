"""Deterministic Reference Literature Provider with synthetic scholarly fixtures."""

from researchforge.domain.contracts.literature import LiteratureProvider
from researchforge.domain.models.literature import Citation, Paper, Source, compute_source_identity
from researchforge.domain.schemas.dtos import (
    LiteratureCitationRequest,
    LiteratureFetchRequest,
    LiteratureRelatedRequest,
    LiteratureSearchRequest,
    LiteratureSearchResponse,
)

# Canonical synthetic fixture dataset
SYNTHETIC_PAPERS = [
    Paper(
        id="paper_ref_01",
        title="[SYNTHETIC REFERENCE LITERATURE] Linear Scaling of Response Y under Parameter X",
        authors=["Dr. Alice Vance", "Dr. Bob Martinez"],
        abstract=(
            "We investigate the empirical relationship between Parameter X and Response Y across the "
            "standard range [0.0, 2.0]. Using calibrated ordinary least squares regression (N=100), we observe "
            "a statistically significant monotonic positive linear response (slope=2.14, p<0.001). "
            "Conclusion: Parameter X reliably increases Response Y under controlled condition Z."
        ),
        year=2024,
        doi="10.1000/synth.ref.01",
        venue="Journal of Synthetic Empirical Studies",
        journal_name="Journal of Synthetic Empirical Studies",
        citation_count=35,
    ),
    Paper(
        id="paper_ref_02",
        title="[SYNTHETIC REFERENCE LITERATURE] Null Effects of Parameter X in High-Variance Regimes",
        authors=["Dr. Clara Oswald", "Dr. David Tennant"],
        abstract=(
            "We replicate Response Y measurements under Parameter X in the range [0.0, 2.0] using a high-variance "
            "unbuffered assay. Our findings show no statistically significant effect of Parameter X on Response Y "
            "(slope=0.03, p=0.78). This directly contradicts prior linear claims and suggests measurement sensitivity."
        ),
        year=2024,
        doi="10.1000/synth.ref.02",
        venue="Transactions on Contradictory Phenomena",
        journal_name="Transactions on Contradictory Phenomena",
        citation_count=18,
    ),
    Paper(
        id="paper_ref_03",
        title="[SYNTHETIC REFERENCE LITERATURE] Non-Linear Saturation of Response Y at Elevated Parameter X",
        authors=["Dr. Elena Rostova", "Dr. Frank Castle"],
        abstract=(
            "Expanding observation into elevated regimes of Parameter X in range [2.0, 5.0], we observe a pronounced "
            "saturation plateau starting at X=2.5 followed by thermal degradation at X>4.0. "
            "The linear model breaks down beyond boundary condition X=2.0."
        ),
        year=2025,
        doi="10.1000/synth.ref.03",
        venue="Advanced Nonlinear Dynamics",
        journal_name="Advanced Nonlinear Dynamics",
        citation_count=42,
    ),
    Paper(
        id="paper_ref_04",
        title="[SYNTHETIC REFERENCE LITERATURE] Methodological Limitations of Low-Sample Assays in Response Y Studies",
        authors=["Dr. Grace Hopper", "Dr. Henry Wu"],
        abstract=(
            "A meta-methodological analysis reveals that assay sample sizes below N=25 introduce "
            "severe false negative rates when assessing Parameter X. Methodological standardization "
            "is required to resolve conflicting reports."
        ),
        year=2025,
        doi="10.1000/synth.ref.04",
        venue="Methodological Review of Computational Discovery",
        journal_name="Methodological Review of Computational Discovery",
        citation_count=29,
    ),
]


class ReferenceLiteratureProvider(LiteratureProvider):
    """Deterministic, offline Reference Literature Provider backed by synthetic fixtures."""

    provider_name: str = "reference-literature-v1"

    def __init__(self) -> None:
        self._sources: dict[str, Source] = {}
        self._init_fixtures()

    def _init_fixtures(self) -> None:
        for paper in SYNTHETIC_PAPERS:
            src_id = compute_source_identity(self.provider_name, paper.id)
            source = Source(
                id=src_id,
                title=paper.title,
                source_type="SCHOLARLY_PAPER",
                uri=f"https://doi.org/{paper.doi}",
                provider_name=self.provider_name,
                provider_record_id=paper.id,
                retrieval_query="parameter_x",
                retrieved_content=paper.abstract,
                paper=paper,
            )
            self._sources[src_id] = source

    async def search(
        self,
        query_or_request: str | LiteratureSearchRequest,
        limit: int = 10,
    ) -> list[Source] | LiteratureSearchResponse:
        """Deterministic search over synthetic literature fixtures."""
        if isinstance(query_or_request, LiteratureSearchRequest):
            query = query_or_request.query
            limit = query_or_request.limit
            is_dto = True
        else:
            query = str(query_or_request)
            is_dto = False

        q_lower = query.lower()
        matched: list[Source] = []
        for s in self._sources.values():
            if (
                q_lower in s.title.lower()
                or q_lower in s.retrieved_content.lower()
                or "parameter" in q_lower
                or "response" in q_lower
                or not q_lower
            ):
                matched.append(s)

        matched = matched[:limit]
        if is_dto:
            return LiteratureSearchResponse(
                sources=matched,
                total_found=len(matched),
                provider_name=self.provider_name,
                query_hash=matched[0].raw_content_hash if matched else "",
            )
        return matched

    async def fetch(
        self,
        record_id_or_request: str | LiteratureFetchRequest,
    ) -> Source | None:
        """Fetch source by ID or provider record ID."""
        rec_id = (
            record_id_or_request.record_id
            if isinstance(record_id_or_request, LiteratureFetchRequest)
            else str(record_id_or_request)
        )
        if rec_id in self._sources:
            return self._sources[rec_id]
        for s in self._sources.values():
            if s.provider_record_id == rec_id:
                return s
        return None

    async def citations(
        self,
        paper_id_or_request: str | LiteratureCitationRequest,
    ) -> list[Citation]:
        """Return synthetic citation relationships."""
        target_id = (
            paper_id_or_request.paper_id
            if isinstance(paper_id_or_request, LiteratureCitationRequest)
            else str(paper_id_or_request)
        )
        return [
            Citation(
                id=f"cite_{target_id}_01",
                source_paper_id="paper_ref_04",
                target_paper_id=target_id,
                citation_intent="CONTRADICTION" if "02" in target_id else "BACKGROUND",
                is_influential=True,
            )
        ]

    async def related(
        self,
        paper_id_or_request: str | LiteratureRelatedRequest,
        limit: int = 5,
    ) -> list[Paper]:
        """Return related synthetic papers."""
        return SYNTHETIC_PAPERS[:limit]
