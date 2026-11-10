# ednaflow-lca comparison harness

`review-tools/` retains the reproducible builder used during the independent
review of `ednaflow-lca` and a short audit record describing how that review
material relates to the maintained release tests.

The review process included a blind review and an informed differential review
on 8 November 2026. The comparison cases were used to isolate individual
behaviours in the upstream eDNAFlow LCA scripts and the standalone
`ednaflow-lca` adaptation. Findings were subsequently assessed individually:
some were fixed, some became explicit intentional divergences, and speculative
or unnecessarily fragile changes were not adopted automatically.

The review involved AI-assisted analysis followed by human review, targeted
regression tests, and release-remediation decisions. The maintained scientific
behaviour is defined by the source, tests, `PARITY_REPORT.md`, `CHANGELOG.md`
and release documentation, not by dated generated review output.

## Files retained in this repository

| Path | Purpose |
|---|---|
| `build_comparison_harness.py` | Reconstructs the review harness, including named comparison cases, scripts and historical review evidence. |
| `harness_README.md` | This audit and usage note. |

Generated harness directories such as `cases/`, `scripts/`, `results/` and
`evidence/` are intentionally not committed under `review-tools/`. They are
review scaffolding and can contain dated or diagnostic output. Generate them in
a disposable working directory when historical review reproduction is needed.

## Maintained regression evidence

Findings accepted during remediation were converted into focused tests under
`tests/` where practical. The maintained suite now includes, among other cases:

- exclusion and literal-TSV parsing behaviour;
- exact eDNAFlow 22-column BLAST validation;
- feature-interleaving invariance;
- numeric identity-difference semantics;
- conservative cross-domain LCA behaviour;
- rank-aware NCBI taxonomy and `nodes.dmp` consistency;
- blank-domain semantics;
- per-hit terminal taxon provenance;
- legacy-compatible and genuine rank-aware full parity fixtures;
- Galaxy managed-reference and Data Manager tests.

The independent differential review workflow is maintained under
`.github/workflows/independent-review.yml` and is configured as a release gate
for pull requests to, and pushes on, `main`.

## Reproducing the historical harness

Do not run the builder in `review-tools/` if the goal is to keep the checkout
minimal. Copy `build_comparison_harness.py` to a throwaway directory and execute
it there, then inspect the generated README/instructions and cases.

The historical harness used the vendored upstream files at repository root:

- `upstream_runAssign_collapsedTaxonomy.py`
- `upstream_working_function.py`

Their provenance is documented in `NOTICE`. The upstream scripts are GPL-3.0
and remain subject to their upstream licence and attribution.

The upstream LCA script performs shell-based taxonomy download and file
operations. Historical differential execution therefore used network-blocking
stubs, timeouts and disposable directories so those operations could not modify
the release checkout or fetch changing taxonomy during deterministic tests.

## Interpreting historical review results

Historical generated result tables represent the implementation state at the
time of review. They are not release specifications and should not be copied
back into this directory as current expected output.

For current behaviour use, in order of authority:

1. focused tests under `tests/`;
2. `PARITY_REPORT.md` for compatibility scope and intentional divergences;
3. `CHANGELOG.md` for release changes;
4. current CI workflows and Galaxy tests.

Synthetic taxonomy cases from the historical harness are useful for isolating
logic, but unusual ranks, viruses, synthetic constructs and current NCBI rank
semantics should be validated against real dated NCBI taxonomy when the decision
depends on those details. The release parity suite now includes a genuine
matching `rankedlineage.dmp`/`nodes.dmp` subset from the 5 November 2026 snapshot
for rank-aware reference testing.

## Licence

The review harness builder and generated review cases were created for this
review process. Upstream eDNAFlow scripts used for comparison are separately
attributed in `NOTICE` and remain GPL-3.0. No generated review output changes
the licence or authorship of either eDNAFlow or `ednaflow-lca`.
