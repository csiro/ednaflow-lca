# Changelog
## 0.1.0 - release candidate
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
- Corrected the identity-difference comparison used by the iterative upstream
  filtering algorithm. eDNAFlow formats identity gaps and the user threshold
  to three decimals but compares the resulting strings lexicographically.
  This is numerically incorrect for some non-default thresholds. ednaflow-lca
  keeps the three-decimal convention and iterative neighbour filtering but
  compares the rounded values numerically. The eDNAFlow defaults (qcov 100,
  pident 97, identity difference 1) and the 76-row upstream parity fixture are
  unchanged by this correction.
- Corrected cross-domain LCA handling. Legacy eDNAFlow stops lineage comparison
  before the domain rank, so equally qualifying hits from different domains can
  retain whichever domain appears first. ednaflow-lca now compares domain as
  well; conflicting domains yield `dropped` at domain and every lower rank.
  Qualifying hit evidence is retained in the filtered-hit output. The 76-row
  default reference parity fixture is unchanged by this correction.
- Added rank-aware NCBI taxonomy handling. Managed snapshots now install and
  checksum both `rankedlineage.dmp` and `nodes.dmp`. The current NCBI node rank
  is used to place terminal species and genus names at their actual represented
  ranks, while infraspecific taxa retain the ancestral species rank.
- Expanded filtered-hit provenance to preserve the exact terminal NCBI
  `taxon_name` and `taxon_rank` alongside the seven-rank lineage used for LCA.
  For example, taxid 9615 retains `Canis lupus familiaris` / `subspecies` while
  its LCA species lineage is `Canis lupus`.
- Added managed/custom taxonomy selection to the Galaxy wrapper. Managed NCBI
  references pass both `rankedlineage.dmp` and `nodes.dmp` to the CLI; custom
  analyses can optionally provide `nodes.dmp` or retain legacy/simple taxonomy
  behaviour when it is omitted.
- Corrected Galaxy Data Manager persistence and registration. Managed files are
  written through Galaxy's real output extra-files path, moved into persistent
  Tool Data storage, and registered with absolute paths. Snapshot identifiers
  combine installation date with a digest derived from both managed files.
- Added end-to-end Galaxy CI assertions that verify persistent paths and
  independent checksums for `rankedlineage.dmp` and `nodes.dmp`, plus a managed
  wrapper execution test proving both registered paths are passed to the LCA job.
