# Full upstream parity report

Date: 2026-11-05
Taxonomy: NCBI expanded taxonomy `rankedlineage.dmp`, SHA-256
`21bc61dd1c40087801e06da63f611cb7ca621e1bb986ead8ca0366614c26bf25`.
A reduced fixture containing the exact upstream BLAST taxid strings is stored
for deterministic regression testing.

Inputs:
- upstream `blastResult_2test_LCAscript.tab`: 1,785 rows;
- upstream `curated_zotuTable_2test_LCAscript.tab`: 495 feature rows;
- thresholds: qcov 100, pident 97, identity difference 1.

Result:
- upstream assignments: 76;
- standalone assignments: 76;
- assignment IDs in common: 76;
- IDs present in only one output: 0;
- row mismatches across taxonomy, feature ID, unique-hit count and abundance: 0.

During parity work, the standalone code was corrected to preserve three subtle
upstream behaviours: iterative adjacent-hit filtering, blank-rank handling in
lineage collapse, and use of the ranked-lineage taxon-name field as species.
Output column labels differ deliberately (`feature_id` and snake_case explanatory
names), but all data rows are identical.

Three source taxid strings are absent from the current taxonomy fixture:
`1915147`, `591391;1915147`, and `N/A`. The original implementation likewise
cannot assign lineage rows for those exact strings.
