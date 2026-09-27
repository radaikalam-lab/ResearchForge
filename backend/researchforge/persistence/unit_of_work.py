from typing import Any

from sqlalchemy.orm import Session

from researchforge.persistence.adapters.graph import GraphPersistenceAdapter
from researchforge.persistence.database import DatabaseManager, get_db_manager
from researchforge.persistence.repositories import (
    ArtifactRepository,
    CandidateDesignEvaluationRepository,
    ClaimRepository,
    ConclusionRepository,
    ContradictionRepository,
    EvidenceClaimBindingRepository,
    EvidenceRepository,
    ExperimentalDesignCandidateRepository,
    ExperimentDesignRepository,
    ExperimentRepository,
    FalsificationRepository,
    GapRepository,
    HumanDecisionRepository,
    HypothesisRepository,
    IdempotencyRepository,
    ParetoCandidateSetRepository,
    ProjectRepository,
    ProvenanceRepository,
    QuestionRepository,
    RunRepository,
    SourceRepository,
    ThreadRepository,
)
from researchforge.provenance.ledger import ProvenanceLedger
from researchforge.provenance.models import ProvenanceEvent


class UnitOfWork:
    """Atomic Unit of Work encompassing repositories and provenance recording."""

    def __init__(self, db_manager: DatabaseManager | None = None) -> None:
        self.db_manager = db_manager or get_db_manager()
        self.session: Session | None = None
        self.projects: ProjectRepository | None = None
        self.threads: ThreadRepository | None = None
        self.questions: QuestionRepository | None = None
        self.sources: SourceRepository | None = None
        self.evidence: EvidenceRepository | None = None
        self.claims: ClaimRepository | None = None
        self.bindings: EvidenceClaimBindingRepository | None = None
        self.contradictions: ContradictionRepository | None = None
        self.gaps: Any = None
        self.hypotheses: HypothesisRepository | None = None
        self.experiments: ExperimentRepository | None = None
        self.experiment_designs: ExperimentDesignRepository | None = None
        self.candidates: ExperimentalDesignCandidateRepository | None = None
        self.evaluations: CandidateDesignEvaluationRepository | None = None
        self.pareto_sets: ParetoCandidateSetRepository | None = None
        self.runs: RunRepository | None = None
        self.falsifications: FalsificationRepository | None = None
        self.decisions: HumanDecisionRepository | None = None
        self.conclusions: ConclusionRepository | None = None
        self.artifacts: ArtifactRepository | None = None
        self.semantic_graphs: GraphPersistenceAdapter | None = None
        self.provenance_repo: ProvenanceRepository | None = None
        self.idempotency: IdempotencyRepository | None = None
        self.ledger: ProvenanceLedger | None = None

    def __enter__(self) -> "UnitOfWork":
        self.session = self.db_manager.session_factory()
        self.projects = ProjectRepository(self.session)
        self.threads = ThreadRepository(self.session)
        self.questions = QuestionRepository(self.session)
        self.sources = SourceRepository(self.session)
        self.evidence = EvidenceRepository(self.session)
        self.claims = ClaimRepository(self.session)
        self.bindings = EvidenceClaimBindingRepository(self.session)
        self.contradictions = ContradictionRepository(self.session)
        self.gaps = GapRepository(self.session)
        self.hypotheses = HypothesisRepository(self.session)
        self.experiments = ExperimentRepository(self.session)
        self.experiment_designs = ExperimentDesignRepository(self.session)
        self.candidates = ExperimentalDesignCandidateRepository(self.session)
        self.evaluations = CandidateDesignEvaluationRepository(self.session)
        self.pareto_sets = ParetoCandidateSetRepository(self.session)
        self.runs = RunRepository(self.session)
        self.falsifications = FalsificationRepository(self.session)
        self.decisions = HumanDecisionRepository(self.session)
        self.conclusions = ConclusionRepository(self.session)
        self.artifacts = ArtifactRepository(self.session)
        self.semantic_graphs = GraphPersistenceAdapter(self.session)
        self.provenance_repo = ProvenanceRepository(self.session)
        self.idempotency = IdempotencyRepository(self.session)
        self.ledger = ProvenanceLedger()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.session is not None:
            if exc_type is not None:
                self.session.rollback()
            else:
                self.session.commit()
            self.session.close()

    def commit(self) -> None:
        """Explicit transaction commit."""
        if self.session:
            self.session.commit()

    def rollback(self) -> None:
        """Explicit transaction rollback."""
        if self.session:
            self.session.rollback()

    def record_provenance(self, event: ProvenanceEvent) -> ProvenanceEvent:
        """Record provenance event to both in-memory cryptographic chain and DB transaction."""
        committed = self.ledger.record_event(event) if (self.ledger and not event.event_hash) else event
        if self.provenance_repo:
            self.provenance_repo.record_event(committed)
        return committed
