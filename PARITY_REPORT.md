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
ranked-lineage taxon-name field as the species output. Output column labels
differ deliberately (`feature_id` and snake_case explanatory names), but the
reference-fixture data rows are identical at the default settings.

Three source taxid strings are absent from the reference taxonomy fixture:
`1915147`, `591391;1915147`, and `N/A`. The original implementation likewise
cannot assign lineage rows for those exact strings.

## Independent differential review and remediation

Subsequent differential testing against the vendored upstream eDNAFlow scripts
identified behaviours not covered by the 76-assignment reference fixture.
These tests are retained as regression evidence rather than treating the
reference fixture as a complete behavioural specification.

### Exclusion semantics

The first standalone implementation searched excluded phrases only in the
BLAST common-name field and normalised case. Upstream performs case-sensitive
searching against the taxonomy-enriched BLAST evidence. This changed real
assignments in targeted differential cases. The standalone implementation was
corrected to match upstream exclusion semantics. Regression gates now verify
exclusion terms occurring in taxonomy names, subject titles and scientific-name
fields, as well as phrase and case behaviour.

### Literal TSV parsing

The first standalone implementation used Python CSV parsing with a tab
delimiter. CSV quote semantics can join multiple physical BLAST records when a
field starts with a double quote. eDNAFlow BLAST input is a literal tabular
format rather than quoted CSV. BLAST and abundance-table inputs are therefore
now read as physical lines split on literal tab characters, while retaining
row-width and numeric validation. Differential quote cases now pass without
silent row merging.

### Intentional numerical correction to upstream behaviour

The upstream filtering algorithm formats the percentage-identity gap and the
`identity_difference` threshold to three decimal places and compares the
resulting strings. Lexicographic string comparison is not equivalent to numeric
comparison for all non-default thresholds.

`ednaflow-lca` intentionally corrects this behaviour while preserving the
upstream iterative adjacent-hit/filtering structure. Both values are rounded to
three decimal places and then compared numerically.

This correction does not change the documented/default eDNAFlow configuration:
- qcov = 100;
- pident = 97;
- identity difference = 1.

Independent comparison found zero text-versus-numeric disagreements at an
identity-difference threshold of 1 across the tested parameter grid, zero
such disagreements across 1,467 same-feature neighbouring pairs in the full
reference BLAST fixture, and the 76-assignment default parity regression
continues to pass.

Targeted non-default regression cases demonstrate the corrected behaviour:
- pident floor 80, gap 14, difference 2: the lower hit is removed numerically;
- pident floor 80, gap 14, difference 9: the lower hit is removed numerically;
- pident floor 97, gap 2, difference 10: both hits are retained numerically.

These cases intentionally differ from legacy eDNAFlow where its string
comparison produces a numerically incorrect result.

### Intentional cross-domain LCA correction

Legacy eDNAFlow compares lineage ranks from species upward but stops before the
domain rank. If equally qualifying hits span different domains, such as
Bacteria and Eukaryota, the legacy result can retain the domain of whichever hit
appears first while marking lower ranks as `dropped`.

`ednaflow-lca` intentionally compares domain as the highest represented rank.
When qualifying evidence conflicts at domain, domain and all lower ranks are
returned as `dropped`. The feature is not deleted: its qualifying hit evidence
remains available in the filtered-hit output and its input abundance remains
part of the source data. This avoids asserting a domain unsupported by the
combined evidence.

The behaviour is covered by `tests/test_cross_domain.py`. The full 76-assignment
reference fixture continues to pass unchanged because that fixture does not
exercise a qualifying cross-domain conflict.

## Galaxy taxonomy persistence validation

The NCBI taxonomy Data Manager is additionally tested as an installed Galaxy
reference, not merely as a successful tool job. CI verifies that Galaxy creates
`ednaflow_lca_taxonomy.loc`, that the registered taxonomy path is absolute and
exists, and that the registered SHA-256 equals both the installed
`rankedlineage.dmp` checksum and the deterministic taxonomy fixture checksum.
Snapshot identifiers combine installation date and a checksum prefix.

## Compatibility statement

The project aims to preserve eDNAFlow LCA behaviour where that behaviour is
scientifically defensible and to document intentional corrections when legacy
behaviour is unsafe or numerically incorrect. The 76/76 reference comparison
therefore demonstrates parity at the documented/default configuration; it is
not a claim of bug-for-bug equivalence for every non-default parameter or edge
case. Intentional departures currently include numeric identity-difference
comparison and refusing to retain a specific domain when qualifying evidence
conflicts across domains.
