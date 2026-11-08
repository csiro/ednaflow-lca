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
- Corrected Galaxy Data Manager persistence and registration. The Data Manager
  writes rankedlineage.dmp to Galaxy's actual output extra-files path, moves it
  into persistent managed reference storage, registers an absolute Tool Data
  Table path, and records the installed SHA-256. Snapshot IDs include the date
  and a checksum prefix to avoid collisions between different same-day
  taxonomy contents.
- Added end-to-end Galaxy CI assertions that verify the registered taxonomy
  file exists at the stored path and that registered, installed, and fixture
  SHA-256 values agree.
