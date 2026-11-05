# eDNAFlow LCA standalone package and Galaxy wrapper

Production-oriented first implementation. The upstream GPL-3 scripts are retained at repository root for provenance. The new CLI preserves the core unique-taxid, qcov/pident, best-hit difference, lineage-collapse, and count-table join behaviour while removing runtime NCBI downloads and fixed temporary filenames.

## Status
- Python package and CLI implemented.
- Offline deterministic unit test implemented.
- Galaxy XML and functional fixture implemented.
- Bioconda recipe scaffold implemented.
- Real upstream full-fixture parity remains blocked on a dated NCBI rankedlineage snapshot matching the original fixture.

## Publication sequence
1. Create a dedicated public repository, retaining GPL-3 and upstream attribution.
2. Run `python -m pytest` and `ednaflow-lca --help`.
3. Tag a `0.1.0` release and replace the Bioconda source placeholders with the release URL and SHA-256.
4. Submit the Bioconda recipe.
5. After publication, run `planemo lint` and `planemo test` on `galaxy/ednaflow_lca.xml`.
6. Add a Galaxy Data Manager for dated NCBI taxonomy snapshots.

## CSIRO release evidence
- Upstream and derivative licence: GPL-3.0.
- Upstream provenance and publication: `NOTICE` and `CITATION.cff`.
- Changes: `NOTICE` and `CHANGELOG.md`.
- Automated tests cover LCA collapse, thresholds, exclusions and malformed input.
- Full upstream result parity against a dated NCBI ranked-lineage snapshot remains
  a release gate.
- Public repository creation and Bioconda submission remain subject to CSIRO approval.
