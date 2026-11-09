# Upstream compatibility and parity report

## Reference parity test

Date of original full-fixture comparison: 2026-11-05

Taxonomy: NCBI expanded taxonomy `rankedlineage.dmp`, SHA-256
`21bc61dd1c40087801e06da63f611cb7ca621e1bb986ead8ca0366614c26bf25`.
A reduced fixture containing the exact upstream BLAST taxid strings is stored
for deterministic regression testing.

Inputs:
- upstream `blastResult_2test_LCAscript.tab`: 1,785 rows;
- upstream `curated_zotuTable_2test_LCAscript.tab`: 495 feature rows;
- thresholds: qcov 100, pident 97, identity difference 1.

Result at the documented/default eDNAFlow settings:
- upstream assignments: 76;
- standalone assignments: 76;
- assignment IDs in common: 76;
- IDs present in only one output: 0;
- row mismatches across taxonomy, feature ID, unique-hit count and abundance: 0.

Output column labels differ deliberately, but assignment data rows remain
identical at the documented/default settings. Three source taxid strings are
absent from the reference taxonomy fixture: `1915147`, `591391;1915147`, and
`N/A`. The original implementation likewise cannot assign lineage rows for
those exact strings.

### Rank-aware parity against the same dated NCBI snapshot

The original 76/76 regression uses `rankedlineage.dmp` alone to preserve the
legacy-compatible interpretation. Release remediation recovered the genuine
matching `nodes.dmp` from the same 5 November 2026 NCBI `new_taxdump` snapshot.
A deterministic subset, `nodes_subset_2026-11-05.dmp`, was generated from that
historical file for every taxid in the committed ranked-lineage subset:

- ranked-lineage taxids: 526;
- genuine matching node records: 526;
- missing node records: 0.

Running the full reference fixture with both the dated ranked-lineage subset and
the genuine matching node-rank subset also produces the same 76 assignment
rows as `upstream_expected.tsv`. Therefore the release has two complementary
full-reference regressions:

- legacy-compatible rankedlineage-only assignment parity: 76/76;
- rank-aware rankedlineage + matching nodes assignment parity: 76/76.

These results demonstrate assignment parity for this dated reference fixture.
They do not imply bug-for-bug equivalence for every parameter, taxonomy snapshot
or malformed-input edge case.

## Independent differential review and remediation

Subsequent differential testing against the vendored upstream eDNAFlow scripts
identified behaviours not exercised by the original 76-assignment fixture. The
reference fixture is retained as a default-setting regression, not as a complete
behavioural specification.

### Exclusion semantics

The first standalone implementation searched excluded phrases only in the
BLAST common-name field and normalised case. Upstream performs case-sensitive
searching against the taxonomy-enriched BLAST evidence. The standalone
implementation was corrected to match upstream exclusion semantics. Regression
gates cover taxonomy names, subject titles, scientific-name fields, phrase and
case behaviour.

### Literal TSV and explicit input contracts

BLAST and abundance-table inputs are read as physical lines split on literal
tabs, avoiding CSV quote semantics that can merge physical BLAST records. The
supported BLAST input is explicitly the 22-column eDNAFlow layout, not arbitrary
BLAST `outfmt 6`. Feature-table identifier headers may be any non-empty label.

### Feature interleaving

Interleaved feature records are valid. An independently reviewed regression
showed that physical interleaving could previously interrupt adjacent-hit
comparisons, allowing an unrelated feature row to alter another feature's hit
selection. `select_hits()` now performs stable per-feature grouping before the
existing adjacent-hit algorithm: feature order follows first appearance and hit
order within each feature is preserved. Grouped and interleaved forms therefore
produce the same selection while preserving the intended order-dependent
within-feature semantics.

### Intentional numerical correction to upstream behaviour

Legacy eDNAFlow compares three-decimal formatted identity gaps and thresholds as
strings. `ednaflow-lca` keeps the upstream iterative neighbour-filter structure
and three-decimal precision, but compares the values numerically. The documented
defaults remain qcov 100, pident 97 and identity difference 1. Targeted
non-default regressions cover cases where lexicographic and numeric comparison
differ.

