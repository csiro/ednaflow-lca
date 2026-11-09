# eDNAFlow LCA standalone package and Galaxy wrapper

`ednaflow-lca` is a standalone, offline adaptation of the Lowest Common Ancestor
(LCA) taxonomy-assignment component from eDNAFlow. It packages the LCA logic as
a reproducible Python CLI and provides Galaxy tooling for both managed NCBI
taxonomy snapshots and custom taxonomy files.

The project is a modified GPL-3.0-only derivative. Upstream eDNAFlow scripts
are retained at repository root for provenance; see `NOTICE`, `LICENSE`,
`CHANGELOG.md`, `PARITY_REPORT.md` and `CITATION.cff`.

## Current status

- Python CLI and package implemented; supported and tested on Python 3.10-3.12.
- eDNAFlow 22-column BLAST tabular contract explicitly validated.
- Literal TSV parsing prevents CSV quote semantics from merging physical BLAST
  records.
- Feature tables accept a non-empty feature-ID header such as `#ID`,
  `feature_id`, `OTU`, `ASV` or `Zotu`.
- The documented/default reference fixture retains 76/76 assignment parity with
  the upstream LCA implementation.
- Intentional corrections to legacy behaviour are documented in
  `PARITY_REPORT.md`, including numeric identity-difference comparison and
  cross-domain ambiguity handling.
- NCBI taxonomy can be rank-aware through paired `rankedlineage.dmp` and
  `nodes.dmp` inputs. Terminal NCBI taxon name and rank are preserved in
  filtered-hit provenance while the assignment table reports the seven-rank
  LCA.
- Galaxy wrapper supports versioned managed taxonomy snapshots or custom
  taxonomy input.
- Galaxy Data Manager installs and registers both NCBI taxonomy files with
  independent checksums, structural validation and persistent managed paths.
- Managed and custom Galaxy execution paths are tested end-to-end.
- Bioconda recipe scaffold is present and will be finalised against the public
  v0.1.0 release archive.

## Validation

The automated validation suite includes:

- Python tests on 3.10, 3.11 and 3.12;
- the 76/76 default reference-fixture parity regression;
- independent differential cases for compatibility and intentional corrections;
- BLAST structure, parsing, exclusion and malformed-input tests;
- rank-aware taxonomy and terminal-provenance tests;
- Galaxy `planemo lint` and functional execution tests;
- Data Manager persistence, registered-path and checksum verification for both
  `rankedlineage.dmp` and `nodes.dmp`; and
- a managed-reference Galaxy execution test proving both registered taxonomy
  paths are supplied to the LCA job.

## Publication sequence

1. Complete the v0.1.0 release metadata and provenance checks.
2. Publish the approved CSIRO repository at
   https://github.com/csiro/ednaflow-lca.
3. Tag the `0.1.0` release.
4. Replace the Bioconda recipe source placeholders with the public release
   archive URL and SHA-256, then validate and submit the recipe.
5. Use the resulting package dependency for Galaxy Australia deployment of the
   eDNA Lab wrapper and Data Manager.

## Upstream attribution

The original eDNAFlow project is available at:
https://github.com/mahsa-mousavi/eDNAFlow

Original publication:
Mousavi-Derazmahalleh M et al. (2021), *eDNAFlow, an automated, reproducible
and scalable workflow for analysis of environmental DNA sequences exploiting
Nextflow and Singularity*. Molecular Ecology Resources 21:1697-1704.
DOI: 10.1111/1755-0998.13356.

See `NOTICE` for the derivative-work provenance and modification summary.

## Licence and release approval

Upstream eDNAFlow and this derivative are distributed under GPL-3.0. The full
GPL-3.0-only licence text is included in `LICENSE`.

CSIRO Software Release Review SR-0285 has received delegate approval for public
release of the eDNAFlow LCA adaptation. The approved public repository is
https://github.com/csiro/ednaflow-lca.
