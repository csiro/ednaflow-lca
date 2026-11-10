# Changelog

## 0.1.0 - 2026-11-09 release candidate

- Initial standalone offline adaptation of eDNAFlow LCA.
- Added explicit taxonomy input, CLI validation, deterministic outputs, tests,
  Galaxy wrapper and Bioconda recipe scaffold.
- Restored upstream exclusion semantics: exclusion terms are matched
  case-sensitively against the taxonomy-enriched BLAST evidence rather than
  only the BLAST common-name field. Differential regression cases verify
  taxonomy-name, subject-title, scientific-name, phrase, and case behaviour.
- Replaced CSV-style input parsing with literal TSV physical-line parsing for
  BLAST and abundance-table inputs. BLAST tabular quotation marks are treated
  as field content and can no longer merge multiple physical records.
- Enforced the exact 22-column eDNAFlow BLAST contract while allowing any
  non-empty feature-table identifier header. Interleaved feature records remain
  valid input.
- Corrected interleaved-hit filtering so unrelated feature rows cannot interrupt
  adjacent-hit comparisons for another feature. Feature order is preserved by
  first appearance and hit order is preserved within each feature.
- Corrected the identity-difference comparison used by the iterative upstream
  filtering algorithm. eDNAFlow formats identity gaps and the user threshold
  to three decimals but compares the resulting strings lexicographically.
  `ednaflow-lca` retains three-decimal precision and the iterative neighbour
  structure but compares values numerically. The documented/default reference
  assignments remain unchanged.
- Corrected cross-domain LCA handling. Conflicting domain evidence yields
  `dropped` at domain and every lower represented rank rather than retaining
  whichever domain appeared first.
- Preserved blank NCBI domain fields as blank rather than falling back to the
  kingdom field and labelling a kingdom as a domain.
- Added rank-aware NCBI taxonomy handling. Managed snapshots install and
  checksum both `rankedlineage.dmp` and `nodes.dmp`; current species and genus
  names are placed at their actual represented ranks, while infraspecific taxa
  retain the ancestral species rank.
- Added consistency validation for explicit rank-aware taxonomy pairs: when
  `nodes.dmp` is supplied, each taxid represented by `rankedlineage.dmp` must
  have a corresponding node-rank entry instead of being silently downgraded.
- Expanded filtered-hit provenance to preserve terminal NCBI `taxon_name` and
  `taxon_rank` alongside the seven-rank lineage used for LCA. For example,
  taxid 9615 retains `Canis lupus familiaris` / `subspecies` while its species
  lineage is `Canis lupus`.
- Strengthened reference parity evidence. The dated 5 November 2026 parity
  fixture retains 76/76 assignment parity in rankedlineage-only mode and also
  in rank-aware mode using an authentic matching `nodes.dmp` subset containing
  all 526 ranked-lineage taxids with zero missing node records.
- Added managed/custom taxonomy selection to the Galaxy wrapper. Managed NCBI
  references pass both `rankedlineage.dmp` and `nodes.dmp`; custom analyses can
  optionally provide `nodes.dmp` or retain legacy/simple taxonomy behaviour when
  it is omitted.
- Corrected Galaxy Data Manager persistence and registration. Managed files are
  installed through Galaxy's real output extra-files path, moved into persistent
  Tool Data storage and registered with absolute paths. Snapshot identifiers
  combine installation date with a digest derived from both managed files.
- Added structural validation for managed taxonomy content and a finite NCBI
  download timeout without imposing biological-completeness rules.
- Added end-to-end Galaxy CI assertions for persistent paths and independent
  checksums for both managed taxonomy files, managed-wrapper execution, and a
  self-contained ordinary Planemo test using repository-local Tool Data test
  configuration.
- Made the independent differential review a release gate for pull requests to
  and pushes on `main`, and added CI concurrency to cancel superseded Galaxy
  validation runs.
- Updated Galaxy help to document the validated input contracts, `dropped`
  semantics, output provenance and managed versus custom taxonomy behaviour.
- Updated package authorship, GPL-3.0-only metadata, upstream provenance,
  modification notice, line-ending policy and Bioconda `run_exports` for public
  release preparation.