### Intentional cross-domain LCA correction

Legacy eDNAFlow stops lineage comparison before domain, so qualifying hits from
different domains can retain whichever domain appears first. `ednaflow-lca`
compares domain as well: conflicting domain evidence yields `dropped` at domain
and every lower represented rank. Qualifying hits remain in filtered-hit
provenance.

### Domain semantics

A blank NCBI domain field remains blank. The parser no longer falls back to the
kingdom field, because doing so can label a kingdom value as `domain`. Sparse or
unusual taxonomy is not rejected merely for having a blank represented rank.

### Rank-aware species and infraspecific handling

NCBI `rankedlineage.dmp` contains the current `taxon_name` and selected ancestral
ranks. Managed NCBI snapshots pair it with `nodes.dmp`, which supplies the
current node rank.

When `nodes.dmp` is available, `ednaflow-lca` places a current species or genus
name at its actual represented rank and retains the ancestral species for taxa
below species. Examples covered by focused tests include:
- genus-node `Escherichia` -> genus `Escherichia`, species blank;
- `Escherichia` plus `Escherichia coli` -> genus `Escherichia`, species dropped;
- `Canis lupus familiaris` plus `Canis lupus` -> species `Canis lupus`.

When a custom `nodes.dmp` is explicitly supplied, each taxid represented in the
ranked-lineage input must have a corresponding rank entry. An inconsistent pair
now fails clearly instead of silently interpreting the missing current rank and
potentially downgrading assignment. A custom taxonomy may still omit
`nodes.dmp` entirely to use the documented legacy/simple interpretation.

The assignment table remains the seven-rank LCA. `filtered_hits` separately
preserves each contributing hit's terminal NCBI `taxon_name`, terminal
`taxon_rank`, and resolved seven-rank lineage. Thus taxid 9615 can retain
`Canis lupus familiaris` / `subspecies` while its species lineage is
`Canis lupus`.

## Galaxy taxonomy persistence and managed execution validation

The NCBI Data Manager is tested as an installed Galaxy reference, not merely as
a successful tool job. Each managed snapshot contains both `rankedlineage.dmp`
and `nodes.dmp`, with independent SHA-256 values recorded in the Tool Data Table.
The snapshot identifier combines installation date with a digest derived from
both files.

CI verifies that:
- Galaxy creates and populates the managed taxonomy Tool Data Table;
- both registered paths are absolute and physically exist;
- registered, installed and deterministic-fixture SHA-256 values agree for both
  managed taxonomy files;
- the rendered managed LCA command receives both `--taxonomy` and
  `--taxonomy-nodes` paths; and
- a plain `planemo test galaxy/ednaflow_lca.xml` can resolve the repository-local
  managed test entry through `tool_data_table_conf.xml.test`, without CI creating
  a separate Tool Data Table for that wrapper job.

The production-style Data Manager persistence test uses its own isolated empty
Tool Data Table so the test-only wrapper table cannot mask registration defects.
The Galaxy wrapper also retains a custom-taxonomy route with optional
`nodes.dmp`.

## Differential review as a release gate

The retained differential harness documents the independent review cases, while
accepted findings are represented by focused maintained tests where practical.
`.github/workflows/independent-review.yml` is configured for pull requests to
and pushes on `main`, so the differential checks operate as a release gate
rather than only as historical review scaffolding.

## Compatibility statement

The project preserves eDNAFlow LCA behaviour where scientifically defensible and
documents intentional corrections where legacy behaviour is unsafe,
numerically incorrect, order-fragile or taxonomically misleading. The 76/76
comparisons are parity statements for the documented/default 5 November 2026
reference fixture in both legacy-compatible and genuine rank-aware modes, not a
claim of universal bug-for-bug equivalence.

Intentional departures include numeric identity-difference comparison,
conservative cross-domain resolution, stable per-feature evaluation of
interleaved records, preservation of blank domain semantics, and rank-aware
placement of current NCBI genus/species names when `nodes.dmp` is supplied.
Terminal NCBI names and ranks remain separately available as provenance.
