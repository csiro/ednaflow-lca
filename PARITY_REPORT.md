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

During the original parity work, the standalone code was corrected to preserve
three subtle upstream behaviours exercised by this fixture: iterative
adjacent-hit filtering, blank-rank handling in lineage collapse, and use of the
ranked-lineage taxon-name field as the species output. Those statements describe
the original parity milestone; subsequent independently reviewed corrections are
documented below. Output column labels differ deliberately, but the reference-
fixture assignment data rows remain identical at the default settings.

Three source taxid strings are absent from the reference taxonomy fixture:
`1915147`, `591391;1915147`, and `N/A`. The original implementation likewise
cannot assign lineage rows for those exact strings.

## Independent differential review and remediation

Subsequent differential testing against the vendored upstream eDNAFlow scripts
identified behaviours not covered by the 76-assignment reference fixture. The
reference fixture is retained as a default-setting regression, not as a complete
behavioural specification.

### Exclusion semantics

The first standalone implementation searched excluded phrases only in the
BLAST common-name field and normalised case. Upstream performs case-sensitive
searching against the taxonomy-enriched BLAST evidence. The standalone
implementation was corrected to match upstream exclusion semantics. Regression
gates cover taxonomy names, subject titles, scientific-name fields, phrase and
case behaviour.

### Literal TSV parsing

The first standalone implementation used Python CSV parsing with a tab
delimiter. CSV quote semantics can join multiple physical BLAST records when a
field starts with a double quote. BLAST and abundance-table inputs are now read
as physical lines split on literal tabs, while retaining row-width and numeric
validation.

### Intentional numerical correction to upstream behaviour

Legacy eDNAFlow compares three-decimal formatted identity gaps and thresholds as
strings. `ednaflow-lca` keeps the upstream iterative neighbour-filter structure
and three-decimal precision, but compares the values numerically. The documented
defaults (qcov 100, pident 97, identity difference 1) are unchanged. Independent
testing found zero text-versus-numeric disagreements at difference 1 and zero
such disagreements across 1,467 same-feature neighbouring pairs in the full
reference BLAST fixture; the 76-assignment default parity regression remains
green.

Targeted non-default regressions cover difference 2 and 9 with a 14-point gap
and difference 10 with a 2-point gap.

### Intentional cross-domain LCA correction

Legacy eDNAFlow stops lineage comparison before domain, so qualifying hits from
different domains can retain whichever domain appears first. `ednaflow-lca`
compares domain as well: conflicting domain evidence yields `dropped` at domain
and every lower represented rank. Qualifying hits remain in filtered-hit
provenance. `tests/test_cross_domain.py` covers this correction; the reference
fixture remains unchanged.

### Rank-aware species and infraspecific handling

NCBI `rankedlineage.dmp` contains the current `taxon_name` and selected ancestral
ranks. For a current species or genus node, its corresponding ancestral rank
field can be blank; for an infraspecific node, the species field contains the
ancestral species. Managed NCBI snapshots therefore pair `rankedlineage.dmp`
with `nodes.dmp`, which supplies the current node rank.

When `nodes.dmp` is available, `ednaflow-lca` places a current species or genus
name at its actual represented rank and retains the ancestral species for taxa
below species. Examples covered by tests include:
- genus-node `Escherichia` -> genus `Escherichia`, species blank;
- `Escherichia` plus `Escherichia coli` -> genus `Escherichia`, species dropped;
- `Canis lupus familiaris` plus `Canis lupus` -> species `Canis lupus`.

The assignment table remains the seven-rank LCA. The filtered-hit provenance
output separately preserves each contributing hit's exact terminal NCBI
`taxon_name` and `taxon_rank`, plus its resolved seven-rank lineage. Thus taxid
9615 can retain `Canis lupus familiaris` / `subspecies` while its species lineage
is `Canis lupus`. This avoids forcing multiple terminal names into one LCA row.

A custom taxonomy may omit `nodes.dmp`; that path deliberately retains the
legacy/simple taxonomy interpretation. Managed NCBI snapshots always provide
both files to the CLI.

## Galaxy taxonomy persistence and managed execution validation

The NCBI Data Manager is tested as an installed Galaxy reference, not merely as
a successful tool job. Each managed snapshot contains both `rankedlineage.dmp`
and `nodes.dmp`, with independent SHA-256 values recorded in the Tool Data Table.
The snapshot identifier combines installation date with a digest derived from
both files.

CI verifies that:
- Galaxy creates `ednaflow_lca_taxonomy.loc`;
- both registered paths are absolute and physically exist;
- registered, installed and deterministic-fixture SHA-256 values agree for both
  `rankedlineage.dmp` and `nodes.dmp`;
- the Galaxy wrapper can select a managed table entry; and
- the rendered LCA job command receives both `--taxonomy` and
  `--taxonomy-nodes` managed paths.

The Galaxy wrapper also retains a custom-taxonomy route, with optional
`nodes.dmp` for rank-aware custom NCBI analysis.

## Compatibility statement

The project preserves eDNAFlow LCA behaviour where scientifically defensible and
documents intentional corrections where legacy behaviour is unsafe,
numerically incorrect, or taxonomically misleading. The 76/76 comparison is a
parity statement for the documented/default reference fixture, not a claim of
bug-for-bug equivalence for every non-default parameter or edge case.

Intentional departures currently include numeric identity-difference comparison,
refusing to retain an arbitrary domain for cross-domain evidence, and rank-aware
placement of current NCBI genus/species names when `nodes.dmp` is available.
Terminal NCBI names and ranks are preserved separately as provenance.
