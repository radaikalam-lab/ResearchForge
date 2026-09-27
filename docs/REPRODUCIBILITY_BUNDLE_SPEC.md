# REPRODUCIBILITY BUNDLE SPECIFICATION

## 1. Objective
Ensure every computational research finding produced by ResearchForge can be packaged into an exportable, self-contained, machine-verifiable research bundle.

---

## 2. Bundle Structure

Exported research bundles follow the canonical layout:
```text
reproducibility/
    manifest.json
    source/
        experiment.py
        environment.lock
    parameters/
        parameters.json
    environment/
        system_profile.json
    provenance/
        event_stream.jsonl
        checkpoints.json
    artifacts/
        findings.md
        dataset.csv
    results/
        run_output.json
```

---

## 3. Manifest Schema (`manifest.json`)

The manifest contains cryptographic digests of all runtime inputs, parameters, outputs, and provenance links:

```json
{
  "manifest_version": "1.0.0",
  "project_id": "proj_reference_01",
  "run_id": "run_sim_01",
  "reproducibility_level": "LEVEL_1_COMPUTATIONAL",
  "generated_at": "2026-09-27T08:30:00Z",
  "system": {
    "researchforge_version": "0.3.0",
    "python_version": "3.13.14",
    "os": "Windows",
    "architecture": "AMD64"
  },
  "execution": {
    "execution_backend": "ReferenceExecutionBackend",
    "random_seed": 42
  },
  "hashes": {
    "parameter_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "input_hash": "a1b2c3d4...",
    "output_hash": "f5e6d7c8...",
    "provenance_head_hash": "7a8b9c0d...",
    "checkpoint_hash": "9e8d7c6b..."
  },
  "artifacts": {
    "report.md": "3c4d5e...",
    "metrics.json": "1a2b3c..."
  }
}
```

---

## 4. Reproducibility Taxonomy

1. **LEVEL_0_PROVENANCE**: Complete DAG audit trail and immutable event chain.
2. **LEVEL_1_COMPUTATIONAL**: Deterministic code and fixed pseudo-random generator seed.
3. **LEVEL_2_ENVIRONMENT**: Pinned dependency lockfile, Python runtime, and host OS specs.
4. **LEVEL_3_BITWISE**: Byte-for-byte exact container image digest, strict IEEE 754 floating-point runtime flags, and deterministic BLAS/LAPACK bindings.
