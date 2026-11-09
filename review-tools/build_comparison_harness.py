"""Rebuild the ednaflow-lca comparison harness from this single file.

This file holds every case, script, result and evidence file of the harness as readable text,
one line of the original per line here (tabs show as \t, Windows line endings as \r).
Running it recreates the folder byte for byte and checks every file against its SHA-256.

Usage:  python3 build_comparison_harness.py [TARGET_FOLDER]
        (default: ./ednaflow-lca-comparison-harness; an existing folder is never overwritten)

After rebuilding, read README.md in the new folder. The case inputs are under cases/,
and cases/index.tsv says what each case tests and which review finding it supports.
"""
import hashlib, os, stat, sys

FILES = {}  # relative path -> (content, sha256); content is str (UTF-8) or bytes


def L(*parts):
    """Join the original lines with newline characters."""
    return "\n".join(parts)


# ---- README.md ---------------------------------------------------------------------------------
FILES['README.md'] = (L(
    '# ednaflow-lca comparison harness',
    '',
    'This folder holds the test cases and scripts behind the two reviews of `ednaflow-lca` (the blind review and the informed review of 8 November 2026). Each case is a small input that isolates one behaviour. The runner puts the same case through the upstream eDNAFlow LCA scripts and through the `ednaflow-lca` command-line tool, so you can see side by side where they agree and where they differ.',
    '',
    'It is review scaffolding, not finished test code. Use it to:',
    '',
    '- write failing tests before each fix;',
    '- start the upstream-comparison CI job recommended in the informed review (section P);',
    '- show reviewers exactly where the tool matches eDNAFlow and where it deliberately differs.',
    '',
    'Nothing here changes the `ednaflow-lca` code.',
    '',
    '## What is in the folder',
    '',
    '| Path | Contents |',
    '|---|---|',
    '| `cases/index.tsv` | One line per case: what it tests and which review finding it supports |',
    '| `cases/set1/` | 13 cases from the blind review (A to M) and their taxonomy file |',
    '| `cases/set2/` | 36 cases from the informed review (D, M, O, P, Q, S, T and X series) and their taxonomy file |',
    "| `cases/set*/rankedlineage.dmp` | Synthetic taxonomy lines in NCBI's `rankedlineage.dmp` layout, covering only the taxa the cases use |",
    '| `scripts/run_both.sh` | Runs one case through upstream and `ednaflow-lca` |',
    '| `scripts/run_all.sh` | Runs every case and writes the results table |',
    '| `scripts/summarise.py` | Builds `results/results.tsv` from the case outputs |',
    '| `scripts/make_cases.py`, `scripts/make_cases2.py` | The generators used to write most of the cases (for reference) |',
    '| `scripts/diff_compare.py` | Maps where the text and numeric identity-difference comparisons disagree |',
    '| `scripts/bench.py` | The hit-filtering benchmark in section N of the informed review |',
    '| `scripts/parity_checks.py`, `scripts/species_rule_check.py` | Checks run against the 76-row parity fixture |',
    '| `results/results.tsv` | Results from a full run on 8 November 2026 |',
    '| `results/console_output.txt` | The raw output of that run |',
    '| `evidence/` | Supporting records for the informed review (Galaxy Data Manager runs, the Data Manager probe fixture, benchmark and validation output) |',
    '',
    "Each case folder holds `blast.tsv` (eDNAFlow's 22-column BLAST layout), `features.tsv` (a small abundance table) and, where the thresholds differ from the defaults of 100, 97 and 1, a `params` file with three numbers: query coverage, percent identity and identity difference.",
    '',
    'The case folders themselves are the inputs. Case M, P11 and the three `_with_other_feature` cases were written by hand, so the generators do not recreate them.',
    '',
    '## Requirements',
    '',
    '- Linux or macOS, with `bash` and Python 3.9 or later. No other packages are needed.',
    '- A checkout of the `ednaflow-lca` repository. The runner needs two things from it:',
    '  - its `src` folder;',
    '  - the vendored upstream scripts `upstream_runAssign_collapsedTaxonomy.py` and `upstream_working_function.py` (at the repository root).',
    '',
    "  The runner also accepts upstream's own file names, from a clone of `mahsa-mousavi/eDNAFlow` (folder `LCA_taxonomyAssignment_scripts`).",
    '',
    '## Running it',
    '',
    'Work on a copy, because the runner writes output folders into every case folder:',
    '',
    '```',
    'cp -r ednaflow-lca-comparison-harness /tmp/harness',
    'bash /tmp/harness/scripts/run_all.sh /path/to/ednaflow-lca /path/to/ednaflow-lca/src',
    '```',
    '',
    'The first argument is the folder that holds the upstream scripts (here the repository root), and the second is the `src` folder. To run a single case:',
    '',
    '```',
    'bash /tmp/harness/scripts/run_both.sh /tmp/harness/cases/set1/A_exclusion_via_taxonomy_name /path/to/ednaflow-lca /path/to/ednaflow-lca/src',
    '```',
    '',
    'Each case folder then gains two output folders:',
    '',
    "- `up/` from upstream: `out.tsv`, `run.log` and upstream's intermediate files;",
    '- `sa/` from `ednaflow-lca`: `a.tsv` (assignments), `h.tsv` (filtered hits), `s.tsv` (summary) and `run.log`.',
    '',
    'A full run takes a few seconds.',
    '',
    '## Reading the results table',
    '',
    '`results/results.tsv` has one row per case and feature. For each side it gives:',
    '',
    '- the lowest rank that is neither empty nor `dropped` (for example `species Antechinus flavipes`), and any blank ranks;',
    '- the exit status.',
    '',
    "A feature missing from a side's output shows as `absent`. Two rows for one feature show as `[2 rows]`. The `agree` column is `yes` only when both seven-rank lineages and both exit statuses match. Where upstream crashes and `ednaflow-lca` stops with a clear message, `agree` is `NO` even though both fail. Read those cases with the error column.",
    '',
    'The run included here matches the findings in the informed review. In particular, A, B, C, X01, X02, X03, I and M show the exclusion and quoting divergences (D1 and D2), and P03 shows the inherited column shift.',
    '',
    '## How upstream is run safely',
    '',
    "Upstream's script downloads NCBI's taxonomy with `wget` and `unzip`, then runs `mkdir`, `mv`, `tr` and `rm` in its working directory. For each case, `run_both.sh`:",
    '',
    '1. copies both upstream scripts into a fresh `up/` folder inside the case;',
    '2. puts stub `wget` and `unzip` commands that simply fail first on `PATH`, so nothing is downloaded;',
    '3. clears proxy variables for that command;',
    "4. copies the case set's `rankedlineage.dmp` into `up/`, which upstream's own `tr` step then converts.",
    '',
    'All of upstream\'s file operations stay inside `up/`. You will see "mv: cannot stat" messages in `up/run.log`; they come from the stubbed download and are expected. For a CI job, also run this step without network access, with a timeout, and in a throwaway directory.',
    '',
    '`ednaflow-lca` is run with `python3 -I` and the `src` folder added to `sys.path`, so nothing is imported from the case folder.',
    '',
    '## Turning this into tests and CI',
    '',
    '1. **Unit tests.** For each fix, copy the relevant case into `tests/`, and assert the result the informed review recommends (section P lists the expected outputs). Write the test first, and confirm it fails before the fix.',
    '2. **Differential CI job.**',
    '   - Run `run_all.sh`, or an equivalent pytest fixture, on every push.',
    '   - Keep an allow-list of intentional divergences: case, reason, and policy (for example, P06 because the byte-order mark handling is a deliberate improvement).',
    '   - Fail the job on any difference not on the list.',
    '   - Treat upstream crashes (P04, P07, T01, T02 and X03 without a second feature) as expected failures.',
    "3. **Golden files.** Commit upstream's outputs for each case too, so the tests can still run where executing upstream is not possible. The live run then proves the golden files are genuine.",
    '',
    '## Limits',
    '',
    "- **The taxonomy lines are synthetic.** They follow NCBI's layout, but they are not copied from a real dump. Cases about viruses, synthetic constructs and NCBI's newer ranks (H, K and L) should be re-checked against lines from a current snapshot (informed review, item V1).",
    '- **Hand-built test data.** The cases test behaviour, not realistic data volumes. For speed, use `scripts/bench.py`.',
    '- **Dated results.** `results/results.tsv` reflects the archive reviewed on 8 November 2026. Expect it to change as fixes land; that is the point.',
    '- **`evidence/probe_dm_fixture/`.** This is a diagnostic Data Manager written to demonstrate a Galaxy behaviour (informed review, section D). It is not a proposed implementation.',
    '',
    '## Licence',
    '',
    'The scripts and cases in this folder were written for the review and contain no code from `ednaflow-lca` or eDNAFlow. The upstream scripts they run are GPL-3.0 and are not included here.',
    '',
), '07aeb0afc041fad63b24f76cd6aaa05a1244af231136fb95693def1afcd161b2')

# ---- cases/index.tsv ---------------------------------------------------------------------------
FILES['cases/index.tsv'] = (L(
    'set\tcase\twhat it tests\treview reference',
    "set1\tA_exclusion_via_taxonomy_name\tExcluded term only in NCBI's taxon name (BLAST names N/A)\tD1 (B1)",
    "set1\tB_eukaryote_marine_clone\tUpstream term 'eukaryote marine clone', shortened in ednaflow-lca\tD1 (B1)",
    "set1\tC_case_of_excluded_term\t'Uncultured bacterium' with a capital U (upstream is case-sensitive)\tD1 (B1)",
    'set1\tD_strain_and_species\tE. coli K-12 strain plus E. coli: taxon name splits the species\tH row 20 (S6)',
    'set1\tE_domain_conflict\tBacteria plus Eukaryota: domain is never compared\tH row 18 (S5)',
    "set1\tF_non_contiguous_feature\tOne feature's hits split into two blocks\tH row 8 (S2)",
    'set1\tG_text_comparison_of_difference\tThreshold 3, floor 80, hits 14 points apart (text comparison)\tH rows 13-15 (S3)',
    'set1\tH_empty_superkingdom\tLineage with an empty domain field\tH row 17 (S1)',
    'set1\tI_quote_in_title\tUnclosed quote at the start of a subject title\tD2 (B2)',
    'set1\tJ_first_hit_per_taxid\tSame taxid at 90% then 99%: first row taken before thresholds\tH row 5 (G2)',
    'set1\tK_synthetic_construct_second\tSynthetic construct (32630, all ranks blank) as the second of three hits\tH row 17 (S1)',
    'set1\tL_synthetic_construct_first\tSynthetic construct as the first hit\tH row 17 (S1)',
    'set1\tM_quote_merges_rows\tTitle starting with a quote, later title containing one: rows merge\tD2 (B2)',
    'set2\tD00_diff0\tDifference threshold 0\tH row 12',
    'set2\tD01_diff1_floor80_gap14\tThreshold 1, floor 80, gap 14 (text comparison correct)\tH row 12',
    'set2\tD02_diff2_floor80_gap14\tThreshold 2, floor 80, gap 14 (text comparison wrong)\tH row 13 (S3)',
    'set2\tD02b_diff2_floor97_gap2.5\tThreshold 2 at the default floor (safe)\tH row 13',
    'set2\tD09_diff9_floor80_gap14\tThreshold 9, gap 14 (text comparison wrong)\tH row 13 (S3)',
    'set2\tD09b_diff9_floor80_gap9.5\tThreshold 9, gap 9.5 (correct)\tH row 13',
    'set2\tD10_diff10_floor97_gap2\tThreshold 10, gap 2 (text comparison wrongly removes the lower hit)\tH row 14 (S3)',
    'set2\tD10b_diff10_floor80_gap14\tThreshold 10, gap 14 (correct)\tH row 14',
    'set2\tM01_blast_feature_missing_from_table\tBLAST feature absent from the abundance table\tH row 23 (N10)',
    'set2\tM02_duplicate_table_ids\tDuplicate ID in the abundance table\tH row 24',
    'set2\tO01_row_order\tFeature-table order differs from BLAST order\tH row 9 (O2)',
    'set2\tP02_embedded_quote\tQuote in the middle of a title (harmless)\tD2',
    'set2\tP03_tab_inside_title\tTab inside a title shifts columns; coverage read from bitscore\tD2 (N5)',
    'set2\tP04_blank_line\tBlank line inside the BLAST file\tD2 (N8)',
    'set2\tP05_CRLF\tWindows line endings in BLAST and table\tD2',
    'set2\tP06_BOM_on_blast\tUTF-8 byte-order mark at the start of the BLAST file\tD2 (N8)',
    'set2\tP07_short_blast_row\tBLAST row with 20 columns\tD2 (N8)',
    'set2\tP08_ragged_table_row\tAbundance-table row with too few columns\tD2 (N8)',
    'set2\tP09_quoted_table_R_style\tAbundance table exported with quoted cells\tD2, H row 26',
    'set2\tP10_table_quote_spans_rows\tQuote in the table that spans rows\tD2 (B2)',
    'set2\tP11_latin1_byte_in_title\tNon-UTF-8 byte in a title\tD2',
    'set2\tQ01_lower_coverage_removed_despite_higher_identity\tCoverage floor 90: 100% identity at 95% coverage loses to 97% at 100%\tH row 10 (G3)',
    'set2\tQ02_identity_tie\tTwo hits with equal identity\tH row 11',
    'set2\tQ03_neighbour_chain\tHits 100, 99.5, 99, 98.5 all survive a threshold of 1\tH row 16 (S4)',
    'set2\tS01_genus_node_plus_species\tGenus-rank taxid (561) plus a species hit\tH row 21 (N6)',
    'set2\tS02_genus_node_alone\tGenus-rank taxid alone: genus name in the species column\tH row 21 (N6)',
    'set2\tS03_subspecies_and_species\tCanis lupus familiaris plus Canis lupus\tH row 20 (S6)',
    'set2\tT01_semicolon_taxid_top_hit\tMulti-taxid top hit, only feature in the file (upstream crashes on an empty intermediate)\tH row 6, N8',
    'set2\tT01_semicolon_taxid_top_hit_with_other_feature\tAs T01 with a second feature, so upstream runs\tH row 6 (O4)',
    'set2\tT02_NA_taxid_top_hit\tN/A taxid top hit, only feature in the file\tH row 7, N8',
    'set2\tT02_NA_taxid_top_hit_with_other_feature\tAs T02 with a second feature\tH row 7 (O4)',
    'set2\tT03_semicolon_taxid_tie\tMulti-taxid hit tied with a single-taxid hit\tH row 6',
    'set2\tX01_term_only_in_stitle\tExcluded term only in the subject title\tD1 (B1)',
    'set2\tX02_term_only_in_sscinames\tExcluded term only in sscinames\tD1 (B1)',
    'set2\tX03_excluded_top_hit_removes_good_hit\tExcluded 100% hit removes a 98.5% hit, only feature in the file\tD1, H row 22',
    'set2\tX03_excluded_top_hit_removes_good_hit_with_other_feature\tAs X03 with a second feature, so upstream runs\tD1, H row 22 (O4)',
    '',
), 'c484d130578d5aa1f319901f34f277430838157777fa74277dde2e850a5addad')

# ---- scripts/bench.py --------------------------------------------------------------------------
FILES['scripts/bench.py'] = (L(
    '"""Usage: python3 -I bench.py SRC UPSTREAM_DIR WORKDIR N_ROWS. Ten hits per feature, eDNAFlow\'s default -max_target_seqs."""',
    'import sys, time, os',
    'src, updir, work, n = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])',
    'PIDS = [100, 99.8, 99.5, 98.0, 97.9, 97.5, 97.2, 97.0, 96.0, 95.0]',
    "path = os.path.join(work, f'blast_{n}.tsv')",
    "with open(path, 'w') as h:",
    '    for i in range(n):',
    '        f, k = divmod(i, 10)',
    "        x = ['N/A'] * 22",
    "        x[0], x[1], x[2], x[6] = f'Zotu{f}', f's{i}', str(1000 + (i * 7) % 5000), f'{PIDS[k]:.3f}'",
    "        x[7] = x[8] = x[9] = '100'; x[18], x[19], x[20], x[21] = '1e-50', '200', '100', '100'",
    "        h.write('\\t'.join(x) + '\\n')",
    'which = sys.argv[5]',
    "if which == 'adaptation':",
    '    sys.path.insert(0, src)',
    '    from ednaflow_lca.cli import read_blast, select_hits',
    "    t0 = time.perf_counter(); rows = read_blast(__import__('pathlib').Path(path)); t1 = time.perf_counter()",
    '    sel, _ = select_hits(rows, 100, 97, 1); t2 = time.perf_counter()',
    "    print(f'adaptation n={n}: parse {t1-t0:.2f} s, select_hits {t2-t1:.2f} s, kept {len(sel)}')",
    'else:',
    '    sys.path.insert(0, updir)',
    '    import working_function as wf',
    "    t0 = time.perf_counter(); r = wf.filterBlast(path, '1', '100', '97'); t1 = time.perf_counter()",
    '    print(f\'upstream   n={n}: filterBlast {t1-t0:.2f} s, kept {len(r["unq"])}\')',
    '',
), '4437fdcb40e2a33f806de304db21118759b23d277ad528194e0b43054ef144cb')

# ---- scripts/diff_compare.py -------------------------------------------------------------------
FILES['scripts/diff_compare.py'] = (L(
    'import sys, itertools',
    'def text_gt(a, d):  # upstream and current rule',
    "    return format(a, '.3f') > format(float(d), '.3f')",
    'def num3_gt(a, d):  # numeric comparison of the same 3-decimal values',
    "    return float(format(a, '.3f')) > float(format(float(d), '.3f'))",
    "print('1. Text versus numeric, identity floor 80 (all identities 80.000 to 100.000 in 0.5 steps):')",
    'vals = [80 + i * 0.5 for i in range(41)]',
    'for d in [0, 0.5, 1, 1.5, 1.999, 2, 3, 5, 9, 9.999, 10, 15, 20]:',
    '    bad = [(x, y) for x, y in itertools.combinations(vals, 2) if text_gt(abs(x - y), d) != num3_gt(abs(x - y), d)]',
    '    ex = bad[0] if bad else None',
    '    print(f\'   diff {d:>6}: {len(bad):4d} of {41*40//2} pairs disagree\' + (f\'; e.g. {ex[0]} vs {ex[1]} (gap {abs(ex[0]-ex[1]):g}): text says {"remove" if text_gt(abs(ex[0]-ex[1]), d) else "keep"}\' if ex else \'\'))',
    "print('2. Same with identity floor 97 (97.000 to 100.000, 0.001 steps, sampled):')",
    'v97 = [97 + i * 0.001 for i in range(0, 3001, 7)]',
    'for d in [1, 2, 3, 9, 10]:',
    '    bad = sum(text_gt(abs(x - y), d) != num3_gt(abs(x - y), d) for x, y in itertools.combinations(v97, 2))',
    "    print(f'   diff {d}: {bad} disagreeing pairs')",
    "print('3. Raw float comparison (no 3-decimal rounding) versus upstream at the default diff 1:')",
    'for x, y in [(99.1, 98.1), (98.6, 97.6), (100.0, 99.0), (98.765, 97.765), (99.3, 98.3)]:',
    '    g = abs(x - y)',
    "    print(f'   {x} vs {y}: float gap {g!r}; upstream removes? {text_gt(g, 1)}; raw float gap > 1? {g > 1}')",
    "rows = [l.rstrip('\\r\\n').split('\\t') for l in open(sys.argv[1], encoding='utf-8') if l.strip()]",
    'n = m = 0',
    'for a, b in zip(rows, rows[1:]):',
    '    if a[0] == b[0]:',
    '        g = abs(float(a[6]) - float(b[6])); n += 1',
    '        if (g > 1) != text_gt(g, 1): m += 1',
    "print(f'4. Parity BLAST file: {n} same-feature neighbour pairs; raw-float and upstream rules disagree on {m}')",
    '',
), '9c0ddb3f04cf06a8440404d896eb7f74df9ba66ee648d671646a1ab825cf44eb')

# ---- scripts/make_cases.py ---------------------------------------------------------------------
FILES['scripts/make_cases.py'] = (L(
    '"""Write small BLAST, feature-table and rankedlineage inputs for upstream-versus-standalone checks."""',
    'import sys',
    'from pathlib import Path',
    '',
    'out = Path(sys.argv[1])',
    'out.mkdir(parents=True, exist_ok=True)',
    "T = '\\t|\\t'",
    "def lin(taxid, name, species='', genus='', family='', order='', klass='', phylum='', kingdom='', superkingdom=''):",
    "    return T.join([str(taxid), name, species, genus, family, order, klass, phylum, kingdom, superkingdom]) + '\\t|\\n'",
    'lineage = [',
    "    lin(38775, 'Antechinus flavipes', '', 'Antechinus', 'Dasyuridae', 'Dasyuromorphia', 'Mammalia', 'Chordata', 'Metazoa', 'Eukaryota'),",
    "    lin(100272, 'uncultured eukaryote', superkingdom='Eukaryota'),",
    "    lin(9606, 'Homo sapiens', '', 'Homo', 'Hominidae', 'Primates', 'Mammalia', 'Chordata', 'Metazoa', 'Eukaryota'),",
    "    lin(562, 'Escherichia coli', '', 'Escherichia', 'Enterobacteriaceae', 'Enterobacterales', 'Gammaproteobacteria', 'Pseudomonadota', 'Pseudomonadati', 'Bacteria'),",
    "    lin(83333, 'Escherichia coli K-12', 'Escherichia coli', 'Escherichia', 'Enterobacteriaceae', 'Enterobacterales', 'Gammaproteobacteria', 'Pseudomonadota', 'Pseudomonadati', 'Bacteria'),",
    "    lin(999999, 'Test virus', '', 'Testvirus', 'Testviridae', 'Testvirales', 'Testviricetes', 'Testviricota', 'Testvirae', ''),",
    ']',
    "(out / 'rankedlineage.dmp').write_text(''.join(lineage))",
    '',
    "def hit(q, taxid, pid, qcov=100, comname='N/A', sciname='N/A', stitle='N/A'):",
    "    x = ['N/A'] * 22",
    "    x[0], x[1], x[2], x[3], x[4] = q, f's_{q}_{taxid}_{pid}', str(taxid), sciname, comname",
    "    x[6], x[7], x[8], x[9], x[17], x[18], x[19], x[20], x[21] = str(pid), '100', '100', '500', stitle, '1e-50', '200', str(qcov), str(qcov)",
    "    return '\\t'.join(x) + '\\n'",
    '',
    'cases = {',
    '  # A: excluded name only in the taxonomy (scomnames N/A, as when BLAST runs without taxdb)',
    "  'A_exclusion_via_taxonomy_name': [hit('OTU_A', 100272, 99), hit('OTU_A', 38775, 98.5)],",
    "  # B: upstream list has 'eukaryote marine clone'; standalone has 'eukaryote marine clone OLI11008'",
    "  'B_eukaryote_marine_clone': [hit('OTU_B', 9606, 99, comname='eukaryote marine clone ABC1'), hit('OTU_B', 38775, 99)],",
    '  # C: upstream match is case-sensitive; standalone lower-cases',
    "  'C_case_of_excluded_term': [hit('OTU_C', 9606, 99, comname='Uncultured bacterium'), hit('OTU_C', 38775, 99)],",
    "  # D: a strain taxid and its species collapse to genus because 'species' is tax_name",
    "  'D_strain_and_species': [hit('OTU_D', 562, 99), hit('OTU_D', 83333, 99)],",
    '  # E: hits in different domains',
    "  'E_domain_conflict': [hit('OTU_E', 562, 99), hit('OTU_E', 9606, 99)],",
    "  # F: one feature's hits in two separate blocks",
    "  'F_non_contiguous_feature': [hit('OTU_F', 9606, 99), hit('OTU_X', 38775, 99), hit('OTU_F', 38775, 99)],",
    '  # H: empty superkingdom field',
    "  'H_empty_superkingdom': [hit('OTU_H', 999999, 99)],",
    '  # J: first hit of a taxid fails the threshold; a later hit of the same taxid passes',
    "  'J_first_hit_per_taxid': [hit('OTU_J', 9606, 90), hit('OTU_J', 9606, 99), hit('OTU_J', 38775, 98.5)],",
    '}',
    'for name, rows in cases.items():',
    '    d = out / name',
    '    d.mkdir(exist_ok=True)',
    "    (d / 'blast.tsv').write_text(''.join(rows))",
    "    feats = sorted({r.split('\\t')[0] for r in rows})",
    "    (d / 'features.tsv').write_text('#ID\\tS1\\n' + ''.join(f'{f}\\t5\\n' for f in feats))",
    '# G: identity difference compared as text (run with pident 80, difference 3)',
    "d = out / 'G_text_comparison_of_difference'; d.mkdir(exist_ok=True)",
    "(d / 'blast.tsv').write_text(hit('OTU_G', 9606, 99) + hit('OTU_G', 38775, 85))",
    "(d / 'features.tsv').write_text('#ID\\tS1\\nOTU_G\\t5\\n')",
    "(d / 'params').write_text('100 80 3')",
    '# I: a BLAST title that starts with a double quote and is not closed',
    "d = out / 'I_quote_in_title'; d.mkdir(exist_ok=True)",
    '(d / \'blast.tsv\').write_text(hit(\'OTU_I\', 9606, 99, stitle=\'"Homo sapiens clone 7\') + hit(\'OTU_I\', 38775, 99) + hit(\'OTU_I2\', 38775, 99))',
    "(d / 'features.tsv').write_text('#ID\\tS1\\nOTU_I\\t5\\nOTU_I2\\t3\\n')",
    "print('cases written')",
    '',
), 'efdb48f49410dad65a77cadb224903a9554b84aacb51245c42a27248c139af57')

# ---- scripts/make_cases2.py --------------------------------------------------------------------
FILES['scripts/make_cases2.py'] = (L(
    '"""Second-pass review cases. Usage: python3 -I make_cases2.py OUTDIR',
    'Each case folder gets blast.tsv, features.tsv and optionally params ("qcov pid diff").',
    'Taxonomy lines are synthetic, in NCBI rankedlineage.dmp layout:',
    'tax_id | tax_name | species | genus | family | order | class | phylum | kingdom | superkingdom |',
    '"""',
    'import os',
    'import sys',
    '',
    'OUT = sys.argv[1]',
    'os.makedirs(OUT, exist_ok=True)',
    '',
    'TAX = {',
    "    '38775': ['Antechinus flavipes', '', 'Antechinus', 'Dasyuridae', 'Dasyuromorphia', 'Mammalia', 'Chordata', 'Metazoa', 'Eukaryota'],",
    "    '100272': ['uncultured eukaryote', '', '', '', '', '', '', '', 'Eukaryota'],",
    "    '77133': ['uncultured bacterium', '', '', '', '', '', '', '', 'Bacteria'],",
    "    '9606': ['Homo sapiens', '', 'Homo', 'Hominidae', 'Primates', 'Mammalia', 'Chordata', 'Metazoa', 'Eukaryota'],",
    "    '9598': ['Pan troglodytes', '', 'Pan', 'Hominidae', 'Primates', 'Mammalia', 'Chordata', 'Metazoa', 'Eukaryota'],",
    "    '562': ['Escherichia coli', '', 'Escherichia', 'Enterobacteriaceae', 'Enterobacterales', 'Gammaproteobacteria', 'Pseudomonadota', 'Pseudomonadati', 'Bacteria'],",
    "    '561': ['Escherichia', '', '', 'Enterobacteriaceae', 'Enterobacterales', 'Gammaproteobacteria', 'Pseudomonadota', 'Pseudomonadati', 'Bacteria'],",
    "    '9612': ['Canis lupus', '', 'Canis', 'Canidae', 'Carnivora', 'Mammalia', 'Chordata', 'Metazoa', 'Eukaryota'],",
    "    '9615': ['Canis lupus familiaris', 'Canis lupus', 'Canis', 'Canidae', 'Carnivora', 'Mammalia', 'Chordata', 'Metazoa', 'Eukaryota'],",
    '}',
    "with open(os.path.join(OUT, 'rankedlineage.dmp'), 'w', newline='\\n') as h:",
    '    for t, f in TAX.items():',
    "        h.write('\\t|\\t'.join([t] + f) + '\\t|\\n')",
    '',
    '',
    "def row(otu, taxid, pid, qcov='100', title='N/A', sci='N/A', com='N/A'):",
    "    x = ['N/A'] * 22",
    "    x[0], x[1], x[2], x[3], x[4] = otu, f's_{otu}_{taxid}_{pid}', taxid, sci, com",
    "    x[6], x[7], x[8], x[9] = str(pid), '100', '100', '500'",
    "    x[17], x[18], x[19], x[20], x[21] = title, '1e-50', '200', str(qcov), str(qcov)",
    "    return '\\t'.join(x)",
    '',
    '',
    'def case(name, rows, feats=None, params=None, raw_blast=None, raw_feats=None, enc_blast=None):',
    '    d = os.path.join(OUT, name)',
    '    os.makedirs(d, exist_ok=True)',
    "    blast = raw_blast if raw_blast is not None else '\\n'.join(rows) + '\\n'",
    "    with open(os.path.join(d, 'blast.tsv'), 'wb') as h:",
    "        h.write(blast.encode(enc_blast or 'utf-8'))",
    '    if raw_feats is None:',
    "        feats = feats or sorted({r.split('\\t')[0] for r in rows})",
    "        raw_feats = '#ID\\tS1\\n' + ''.join(f'{f}\\t5\\n' for f in feats)",
    "    with open(os.path.join(d, 'features.tsv'), 'wb') as h:",
    "        h.write(raw_feats.encode('utf-8'))",
    '    if params:',
    "        with open(os.path.join(d, 'params'), 'w') as h:",
    "            h.write(params + '\\n')",
    '',
    '',
    "A = '38775'",
    '# Exclusion semantics',
    "case('X01_term_only_in_stitle', [row('OTU', '9606', 99, title='uncultured organism clone 7 18S rRNA gene'), row('OTU', A, 99)])",
    "case('X02_term_only_in_sscinames', [row('OTU', '9606', 99, sci='uncultured bacterium'), row('OTU', A, 99)])",
    "case('X03_excluded_top_hit_removes_good_hit', [row('OTU', '100272', 100), row('OTU', A, 98.5)])",
    '# Taxon-name and rank semantics',
    "case('S01_genus_node_plus_species', [row('OTU', '561', 99), row('OTU', '562', 99)])",
    "case('S02_genus_node_alone', [row('OTU', '561', 99)])",
    "case('S03_subspecies_and_species', [row('OTU', '9615', 99), row('OTU', '9612', 99)])",
    '# Taxid strings',
    "case('T01_semicolon_taxid_top_hit', [row('OTU', '9606;9598', 100), row('OTU', A, 98.5)])",
    "case('T02_NA_taxid_top_hit', [row('OTU', 'N/A', 100), row('OTU', A, 98.5)])",
    "case('T03_semicolon_taxid_tie', [row('OTU', '9606;9598', 99), row('OTU', '9606', 99)])",
    '# Coverage and identity rules',
    "case('Q01_lower_coverage_removed_despite_higher_identity', [row('OTU', '9606', 100, qcov=95), row('OTU', A, 97, qcov=100)], params='90 97 1')",
    "case('Q02_identity_tie', [row('OTU', '9606', 99), row('OTU', A, 99)])",
    "case('Q03_neighbour_chain', [row('OTU', '9606', 100), row('OTU', '9598', 99.5), row('OTU', A, 99), row('OTU', '562', 98.5)])",
    '# Identity-difference thresholds (text comparison)',
    "case('D00_diff0', [row('OTU', '9606', 99.5), row('OTU', A, 99)], params='100 97 0')",
    "case('D01_diff1_floor80_gap14', [row('OTU', '9606', 99), row('OTU', A, 85)], params='100 80 1')",
    "case('D02_diff2_floor80_gap14', [row('OTU', '9606', 99), row('OTU', A, 85)], params='100 80 2')",
    "case('D02b_diff2_floor97_gap2.5', [row('OTU', '9606', 99.5), row('OTU', A, 97)], params='100 97 2')",
    "case('D09_diff9_floor80_gap14', [row('OTU', '9606', 99), row('OTU', A, 85)], params='100 80 9')",
    "case('D09b_diff9_floor80_gap9.5', [row('OTU', '9606', 99), row('OTU', A, 89.5)], params='100 80 9')",
    "case('D10_diff10_floor97_gap2', [row('OTU', '9606', 99), row('OTU', A, 97)], params='100 97 10')",
    "case('D10b_diff10_floor80_gap14', [row('OTU', '9606', 99), row('OTU', A, 85)], params='100 80 10')",
    '# Table handling',
    "case('O01_row_order', [row('OTU_A', A, 99), row('OTU_B', '9606', 99)], feats=['OTU_B', 'OTU_A'])",
    "case('M01_blast_feature_missing_from_table', [row('OTU_A', A, 99), row('OTU_Z', '9606', 99)], feats=['OTU_A'])",
    "case('M02_duplicate_table_ids', [row('OTU_A', A, 99)], raw_feats='#ID\\tS1\\nOTU_A\\t5\\nOTU_A\\t9\\n')",
    '# Parsing',
    'case(\'P02_embedded_quote\', [row(\'OTU\', \'9606\', 99, title=\'Homo sapiens 16S "partial" sequence\'), row(\'OTU\', A, 99)])',
    "case('P03_tab_inside_title', [row('OTU', '9606', 99, qcov=90, title='Homo\\tsapiens clone'), row('OTU', A, 99)])",
    "rows = [row('OTU_A', A, 99), row('OTU_A', '9606', 99), row('OTU_B', A, 99)]",
    "case('P04_blank_line', rows, raw_blast=rows[0] + '\\n\\n' + rows[1] + '\\n' + rows[2] + '\\n')",
    "case('P05_CRLF', rows, raw_blast='\\r\\n'.join(rows) + '\\r\\n', raw_feats='#ID\\tS1\\r\\nOTU_A\\t5\\r\\nOTU_B\\t3\\r\\n')",
    "case('P06_BOM_on_blast', rows, raw_blast='\ufeff' + '\\n'.join(rows) + '\\n')",
    "short = '\\t'.join(rows[2].split('\\t')[:20])",
    "case('P07_short_blast_row', rows, raw_blast='\\n'.join(rows[:2] + [short]) + '\\n')",
    "case('P08_ragged_table_row', rows, raw_feats='#ID\\tS1\\tS2\\nOTU_A\\t5\\t6\\nOTU_B\\t3\\n')",
    'case(\'P09_quoted_table_R_style\', rows, raw_feats=\'"#ID"\\t"S1"\\n"OTU_A"\\t"5"\\n"OTU_B"\\t"3"\\n\')',
    "case('P10_table_quote_spans_rows', [row('OTU_A', A, 99), row('OTU_B', '9606', 99), row('OTU_C', A, 99)],",
    '     raw_feats=\'#ID\\tS1\\n"OTU_A\\t5\\nOTU_B\\t3\\nOTU_C"\\t7\\n\')',
    "print('cases written to', OUT)",
    '',
), '47db371e0e4c6d27045fc846a522d90626d9a2fa58171cced9d5b57280b979bb')

# ---- scripts/parity_checks.py ------------------------------------------------------------------
FILES['scripts/parity_checks.py'] = (L(
    'import sys, csv, collections',
    'P, O = sys.argv[1], sys.argv[2]',
    'tax = {}',
    "for line in open(f'{P}/rankedlineage_subset_2026-11-05.dmp', encoding='utf-8'):",
    "    p = [x.strip() for x in line.rstrip('\\r\\n').split('|')]",
    '    tax[p[0]] = p',
    'infra = {t for t, p in tax.items() if p[2]}',
    'oneword = {t for t, p in tax.items() if len(p[1].split()) == 1}',
    "used = [r for r in csv.reader(open(f'{O}/h.tsv'), delimiter='\\t')][1:]",
    'used_taxids = {r[2] for r in used}',
    "print('taxa in subset:', len(tax), '| with non-empty species field (below species):', len(infra), '| used in filtered hits:', len(infra & used_taxids))",
    "print('one-word tax_name (likely above species):', len(oneword), sorted(tax[t][1] for t in oneword)[:10], '| used:', len(oneword & used_taxids))",
    "rows = [l.rstrip('\\r\\n').split('\\t') for l in open(f'{P}/blastResult_2test_LCAscript.tab', encoding='utf-8') if l.strip()]",
    "print('BLAST rows:', len(rows), '| column counts:', collections.Counter(len(r) for r in rows))",
    'order = [r[0] for r in rows]',
    'blocks = [k for i, k in enumerate(order) if i == 0 or order[i-1] != k]',
    "print('features:', len(set(order)), '| contiguous blocks:', len(blocks), '| non-contiguous features:', len(blocks) - len(set(order)))",
    "semi = [(r[0], r[2], r[6], r[20]) for r in rows if ';' in r[2] or r[2] == 'N/A']",
    "print('semicolon or N/A taxid rows:', len(semi), semi[:6])",
    'print(\'rows containing a double quote:\', sum(\'"\' in l for l in open(f\'{P}/blastResult_2test_LCAscript.tab\', encoding=\'utf-8\')))',
    "print('distinct sscinames/scomnames values:', collections.Counter(r[3] for r in rows).most_common(2), collections.Counter(r[4] for r in rows).most_common(2))",
    "print('qcov values:', collections.Counter(r[20] for r in rows).most_common(4))",
    'dom = collections.defaultdict(set)',
    'for r in used:',
    '    if r[2] in tax: dom[r[0]].add(tax[r[2]][9])',
    "print('features with cross-domain usable hits:', sum(len(v) > 1 for v in dom.values()))",
    '',
), 'dde6409c2b1f470577d21f2ede5356bc8e3ee76ad259772d651020691a57782f')

# ---- scripts/run_all.sh ------------------------------------------------------------------------
FILES['scripts/run_all.sh'] = (L(
    '#!/bin/bash',
    '# Run every case in cases/set1 and cases/set2, then write results/results.tsv and results/console_output.txt.',
    '#',
    '# Usage: run_all.sh UPSTREAM_DIR SRC_DIR',
    '#   UPSTREAM_DIR  folder holding the upstream scripts (see run_both.sh)',
    "#   SRC_DIR       the ednaflow-lca repository's src folder",
    '#',
    '# Run it on a working copy of this harness: it writes up/ and sa/ output folders into every case folder.',
    'set -u',
    'here=$(cd "$(dirname "$0")/.." && pwd)',
    'up=$(cd "$1" && pwd); src=$(cd "$2" && pwd)',
    'mkdir -p "$here/results"',
    'for set in set1 set2; do',
    '    for d in "$here/cases/$set"/*/; do',
    '        bash "$here/scripts/run_both.sh" "${d%/}" "$up" "$src"',
    '    done',
    'done > "$here/results/console_output.txt" 2>&1',
    'python3 -I "$here/scripts/summarise.py" "$here/cases" > "$here/results/results.tsv"',
    'echo "Wrote $here/results/results.tsv and $here/results/console_output.txt"',
    '',
), 'dcbc14f179e9860d497e9584637bfb105bb00722b4f457fa5f4bb60753d5a573')

# ---- scripts/run_both.sh -----------------------------------------------------------------------
FILES['scripts/run_both.sh'] = (L(
    '#!/bin/bash',
    '# Run upstream eDNAFlow LCA and the ednaflow-lca CLI on one case folder, side by side.',
    '#',
    '# Usage: run_both.sh CASE_DIR UPSTREAM_DIR SRC_DIR',
    '#   CASE_DIR      a case folder holding blast.tsv, features.tsv and optionally params ("qcov pident diff");',
    '#                 its parent folder must hold rankedlineage.dmp',
    '#   UPSTREAM_DIR  folder holding the upstream scripts, either as named upstream',
    '#                 (runAssign_collapsedTaxonomy.py, working_function.py) or as vendored in the',
    '#                 ednaflow-lca repository (upstream_runAssign_collapsedTaxonomy.py, upstream_working_function.py)',
    "#   SRC_DIR       the ednaflow-lca repository's src folder (holds the ednaflow_lca package)",
    '#',
    '# Upstream runs inside CASE_DIR/up with wget and unzip replaced by stubs that exit 1, so it cannot',
    "# download anything; it then uses the rankedlineage.dmp copied into that folder. Upstream's own shell",
    '# step runs mkdir, mv, tr and rm inside CASE_DIR/up only. Results go to CASE_DIR/up and CASE_DIR/sa.',
    'set -u',
    'case=$1; up=$2; src=$3',
    'read qcov pid diff < <(cat "$case/params" 2>/dev/null || echo "100 97 1")',
    'rm -rf "$case/up" "$case/sa"; mkdir -p "$case/up/bin" "$case/sa"',
    'for name in runAssign_collapsedTaxonomy.py working_function.py; do',
    '    if [ -f "$up/$name" ]; then cp "$up/$name" "$case/up/$name"',
    '    elif [ -f "$up/upstream_$name" ]; then cp "$up/upstream_$name" "$case/up/$name"',
    '    else echo "cannot find $name or upstream_$name in $up" >&2; exit 1; fi',
    'done',
    'printf \'#!/bin/sh\\nexit 1\\n\' > "$case/up/bin/wget"; printf \'#!/bin/sh\\nexit 1\\n\' > "$case/up/bin/unzip"; chmod +x "$case/up/bin/"*',
    'cp "$case/../rankedlineage.dmp" "$case/up/rankedlineage.dmp"',
    '(cd "$case/up" && env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY PATH="$PWD/bin:$PATH" \\',
    '    python3 runAssign_collapsedTaxonomy.py ../features.tsv ../blast.tsv $qcov $pid $diff out.tsv > run.log 2>&1',
    ' echo "upstream exit $?" >> run.log)',
    'python3 -I -c "import sys; sys.path.insert(0, sys.argv[1]); from ednaflow_lca.cli import main; main(sys.argv[2:])" "$src" \\',
    '  --feature-table "$case/features.tsv" --blast-results "$case/blast.tsv" --taxonomy "$case/../rankedlineage.dmp" \\',
    '  --query-coverage $qcov --percent-identity $pid --identity-difference $diff \\',
    '  --assignments "$case/sa/a.tsv" --filtered-hits "$case/sa/h.tsv" --summary "$case/sa/s.tsv" > "$case/sa/run.log" 2>&1',
    'echo "standalone exit $?" >> "$case/sa/run.log"',
    'echo "=== $(basename "$case")  (qcov $qcov, pident $pid, difference $diff)"',
    'echo "upstream:";   (tail -n +2 "$case/up/out.tsv" 2>/dev/null | cut -f1-9) ; grep -h "exit\\|Error\\|error" "$case/up/run.log" | grep -v "mv: cannot stat" | tail -2',
    'echo "standalone:"; (tail -n +2 "$case/sa/a.tsv" 2>/dev/null | cut -f1-9) ; grep -h "exit\\|rror" "$case/sa/run.log" | tail -2',
    '',
), '5a8c7f93aba75a707c0340707c7bb1530841e9e4bf08a806ae330ee716b4c58d')

# ---- scripts/species_rule_check.py -------------------------------------------------------------
FILES['scripts/species_rule_check.py'] = (L(
    'import sys, csv, collections',
    'sys.path.insert(0, sys.argv[1])',
    'from ednaflow_lca.cli import lca',
    'P, O = sys.argv[2], sys.argv[3]',
    'tax = {}',
    "for line in open(f'{P}/rankedlineage_subset_2026-11-05.dmp', encoding='utf-8'):",
    "    p = [x.strip() for x in line.rstrip('\\r\\n').split('|')]",
    '    tax[p[0]] = p',
    'def lineage(t, rule):',
    '    p = tax[t]',
    "    sp = (p[2] or p[1]) if rule == 'species_field' else p[1]",
    '    return (p[9] or p[8], p[7], p[6], p[5], p[4], p[3], sp)',
    'hits = collections.defaultdict(list)',
    "for r in list(csv.reader(open(f'{O}/h.tsv'), delimiter='\\t'))[1:]:",
    '    hits[r[0]].append(r[2])',
    'for t, p in tax.items():',
    "    if p[2]: print('infraspecific taxon in fixture:', t, '|', p[1], '| species field:', p[2])",
    'changed = 0',
    'for f, ts in hits.items():',
    "    a, b = lca([lineage(t, 'tax_name') for t in ts]), lca([lineage(t, 'species_field') for t in ts])",
    '    if a != b:',
    "        changed += 1; print('changes:', f, a[-2:], '->', b[-2:])",
    "print('features whose assignment would change under a species-field rule:', changed, 'of', len(hits))",
    '',
), 'f7dd15a42ada80e2544a2e96af5477080fb636354ec99601507221a18bca2d54')

# ---- scripts/summarise.py ----------------------------------------------------------------------
FILES['scripts/summarise.py'] = (L(
    '"""Summarise upstream and ednaflow-lca results for every case folder, as a tab-separated table.',
    '',
    'Usage: python3 -I summarise.py CASES_DIR > results.tsv',
    '',
    'For each case and feature it reports the lowest rank that is neither empty nor "dropped", for upstream',
    'and for ednaflow-lca, the exit status of each, and whether the two full seven-rank lineages agree.',
    '"""',
    'import sys',
    'from pathlib import Path',
    '',
    "RANKS = ['domain', 'phylum', 'class', 'order', 'family', 'genus', 'species']",
    '',
    '',
    'def read_rows(path):',
    '    if not path.exists():',
    '        return None',
    '    rows = {}',
    "    lines = path.read_text(encoding='utf-8', errors='replace').splitlines()",
    '    for line in lines[1:]:',
    "        p = line.split('\\t')",
    '        if len(p) < 8:',
    '            continue',
    '        rows.setdefault(p[7], []).append(tuple(p[:7]))',
    '    return rows',
    '',
    '',
    'def label(lineages):',
    '    if not lineages:',
    "        return 'absent'",
    '    out = []',
    '    for lin in lineages:',
    "        best = 'nothing assigned'",
    '        for rank, value in zip(RANKS, lin):',
    "            if value and value != 'dropped':",
    "                best = f'{rank} {value}'",
    '        blanks = [r for r, v in zip(RANKS, lin) if not v]',
    '        out.append(best + (f\' (blank: {",".join(blanks)})\' if blanks else \'\'))',
    "    return ' | '.join(out) + (f'  [{len(lineages)} rows]' if len(lineages) > 1 else '')",
    '',
    '',
    'def exit_status(log):',
    '    if not log.exists():',
    "        return 'not run'",
    "    for line in reversed(log.read_text(encoding='utf-8', errors='replace').splitlines()):",
    "        if ' exit ' in line:",
    '            return line.split()[-1]',
    "    return '?'",
    '',
    '',
    'def last_error(log):',
    '    if not log.exists():',
    "        return ''",
    "    lines = [l for l in log.read_text(encoding='utf-8', errors='replace').splitlines()",
    "             if ('rror' in l) and 'mv: cannot stat' not in l]",
    "    return lines[-1].strip()[:120] if lines else ''",
    '',
    '',
    "print('\\t'.join(['set', 'case', 'thresholds (qcov pident diff)', 'feature', 'upstream result', 'upstream exit',",
    "                 'ednaflow-lca result', 'ednaflow-lca exit', 'agree', 'error messages']))",
    "for case in sorted(Path(sys.argv[1]).glob('set*/*/')):",
    "    params = (case / 'params').read_text().strip() if (case / 'params').exists() else '100 97 1'",
    "    up, sa = read_rows(case / 'up' / 'out.tsv') or {}, read_rows(case / 'sa' / 'a.tsv') or {}",
    "    ue, se = exit_status(case / 'up' / 'run.log'), exit_status(case / 'sa' / 'run.log')",
    "    errors = ' / '.join(x for x in (last_error(case / 'up' / 'run.log'), last_error(case / 'sa' / 'run.log')) if x)",
    "    features = sorted(set(up) | set(sa)) or ['(no rows)']",
    '    for f in features:',
    "        agree = 'yes' if (up.get(f) == sa.get(f) and ue == se) else 'NO'",
    "        print('\\t'.join([case.parent.name, case.name, params, f, label(up.get(f)), ue, label(sa.get(f)), se, agree, errors]))",
    '',
), '88c7a0b1fdcf65351cadaa52f31353ce12373dd0c35d8016b4a4031adaf3d4b0')

# ---- cases/set1/A_exclusion_via_taxonomy_name/blast.tsv ----------------------------------------
FILES['cases/set1/A_exclusion_via_taxonomy_name/blast.tsv'] = (L(
    'OTU_A\ts_OTU_A_100272_99\t100272\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_A\ts_OTU_A_38775_98.5\t38775\tN/A\tN/A\tN/A\t98.5\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), 'b1f9e54299e10d58784ace5a874b0a66967e96963982426cfe56d2dec09a5346')

# ---- cases/set1/A_exclusion_via_taxonomy_name/features.tsv -------------------------------------
FILES['cases/set1/A_exclusion_via_taxonomy_name/features.tsv'] = (L(
    '#ID\tS1',
    'OTU_A\t5',
    '',
), 'c3d7f546083812526b867f22b8840349d8e805b92638477c1c0c20581cc307cd')

# ---- cases/set1/B_eukaryote_marine_clone/blast.tsv ---------------------------------------------
FILES['cases/set1/B_eukaryote_marine_clone/blast.tsv'] = (L(
    'OTU_B\ts_OTU_B_9606_99\t9606\tN/A\teukaryote marine clone ABC1\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_B\ts_OTU_B_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '9dba7a876949500a0d576a624888a864bc60b8fdad16d0e6a036e9ca14a5d83c')

# ---- cases/set1/B_eukaryote_marine_clone/features.tsv ------------------------------------------
FILES['cases/set1/B_eukaryote_marine_clone/features.tsv'] = (L(
    '#ID\tS1',
    'OTU_B\t5',
    '',
), '971a80a62cba097d68cf9b75f2cf612dcc42e735029531e73d7d3dc16b3be3a7')

# ---- cases/set1/C_case_of_excluded_term/blast.tsv ----------------------------------------------
FILES['cases/set1/C_case_of_excluded_term/blast.tsv'] = (L(
    'OTU_C\ts_OTU_C_9606_99\t9606\tN/A\tUncultured bacterium\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_C\ts_OTU_C_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '1125b8864860d93ce3770f355ab21cdc60c50026f377e455a0c040a0ee0e6111')

# ---- cases/set1/C_case_of_excluded_term/features.tsv -------------------------------------------
FILES['cases/set1/C_case_of_excluded_term/features.tsv'] = (L(
    '#ID\tS1',
    'OTU_C\t5',
    '',
), '45da7f6675b3b09ef9b587ba4868c630016d5267a5eee4ec31e2cd4929746cb1')

# ---- cases/set1/D_strain_and_species/blast.tsv -------------------------------------------------
FILES['cases/set1/D_strain_and_species/blast.tsv'] = (L(
    'OTU_D\ts_OTU_D_562_99\t562\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_D\ts_OTU_D_83333_99\t83333\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '06d6f9c31b4977c24b59096fa48f028ebaa9a2b037fb44a846c5d072d6879e22')

# ---- cases/set1/D_strain_and_species/features.tsv ----------------------------------------------
FILES['cases/set1/D_strain_and_species/features.tsv'] = (L(
    '#ID\tS1',
    'OTU_D\t5',
    '',
), '18045872e1bb35cb5069cfa9e88445dd2f5c104ae0270b071fc12a2c385d023c')

# ---- cases/set1/E_domain_conflict/blast.tsv ----------------------------------------------------
FILES['cases/set1/E_domain_conflict/blast.tsv'] = (L(
    'OTU_E\ts_OTU_E_562_99\t562\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_E\ts_OTU_E_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '10279bc80f3f17dbb7f9c15ced1e1b2950dd3880ce99db40f90cd7ea5e678041')

# ---- cases/set1/E_domain_conflict/features.tsv -------------------------------------------------
FILES['cases/set1/E_domain_conflict/features.tsv'] = (L(
    '#ID\tS1',
    'OTU_E\t5',
    '',
), 'ed173a3f7e6a9a3ed09fa4038f7d2e2d3af2cf77adb9697afe89840ff80e7ddb')

# ---- cases/set1/F_non_contiguous_feature/blast.tsv ---------------------------------------------
FILES['cases/set1/F_non_contiguous_feature/blast.tsv'] = (L(
    'OTU_F\ts_OTU_F_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_X\ts_OTU_X_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_F\ts_OTU_F_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '59e88ea04552dc81c0c88a27933b4670b3d82341e453021a28226750e574272d')

# ---- cases/set1/F_non_contiguous_feature/features.tsv ------------------------------------------
FILES['cases/set1/F_non_contiguous_feature/features.tsv'] = (L(
    '#ID\tS1',
    'OTU_F\t5',
    'OTU_X\t5',
    '',
), '64f8e4b84a0cb5b4ee25208fd75416c81abb7da8fc26bf9e8ca0bf9fcf844a8a')

# ---- cases/set1/G_text_comparison_of_difference/blast.tsv --------------------------------------
FILES['cases/set1/G_text_comparison_of_difference/blast.tsv'] = (L(
    'OTU_G\ts_OTU_G_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_G\ts_OTU_G_38775_85\t38775\tN/A\tN/A\tN/A\t85\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '84b457bb8ae4cffbb8d08441fb9b35d45fe5b2a5bb3f6d61a1ae26d639721e0c')

# ---- cases/set1/G_text_comparison_of_difference/features.tsv -----------------------------------
FILES['cases/set1/G_text_comparison_of_difference/features.tsv'] = (L(
    '#ID\tS1',
    'OTU_G\t5',
    '',
), '95b3059734a3c335a5d1cf13029845a1f1b10e242ee96d96b87c72e433121fec')

# ---- cases/set1/G_text_comparison_of_difference/params -----------------------------------------
FILES['cases/set1/G_text_comparison_of_difference/params'] = (L(
    '100 80 3',
), 'd2bee9f5c0184150c54dd5c0855f1981a312f326d3a1d73c4a16f4f106209776')

# ---- cases/set1/H_empty_superkingdom/blast.tsv -------------------------------------------------
FILES['cases/set1/H_empty_superkingdom/blast.tsv'] = (L(
    'OTU_H\ts_OTU_H_999999_99\t999999\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '87efaa730ce1cb53f8401903bece963140d88f7af900bf5f3946f204be80b06f')

# ---- cases/set1/H_empty_superkingdom/features.tsv ----------------------------------------------
FILES['cases/set1/H_empty_superkingdom/features.tsv'] = (L(
    '#ID\tS1',
    'OTU_H\t5',
    '',
), '032aa20ea0672e49f6432d73fea65f5966e099ae51c6909122bc16bd3aba6795')

# ---- cases/set1/I_quote_in_title/blast.tsv -----------------------------------------------------
FILES['cases/set1/I_quote_in_title/blast.tsv'] = (L(
    'OTU_I\ts_OTU_I_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t"Homo sapiens clone 7\t1e-50\t200\t100\t100',
    'OTU_I\ts_OTU_I_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_I2\ts_OTU_I2_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '920d8d3612b3f2bc2288a3ae325c55824c5238673a77f603cbae7dfb0d8bfed1')

# ---- cases/set1/I_quote_in_title/features.tsv --------------------------------------------------
FILES['cases/set1/I_quote_in_title/features.tsv'] = (L(
    '#ID\tS1',
    'OTU_I\t5',
    'OTU_I2\t3',
    '',
), '7fa03f4c63e4dba52060b30daf8c4c74d5c29e4f172d401be378614e071522ac')

# ---- cases/set1/J_first_hit_per_taxid/blast.tsv ------------------------------------------------
FILES['cases/set1/J_first_hit_per_taxid/blast.tsv'] = (L(
    'OTU_J\ts_OTU_J_9606_90\t9606\tN/A\tN/A\tN/A\t90\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_J\ts_OTU_J_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_J\ts_OTU_J_38775_98.5\t38775\tN/A\tN/A\tN/A\t98.5\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '75d50443832429231bc7bc48951c93fe1382b8e4ee55b9326df2a993d37f8c64')

# ---- cases/set1/J_first_hit_per_taxid/features.tsv ---------------------------------------------
FILES['cases/set1/J_first_hit_per_taxid/features.tsv'] = (L(
    '#ID\tS1',
    'OTU_J\t5',
    '',
), 'b7ca3ebd29992852bb71dbd74f868686eac6340fc9f657a9a9ceff16957b09a6')

# ---- cases/set1/K_synthetic_construct_second/blast.tsv -----------------------------------------
FILES['cases/set1/K_synthetic_construct_second/blast.tsv'] = (L(
    'OTU_K\ts_OTU_K_9606\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_K\ts_OTU_K_32630\t32630\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_K\ts_OTU_K_38775\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '1ce3bf14e0664dc3c065d865138f2cfa00e422951fcc639bf74a28ccbe12134e')

# ---- cases/set1/K_synthetic_construct_second/features.tsv --------------------------------------
FILES['cases/set1/K_synthetic_construct_second/features.tsv'] = (L(
    '#ID\tS1',
    'OTU_K\t5',
    '',
), '05e8c1fadefe4ae25f6e7a71d64d3e2f4c39bcc41e67aa3008583b46b2141585')

# ---- cases/set1/L_synthetic_construct_first/blast.tsv ------------------------------------------
FILES['cases/set1/L_synthetic_construct_first/blast.tsv'] = (L(
    'OTU_L\ts_OTU_L_32630\t32630\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_L\ts_OTU_L_9606\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '5f73b956c730280c81117a71b4f06af229f0660f272875d0f2225c3308f5ee73')

# ---- cases/set1/L_synthetic_construct_first/features.tsv ---------------------------------------
FILES['cases/set1/L_synthetic_construct_first/features.tsv'] = (L(
    '#ID\tS1',
    'OTU_L\t5',
    '',
), '237d3ea5553ab39a525da8b7d978b93ce57b370cb3f54d3bdfbf607256a5b03f')

# ---- cases/set1/M_quote_merges_rows/blast.tsv --------------------------------------------------
FILES['cases/set1/M_quote_merges_rows/blast.tsv'] = (L(
    'OTU1\ts_OTU1_9606\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t100\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t"Quoted strain title\t1e-50\t200\t100\t100',
    'OTU1\ts_OTU1_38775\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t100\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tordinary title\t1e-50\t200\t100\t100',
    'OTU2\ts_OTU2_562\t562\tN/A\tN/A\tN/A\t99\t100\t100\t100\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tanother title\t1e-50\t200\t100\t100',
    'OTU3\ts_OTU3_562\t562\tN/A\tN/A\tN/A\t99\t100\t100\t100\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\ttitle with a "quote" inside\t1e-50\t200\t100\t100',
    '',
), 'c226cb492b3a590c74337ca79bdbc425a8b42cd84a77690295d7b06b42c1ff65')

# ---- cases/set1/M_quote_merges_rows/features.tsv -----------------------------------------------
FILES['cases/set1/M_quote_merges_rows/features.tsv'] = (L(
    '#ID\tS1',
    'OTU1\t5',
    'OTU2\t7',
    'OTU3\t9',
    '',
), 'bee4d13b1fe6e63d78945983d704f8a7960190f14449549a2dbe12b17828d121')

# ---- cases/set1/rankedlineage.dmp --------------------------------------------------------------
FILES['cases/set1/rankedlineage.dmp'] = (L(
    '38775\t|\tAntechinus flavipes\t|\t\t|\tAntechinus\t|\tDasyuridae\t|\tDasyuromorphia\t|\tMammalia\t|\tChordata\t|\tMetazoa\t|\tEukaryota\t|',
    '100272\t|\tuncultured eukaryote\t|\t\t|\t\t|\t\t|\t\t|\t\t|\t\t|\t\t|\tEukaryota\t|',
    '9606\t|\tHomo sapiens\t|\t\t|\tHomo\t|\tHominidae\t|\tPrimates\t|\tMammalia\t|\tChordata\t|\tMetazoa\t|\tEukaryota\t|',
    '562\t|\tEscherichia coli\t|\t\t|\tEscherichia\t|\tEnterobacteriaceae\t|\tEnterobacterales\t|\tGammaproteobacteria\t|\tPseudomonadota\t|\tPseudomonadati\t|\tBacteria\t|',
    '83333\t|\tEscherichia coli K-12\t|\tEscherichia coli\t|\tEscherichia\t|\tEnterobacteriaceae\t|\tEnterobacterales\t|\tGammaproteobacteria\t|\tPseudomonadota\t|\tPseudomonadati\t|\tBacteria\t|',
    '999999\t|\tTest virus\t|\t\t|\tTestvirus\t|\tTestviridae\t|\tTestvirales\t|\tTestviricetes\t|\tTestviricota\t|\tTestvirae\t|\t\t|',
    '32630\t|\tsynthetic construct\t|\t\t|\t\t|\t\t|\t\t|\t\t|\t\t|\t\t|\t\t|',
    '',
), '7ede896d4dc4e711b0d093230cfccd4235b1702141fbc52b30e2d13b8e1428a8')

# ---- cases/set2/D00_diff0/blast.tsv ------------------------------------------------------------
FILES['cases/set2/D00_diff0/blast.tsv'] = (L(
    'OTU\ts_OTU_9606_99.5\t9606\tN/A\tN/A\tN/A\t99.5\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU\ts_OTU_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '3eb1cbfc38c9a796bb9d6195cfcd7a9f9cc22ca3c4f9726b40eec48b2b72ded1')

# ---- cases/set2/D00_diff0/features.tsv ---------------------------------------------------------
FILES['cases/set2/D00_diff0/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    '',
), '876af60bbd221585bce5c3ae604035145ee0d2a7486037f951d3304a761d3978')

# ---- cases/set2/D00_diff0/params ---------------------------------------------------------------
FILES['cases/set2/D00_diff0/params'] = (L(
    '100 97 0',
    '',
), 'daaedc927da6fb13b9a5a7ae111b57556d782387275a173110e2fb6e01bbbef9')

# ---- cases/set2/D01_diff1_floor80_gap14/blast.tsv ----------------------------------------------
FILES['cases/set2/D01_diff1_floor80_gap14/blast.tsv'] = (L(
    'OTU\ts_OTU_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU\ts_OTU_38775_85\t38775\tN/A\tN/A\tN/A\t85\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), 'f74926376ae52b8d5d537003581f61cf427dd30223ac3bd429fa497ef02c9603')

# ---- cases/set2/D01_diff1_floor80_gap14/features.tsv -------------------------------------------
FILES['cases/set2/D01_diff1_floor80_gap14/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    '',
), '876af60bbd221585bce5c3ae604035145ee0d2a7486037f951d3304a761d3978')

# ---- cases/set2/D01_diff1_floor80_gap14/params -------------------------------------------------
FILES['cases/set2/D01_diff1_floor80_gap14/params'] = (L(
    '100 80 1',
    '',
), 'c58c5d372f00d9fadf5f698de529f73d9366ac265936dcf1caf4a569150c6ef8')

# ---- cases/set2/D02_diff2_floor80_gap14/blast.tsv ----------------------------------------------
FILES['cases/set2/D02_diff2_floor80_gap14/blast.tsv'] = (L(
    'OTU\ts_OTU_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU\ts_OTU_38775_85\t38775\tN/A\tN/A\tN/A\t85\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), 'f74926376ae52b8d5d537003581f61cf427dd30223ac3bd429fa497ef02c9603')

# ---- cases/set2/D02_diff2_floor80_gap14/features.tsv -------------------------------------------
FILES['cases/set2/D02_diff2_floor80_gap14/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    '',
), '876af60bbd221585bce5c3ae604035145ee0d2a7486037f951d3304a761d3978')

# ---- cases/set2/D02_diff2_floor80_gap14/params -------------------------------------------------
FILES['cases/set2/D02_diff2_floor80_gap14/params'] = (L(
    '100 80 2',
    '',
), '0d1712f73251fb82e51301b49f202ebf5d7a63657a0563091c16f7adde176127')

# ---- cases/set2/D02b_diff2_floor97_gap2.5/blast.tsv --------------------------------------------
FILES['cases/set2/D02b_diff2_floor97_gap2.5/blast.tsv'] = (L(
    'OTU\ts_OTU_9606_99.5\t9606\tN/A\tN/A\tN/A\t99.5\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU\ts_OTU_38775_97\t38775\tN/A\tN/A\tN/A\t97\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), 'bedaab60ae24c9f1eed4a5c89c4e8508f992e043fe05d6a2eabc27eb91fdaeff')

# ---- cases/set2/D02b_diff2_floor97_gap2.5/features.tsv -----------------------------------------
FILES['cases/set2/D02b_diff2_floor97_gap2.5/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    '',
), '876af60bbd221585bce5c3ae604035145ee0d2a7486037f951d3304a761d3978')

# ---- cases/set2/D02b_diff2_floor97_gap2.5/params -----------------------------------------------
FILES['cases/set2/D02b_diff2_floor97_gap2.5/params'] = (L(
    '100 97 2',
    '',
), '89d30c8c1ce5ede7e1e957396b07edfed64494e76e60ce5f1413cd4c6d96adb3')

# ---- cases/set2/D09_diff9_floor80_gap14/blast.tsv ----------------------------------------------
FILES['cases/set2/D09_diff9_floor80_gap14/blast.tsv'] = (L(
    'OTU\ts_OTU_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU\ts_OTU_38775_85\t38775\tN/A\tN/A\tN/A\t85\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), 'f74926376ae52b8d5d537003581f61cf427dd30223ac3bd429fa497ef02c9603')

# ---- cases/set2/D09_diff9_floor80_gap14/features.tsv -------------------------------------------
FILES['cases/set2/D09_diff9_floor80_gap14/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    '',
), '876af60bbd221585bce5c3ae604035145ee0d2a7486037f951d3304a761d3978')

# ---- cases/set2/D09_diff9_floor80_gap14/params -------------------------------------------------
FILES['cases/set2/D09_diff9_floor80_gap14/params'] = (L(
    '100 80 9',
    '',
), 'dcb059d47fc570c2b330762144181db5d850bff6c50089bec37cca80a54f0cab')

# ---- cases/set2/D09b_diff9_floor80_gap9.5/blast.tsv --------------------------------------------
FILES['cases/set2/D09b_diff9_floor80_gap9.5/blast.tsv'] = (L(
    'OTU\ts_OTU_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU\ts_OTU_38775_89.5\t38775\tN/A\tN/A\tN/A\t89.5\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '071ac35682d04f5512de947881bb866a4bee6726bcee85c4f4d6434087ee0590')

# ---- cases/set2/D09b_diff9_floor80_gap9.5/features.tsv -----------------------------------------
FILES['cases/set2/D09b_diff9_floor80_gap9.5/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    '',
), '876af60bbd221585bce5c3ae604035145ee0d2a7486037f951d3304a761d3978')

# ---- cases/set2/D09b_diff9_floor80_gap9.5/params -----------------------------------------------
FILES['cases/set2/D09b_diff9_floor80_gap9.5/params'] = (L(
    '100 80 9',
    '',
), 'dcb059d47fc570c2b330762144181db5d850bff6c50089bec37cca80a54f0cab')

# ---- cases/set2/D10_diff10_floor97_gap2/blast.tsv ----------------------------------------------
FILES['cases/set2/D10_diff10_floor97_gap2/blast.tsv'] = (L(
    'OTU\ts_OTU_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU\ts_OTU_38775_97\t38775\tN/A\tN/A\tN/A\t97\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), 'c0d88c6b5f9e2169f85e2578d0059c99750c154834ab6141f5cb518e53f67cbd')

# ---- cases/set2/D10_diff10_floor97_gap2/features.tsv -------------------------------------------
FILES['cases/set2/D10_diff10_floor97_gap2/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    '',
), '876af60bbd221585bce5c3ae604035145ee0d2a7486037f951d3304a761d3978')

# ---- cases/set2/D10_diff10_floor97_gap2/params -------------------------------------------------
FILES['cases/set2/D10_diff10_floor97_gap2/params'] = (L(
    '100 97 10',
    '',
), '637f742accc39b6dd77e67cabfb2ce94d2a6c5088363921f9386a474a3b964b5')

# ---- cases/set2/D10b_diff10_floor80_gap14/blast.tsv --------------------------------------------
FILES['cases/set2/D10b_diff10_floor80_gap14/blast.tsv'] = (L(
    'OTU\ts_OTU_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU\ts_OTU_38775_85\t38775\tN/A\tN/A\tN/A\t85\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), 'f74926376ae52b8d5d537003581f61cf427dd30223ac3bd429fa497ef02c9603')

# ---- cases/set2/D10b_diff10_floor80_gap14/features.tsv -----------------------------------------
FILES['cases/set2/D10b_diff10_floor80_gap14/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    '',
), '876af60bbd221585bce5c3ae604035145ee0d2a7486037f951d3304a761d3978')

# ---- cases/set2/D10b_diff10_floor80_gap14/params -----------------------------------------------
FILES['cases/set2/D10b_diff10_floor80_gap14/params'] = (L(
    '100 80 10',
    '',
), '95d353883f6d8133b1b8e06944876ecc7edc2a85fc7275f7688c180f2119734f')

# ---- cases/set2/M01_blast_feature_missing_from_table/blast.tsv ---------------------------------
FILES['cases/set2/M01_blast_feature_missing_from_table/blast.tsv'] = (L(
    'OTU_A\ts_OTU_A_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_Z\ts_OTU_Z_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), 'ba0ba93190bf374d4cd951b2c90b36d5eb73c08a2c10dcd22d46c03d80c373c5')

# ---- cases/set2/M01_blast_feature_missing_from_table/features.tsv ------------------------------
FILES['cases/set2/M01_blast_feature_missing_from_table/features.tsv'] = (L(
    '#ID\tS1',
    'OTU_A\t5',
    '',
), 'c3d7f546083812526b867f22b8840349d8e805b92638477c1c0c20581cc307cd')

# ---- cases/set2/M02_duplicate_table_ids/blast.tsv ----------------------------------------------
FILES['cases/set2/M02_duplicate_table_ids/blast.tsv'] = (L(
    'OTU_A\ts_OTU_A_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '68bc09cc75e10cfa1820a401a6708e4b711b377d3ee02c8456091fe3d245c436')

# ---- cases/set2/M02_duplicate_table_ids/features.tsv -------------------------------------------
FILES['cases/set2/M02_duplicate_table_ids/features.tsv'] = (L(
    '#ID\tS1',
    'OTU_A\t5',
    'OTU_A\t9',
    '',
), '6a91f5d1b37f9a5ffb794531d4a9e9cc29a70dace978957b3dc115bb0005e54c')

# ---- cases/set2/O01_row_order/blast.tsv --------------------------------------------------------
FILES['cases/set2/O01_row_order/blast.tsv'] = (L(
    'OTU_A\ts_OTU_A_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_B\ts_OTU_B_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '967b8516fa3fb754aca81e702388cec65cb5101f89e46e115090c8fdc356a6e6')

# ---- cases/set2/O01_row_order/features.tsv -----------------------------------------------------
FILES['cases/set2/O01_row_order/features.tsv'] = (L(
    '#ID\tS1',
    'OTU_B\t5',
    'OTU_A\t5',
    '',
), 'f14d7734a2d4749a3a4ce45914232de74c3c43cf0a2ba76017d7aa9d59a92216')

# ---- cases/set2/P02_embedded_quote/blast.tsv ---------------------------------------------------
FILES['cases/set2/P02_embedded_quote/blast.tsv'] = (L(
    'OTU\ts_OTU_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tHomo sapiens 16S "partial" sequence\t1e-50\t200\t100\t100',
    'OTU\ts_OTU_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), 'bc1d5aed542b8396c7ad4af8b9b92e96251a51f933176c5b1a588665b5c664ea')

# ---- cases/set2/P02_embedded_quote/features.tsv ------------------------------------------------
FILES['cases/set2/P02_embedded_quote/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    '',
), '876af60bbd221585bce5c3ae604035145ee0d2a7486037f951d3304a761d3978')

# ---- cases/set2/P03_tab_inside_title/blast.tsv -------------------------------------------------
FILES['cases/set2/P03_tab_inside_title/blast.tsv'] = (L(
    'OTU\ts_OTU_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tHomo\tsapiens clone\t1e-50\t200\t90\t90',
    'OTU\ts_OTU_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '422d4ce5d2af8272b252fa9860dc744987332cb82c7f8a5a606720f2e5cf26e8')

# ---- cases/set2/P03_tab_inside_title/features.tsv ----------------------------------------------
FILES['cases/set2/P03_tab_inside_title/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    '',
), '876af60bbd221585bce5c3ae604035145ee0d2a7486037f951d3304a761d3978')

# ---- cases/set2/P04_blank_line/blast.tsv -------------------------------------------------------
FILES['cases/set2/P04_blank_line/blast.tsv'] = (L(
    'OTU_A\ts_OTU_A_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
    'OTU_A\ts_OTU_A_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_B\ts_OTU_B_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), 'deea411bfd52b6e42b55481cbb4aba844cad7a12c6d3ef6def128938e353187d')

# ---- cases/set2/P04_blank_line/features.tsv ----------------------------------------------------
FILES['cases/set2/P04_blank_line/features.tsv'] = (L(
    '#ID\tS1',
    'OTU_A\t5',
    'OTU_B\t5',
    '',
), '853cb7d022d4c366dee18a2d221d53bf8fccce95de7aac98779225ff47052ff8')

# ---- cases/set2/P05_CRLF/blast.tsv -------------------------------------------------------------
FILES['cases/set2/P05_CRLF/blast.tsv'] = (L(
    'OTU_A\ts_OTU_A_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100\r',
    'OTU_A\ts_OTU_A_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100\r',
    'OTU_B\ts_OTU_B_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100\r',
    '',
), 'c3482d2e3f0664ff394aac226423cda9a62e107cd35defdd735f0d52a3de558c')

# ---- cases/set2/P05_CRLF/features.tsv ----------------------------------------------------------
FILES['cases/set2/P05_CRLF/features.tsv'] = (L(
    '#ID\tS1\r',
    'OTU_A\t5\r',
    'OTU_B\t3\r',
    '',
), '1ef768ad9fd9043865e5e0d0b22f0bedd79ce0d52eed15ff4d3cf6c82c384206')

# ---- cases/set2/P06_BOM_on_blast/blast.tsv -----------------------------------------------------
FILES['cases/set2/P06_BOM_on_blast/blast.tsv'] = (L(
    '\ufeffOTU_A\ts_OTU_A_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_A\ts_OTU_A_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_B\ts_OTU_B_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '30a9357750b967d0fd125aab9bd32f57835ef5be8d5ad05fd40fef25f6f75f6d')

# ---- cases/set2/P06_BOM_on_blast/features.tsv --------------------------------------------------
FILES['cases/set2/P06_BOM_on_blast/features.tsv'] = (L(
    '#ID\tS1',
    'OTU_A\t5',
    'OTU_B\t5',
    '',
), '853cb7d022d4c366dee18a2d221d53bf8fccce95de7aac98779225ff47052ff8')

# ---- cases/set2/P07_short_blast_row/blast.tsv --------------------------------------------------
FILES['cases/set2/P07_short_blast_row/blast.tsv'] = (L(
    'OTU_A\ts_OTU_A_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_A\ts_OTU_A_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_B\ts_OTU_B_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200',
    '',
), 'd3d5c27da0bbfd601edfb9baf6456ee46751d36821c003298d3ba762dc171756')

# ---- cases/set2/P07_short_blast_row/features.tsv -----------------------------------------------
FILES['cases/set2/P07_short_blast_row/features.tsv'] = (L(
    '#ID\tS1',
    'OTU_A\t5',
    'OTU_B\t5',
    '',
), '853cb7d022d4c366dee18a2d221d53bf8fccce95de7aac98779225ff47052ff8')

# ---- cases/set2/P08_ragged_table_row/blast.tsv -------------------------------------------------
FILES['cases/set2/P08_ragged_table_row/blast.tsv'] = (L(
    'OTU_A\ts_OTU_A_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_A\ts_OTU_A_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_B\ts_OTU_B_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '34d57df90a230b19d3bcde80707d2a0b4b04643dd7a5d794a00c51d7066ad2b5')

# ---- cases/set2/P08_ragged_table_row/features.tsv ----------------------------------------------
FILES['cases/set2/P08_ragged_table_row/features.tsv'] = (L(
    '#ID\tS1\tS2',
    'OTU_A\t5\t6',
    'OTU_B\t3',
    '',
), 'c26689fe88bf63db91573fea2666cce06c93bcaadb8a68b496c08e5629e0d9f4')

# ---- cases/set2/P09_quoted_table_R_style/blast.tsv ---------------------------------------------
FILES['cases/set2/P09_quoted_table_R_style/blast.tsv'] = (L(
    'OTU_A\ts_OTU_A_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_A\ts_OTU_A_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_B\ts_OTU_B_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '34d57df90a230b19d3bcde80707d2a0b4b04643dd7a5d794a00c51d7066ad2b5')

# ---- cases/set2/P09_quoted_table_R_style/features.tsv ------------------------------------------
FILES['cases/set2/P09_quoted_table_R_style/features.tsv'] = (L(
    '"#ID"\t"S1"',
    '"OTU_A"\t"5"',
    '"OTU_B"\t"3"',
    '',
), 'e1244435892d1751be90274bc81a72771f724f806ccc088a2d6b449ea00b64e7')

# ---- cases/set2/P10_table_quote_spans_rows/blast.tsv -------------------------------------------
FILES['cases/set2/P10_table_quote_spans_rows/blast.tsv'] = (L(
    'OTU_A\ts_OTU_A_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_B\ts_OTU_B_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_C\ts_OTU_C_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '8cd9743caa76fae928e59e515f62414516942306859066a2067b1b574995bae0')

# ---- cases/set2/P10_table_quote_spans_rows/features.tsv ----------------------------------------
FILES['cases/set2/P10_table_quote_spans_rows/features.tsv'] = (L(
    '#ID\tS1',
    '"OTU_A\t5',
    'OTU_B\t3',
    'OTU_C"\t7',
    '',
), 'ca0a4434dc38d8f5334b1cfb0b9bdfb1da94fcb412c588520b87588b9c0a55a8')

# ---- cases/set2/P11_latin1_byte_in_title/blast.tsv ---------------------------------------------
FILES['cases/set2/P11_latin1_byte_in_title/blast.tsv'] = (b'OTU\ts1\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tHomo sapiens caf\xe9 clone\t1e-50\t200\t100\t100\n', 'a1c010b5246962d2bfece73967f1e9a91069fa08c7bbd90a3362b8e0b2840101')  # not UTF-8 on purpose

# ---- cases/set2/P11_latin1_byte_in_title/features.tsv ------------------------------------------
FILES['cases/set2/P11_latin1_byte_in_title/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    '',
), '876af60bbd221585bce5c3ae604035145ee0d2a7486037f951d3304a761d3978')

# ---- cases/set2/Q01_lower_coverage_removed_despite_higher_identity/blast.tsv -------------------
FILES['cases/set2/Q01_lower_coverage_removed_despite_higher_identity/blast.tsv'] = (L(
    'OTU\ts_OTU_9606_100\t9606\tN/A\tN/A\tN/A\t100\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t95\t95',
    'OTU\ts_OTU_38775_97\t38775\tN/A\tN/A\tN/A\t97\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), 'bb8421ebafda4a6c4f1750d03a3c0f1439932bfd0dd36d31a0f43bb876da6b21')

# ---- cases/set2/Q01_lower_coverage_removed_despite_higher_identity/features.tsv ----------------
FILES['cases/set2/Q01_lower_coverage_removed_despite_higher_identity/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    '',
), '876af60bbd221585bce5c3ae604035145ee0d2a7486037f951d3304a761d3978')

# ---- cases/set2/Q01_lower_coverage_removed_despite_higher_identity/params ----------------------
FILES['cases/set2/Q01_lower_coverage_removed_despite_higher_identity/params'] = (L(
    '90 97 1',
    '',
), '719e0b542519e20ab053ee7f85fcafea6c7b2f908e6be63348f46b22a606ee64')

# ---- cases/set2/Q02_identity_tie/blast.tsv -----------------------------------------------------
FILES['cases/set2/Q02_identity_tie/blast.tsv'] = (L(
    'OTU\ts_OTU_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU\ts_OTU_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), 'e2e849f71f5e08910a670a7efd91b307f384cc2a028f3548d341137ee04a9a1a')

# ---- cases/set2/Q02_identity_tie/features.tsv --------------------------------------------------
FILES['cases/set2/Q02_identity_tie/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    '',
), '876af60bbd221585bce5c3ae604035145ee0d2a7486037f951d3304a761d3978')

# ---- cases/set2/Q03_neighbour_chain/blast.tsv --------------------------------------------------
FILES['cases/set2/Q03_neighbour_chain/blast.tsv'] = (L(
    'OTU\ts_OTU_9606_100\t9606\tN/A\tN/A\tN/A\t100\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU\ts_OTU_9598_99.5\t9598\tN/A\tN/A\tN/A\t99.5\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU\ts_OTU_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU\ts_OTU_562_98.5\t562\tN/A\tN/A\tN/A\t98.5\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '70e74aacf8fc780bd3e1630ff9124658082ba229ec45f0f0efa1496ba274fb90')

# ---- cases/set2/Q03_neighbour_chain/features.tsv -----------------------------------------------
FILES['cases/set2/Q03_neighbour_chain/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    '',
), '876af60bbd221585bce5c3ae604035145ee0d2a7486037f951d3304a761d3978')

# ---- cases/set2/S01_genus_node_plus_species/blast.tsv ------------------------------------------
FILES['cases/set2/S01_genus_node_plus_species/blast.tsv'] = (L(
    'OTU\ts_OTU_561_99\t561\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU\ts_OTU_562_99\t562\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '790da4e9d7f2bb21cfb15da3a3bd55a5789594137df33a6644543f7d7f320466')

# ---- cases/set2/S01_genus_node_plus_species/features.tsv ---------------------------------------
FILES['cases/set2/S01_genus_node_plus_species/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    '',
), '876af60bbd221585bce5c3ae604035145ee0d2a7486037f951d3304a761d3978')

# ---- cases/set2/S02_genus_node_alone/blast.tsv -------------------------------------------------
FILES['cases/set2/S02_genus_node_alone/blast.tsv'] = (L(
    'OTU\ts_OTU_561_99\t561\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), 'c34ac068132d6e7e2158b43943a047a3c253086fb82ce82a96f6544d4790658c')

# ---- cases/set2/S02_genus_node_alone/features.tsv ----------------------------------------------
FILES['cases/set2/S02_genus_node_alone/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    '',
), '876af60bbd221585bce5c3ae604035145ee0d2a7486037f951d3304a761d3978')

# ---- cases/set2/S03_subspecies_and_species/blast.tsv -------------------------------------------
FILES['cases/set2/S03_subspecies_and_species/blast.tsv'] = (L(
    'OTU\ts_OTU_9615_99\t9615\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU\ts_OTU_9612_99\t9612\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '8770512697b67b053ce4feb778667398e5b01fb46b437a26903fdd96d8d34b63')

# ---- cases/set2/S03_subspecies_and_species/features.tsv ----------------------------------------
FILES['cases/set2/S03_subspecies_and_species/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    '',
), '876af60bbd221585bce5c3ae604035145ee0d2a7486037f951d3304a761d3978')

# ---- cases/set2/T01_semicolon_taxid_top_hit/blast.tsv ------------------------------------------
FILES['cases/set2/T01_semicolon_taxid_top_hit/blast.tsv'] = (L(
    'OTU\ts_OTU_9606;9598_100\t9606;9598\tN/A\tN/A\tN/A\t100\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU\ts_OTU_38775_98.5\t38775\tN/A\tN/A\tN/A\t98.5\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '2afad41dc7bd8a5217b29d4b3f7d9060e65993f8ce9f911ce32dd6082e5d01f5')

# ---- cases/set2/T01_semicolon_taxid_top_hit/features.tsv ---------------------------------------
FILES['cases/set2/T01_semicolon_taxid_top_hit/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    '',
), '876af60bbd221585bce5c3ae604035145ee0d2a7486037f951d3304a761d3978')

# ---- cases/set2/T01_semicolon_taxid_top_hit_with_other_feature/blast.tsv -----------------------
FILES['cases/set2/T01_semicolon_taxid_top_hit_with_other_feature/blast.tsv'] = (L(
    'OTU\ts_OTU_9606;9598_100\t9606;9598\tN/A\tN/A\tN/A\t100\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU\ts_OTU_38775_98.5\t38775\tN/A\tN/A\tN/A\t98.5\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_OK\ts_OTU_OK_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '41511f3b21ce90f17cf99347d12d7cd3266985d5893033ade0d8e54bd8a51e6f')

# ---- cases/set2/T01_semicolon_taxid_top_hit_with_other_feature/features.tsv --------------------
FILES['cases/set2/T01_semicolon_taxid_top_hit_with_other_feature/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    'OTU_OK\t4',
    '',
), 'b427a02f5caf31994cf68f6771058d71197be589cc53935a52aa1978aeb32ea4')

# ---- cases/set2/T02_NA_taxid_top_hit/blast.tsv -------------------------------------------------
FILES['cases/set2/T02_NA_taxid_top_hit/blast.tsv'] = (L(
    'OTU\ts_OTU_N/A_100\tN/A\tN/A\tN/A\tN/A\t100\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU\ts_OTU_38775_98.5\t38775\tN/A\tN/A\tN/A\t98.5\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '03e4c10ef233f7b8f422215c94f16a67e09000c298975045f583d1571ccece81')

# ---- cases/set2/T02_NA_taxid_top_hit/features.tsv ----------------------------------------------
FILES['cases/set2/T02_NA_taxid_top_hit/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    '',
), '876af60bbd221585bce5c3ae604035145ee0d2a7486037f951d3304a761d3978')

# ---- cases/set2/T02_NA_taxid_top_hit_with_other_feature/blast.tsv ------------------------------
FILES['cases/set2/T02_NA_taxid_top_hit_with_other_feature/blast.tsv'] = (L(
    'OTU\ts_OTU_N/A_100\tN/A\tN/A\tN/A\tN/A\t100\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU\ts_OTU_38775_98.5\t38775\tN/A\tN/A\tN/A\t98.5\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_OK\ts_OTU_OK_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), 'c8d86c656098d95c5141e83113cf7b6950425e037f43fb740ada0e0ac1e86a67')

# ---- cases/set2/T02_NA_taxid_top_hit_with_other_feature/features.tsv ---------------------------
FILES['cases/set2/T02_NA_taxid_top_hit_with_other_feature/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    'OTU_OK\t4',
    '',
), 'b427a02f5caf31994cf68f6771058d71197be589cc53935a52aa1978aeb32ea4')

# ---- cases/set2/T03_semicolon_taxid_tie/blast.tsv ----------------------------------------------
FILES['cases/set2/T03_semicolon_taxid_tie/blast.tsv'] = (L(
    'OTU\ts_OTU_9606;9598_99\t9606;9598\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU\ts_OTU_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '078ec9bf2fb8cc9a6b77c1f81c443a4bf566db86052338493afa0058a91149ad')

# ---- cases/set2/T03_semicolon_taxid_tie/features.tsv -------------------------------------------
FILES['cases/set2/T03_semicolon_taxid_tie/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    '',
), '876af60bbd221585bce5c3ae604035145ee0d2a7486037f951d3304a761d3978')

# ---- cases/set2/X01_term_only_in_stitle/blast.tsv ----------------------------------------------
FILES['cases/set2/X01_term_only_in_stitle/blast.tsv'] = (L(
    'OTU\ts_OTU_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tuncultured organism clone 7 18S rRNA gene\t1e-50\t200\t100\t100',
    'OTU\ts_OTU_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '67d4db9fba25546a6916dace9f85fe11d37b645138e5aee422e00baa1a73a1f2')

# ---- cases/set2/X01_term_only_in_stitle/features.tsv -------------------------------------------
FILES['cases/set2/X01_term_only_in_stitle/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    '',
), '876af60bbd221585bce5c3ae604035145ee0d2a7486037f951d3304a761d3978')

# ---- cases/set2/X02_term_only_in_sscinames/blast.tsv -------------------------------------------
FILES['cases/set2/X02_term_only_in_sscinames/blast.tsv'] = (L(
    'OTU\ts_OTU_9606_99\t9606\tuncultured bacterium\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU\ts_OTU_38775_99\t38775\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), 'c6a4a86f102f2fb8b7f778f51faf29e235b70eb36b56021dfca6c08e841100c6')

# ---- cases/set2/X02_term_only_in_sscinames/features.tsv ----------------------------------------
FILES['cases/set2/X02_term_only_in_sscinames/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    '',
), '876af60bbd221585bce5c3ae604035145ee0d2a7486037f951d3304a761d3978')

# ---- cases/set2/X03_excluded_top_hit_removes_good_hit/blast.tsv --------------------------------
FILES['cases/set2/X03_excluded_top_hit_removes_good_hit/blast.tsv'] = (L(
    'OTU\ts_OTU_100272_100\t100272\tN/A\tN/A\tN/A\t100\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU\ts_OTU_38775_98.5\t38775\tN/A\tN/A\tN/A\t98.5\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), 'ef955c3322a5ffcc4c3f23b060092826e40897c204a8cd6e61e96b01caa33406')

# ---- cases/set2/X03_excluded_top_hit_removes_good_hit/features.tsv -----------------------------
FILES['cases/set2/X03_excluded_top_hit_removes_good_hit/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    '',
), '876af60bbd221585bce5c3ae604035145ee0d2a7486037f951d3304a761d3978')

# ---- cases/set2/X03_excluded_top_hit_removes_good_hit_with_other_feature/blast.tsv -------------
FILES['cases/set2/X03_excluded_top_hit_removes_good_hit_with_other_feature/blast.tsv'] = (L(
    'OTU\ts_OTU_100272_100\t100272\tN/A\tN/A\tN/A\t100\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU\ts_OTU_38775_98.5\t38775\tN/A\tN/A\tN/A\t98.5\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    'OTU_OK\ts_OTU_OK_9606_99\t9606\tN/A\tN/A\tN/A\t99\t100\t100\t500\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100',
    '',
), '6780a1d47b46a5e10d77a1de4f20f5cf3ac84efe384386ac4e931b123af4f9a2')

# ---- cases/set2/X03_excluded_top_hit_removes_good_hit_with_other_feature/features.tsv ----------
FILES['cases/set2/X03_excluded_top_hit_removes_good_hit_with_other_feature/features.tsv'] = (L(
    '#ID\tS1',
    'OTU\t5',
    'OTU_OK\t4',
    '',
), 'b427a02f5caf31994cf68f6771058d71197be589cc53935a52aa1978aeb32ea4')

# ---- cases/set2/rankedlineage.dmp --------------------------------------------------------------
FILES['cases/set2/rankedlineage.dmp'] = (L(
    '38775\t|\tAntechinus flavipes\t|\t\t|\tAntechinus\t|\tDasyuridae\t|\tDasyuromorphia\t|\tMammalia\t|\tChordata\t|\tMetazoa\t|\tEukaryota\t|',
    '100272\t|\tuncultured eukaryote\t|\t\t|\t\t|\t\t|\t\t|\t\t|\t\t|\t\t|\tEukaryota\t|',
    '77133\t|\tuncultured bacterium\t|\t\t|\t\t|\t\t|\t\t|\t\t|\t\t|\t\t|\tBacteria\t|',
    '9606\t|\tHomo sapiens\t|\t\t|\tHomo\t|\tHominidae\t|\tPrimates\t|\tMammalia\t|\tChordata\t|\tMetazoa\t|\tEukaryota\t|',
    '9598\t|\tPan troglodytes\t|\t\t|\tPan\t|\tHominidae\t|\tPrimates\t|\tMammalia\t|\tChordata\t|\tMetazoa\t|\tEukaryota\t|',
    '562\t|\tEscherichia coli\t|\t\t|\tEscherichia\t|\tEnterobacteriaceae\t|\tEnterobacterales\t|\tGammaproteobacteria\t|\tPseudomonadota\t|\tPseudomonadati\t|\tBacteria\t|',
    '561\t|\tEscherichia\t|\t\t|\t\t|\tEnterobacteriaceae\t|\tEnterobacterales\t|\tGammaproteobacteria\t|\tPseudomonadota\t|\tPseudomonadati\t|\tBacteria\t|',
    '9612\t|\tCanis lupus\t|\t\t|\tCanis\t|\tCanidae\t|\tCarnivora\t|\tMammalia\t|\tChordata\t|\tMetazoa\t|\tEukaryota\t|',
    '9615\t|\tCanis lupus familiaris\t|\tCanis lupus\t|\tCanis\t|\tCanidae\t|\tCarnivora\t|\tMammalia\t|\tChordata\t|\tMetazoa\t|\tEukaryota\t|',
    '',
), '0339c6887983d6db2b61f7827205119cf55753ec9d762dd74359e736cd493e54')

# ---- results/console_output.txt ----------------------------------------------------------------
FILES['results/console_output.txt'] = (L(
    '=== A_exclusion_via_taxonomy_name  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU_A\t2',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tdropped\tdropped\tdropped\tdropped\tdropped\tdropped\tOTU_A\t2',
    'standalone exit 0',
    '=== B_eukaryote_marine_clone  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU_B\t2',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tdropped\tdropped\tdropped\tdropped\tOTU_B\t2',
    'standalone exit 0',
    '=== C_case_of_excluded_term  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tdropped\tdropped\tdropped\tdropped\tOTU_C\t2',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU_C\t2',
    'standalone exit 0',
    '=== D_strain_and_species  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Bacteria\tPseudomonadota\tGammaproteobacteria\tEnterobacterales\tEnterobacteriaceae\tEscherichia\tdropped\tOTU_D\t2',
    'upstream exit 0',
    'standalone:',
    'Bacteria\tPseudomonadota\tGammaproteobacteria\tEnterobacterales\tEnterobacteriaceae\tEscherichia\tdropped\tOTU_D\t2',
    'standalone exit 0',
    '=== E_domain_conflict  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Bacteria\tdropped\tdropped\tdropped\tdropped\tdropped\tdropped\tOTU_E\t2',
    'upstream exit 0',
    'standalone:',
    'Bacteria\tdropped\tdropped\tdropped\tdropped\tdropped\tdropped\tOTU_E\t2',
    'standalone exit 0',
    '=== F_non_contiguous_feature  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU_F\t2',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU_X\t1',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU_F\t2',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tdropped\tdropped\tdropped\tdropped\tOTU_F\t2',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU_X\t1',
    'standalone exit 0',
    '=== G_text_comparison_of_difference  (qcov 100, pident 80, difference 3)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tdropped\tdropped\tdropped\tdropped\tOTU_G\t2',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tdropped\tdropped\tdropped\tdropped\tOTU_G\t2',
    'standalone exit 0',
    '=== H_empty_superkingdom  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'upstream exit 0',
    'standalone:',
    'Testvirae\tTestviricota\tTestviricetes\tTestvirales\tTestviridae\tTestvirus\tTest virus\tOTU_H\t1',
    'standalone exit 0',
    '=== I_quote_in_title  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tdropped\tdropped\tdropped\tdropped\tOTU_I\t2',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU_I2\t1',
    'upstream exit 0',
    'standalone:',
    '-c: error: BLAST row 1 has 18 columns; eDNAFlow requires at least 21',
    'standalone exit 2',
    '=== J_first_hit_per_taxid  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU_J\t2',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU_J\t2',
    'standalone exit 0',
    '=== K_synthetic_construct_second  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU_K\t3',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU_K\t3',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tdropped\tdropped\tdropped\tdropped\tdropped\tdropped\tOTU_K\t3',
    'standalone exit 0',
    '=== L_synthetic_construct_first  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU_L\t2',
    'upstream exit 0',
    'standalone:',
    '\tdropped\tdropped\tdropped\tdropped\tdropped\tdropped\tOTU_L\t2',
    'standalone exit 0',
    '=== M_quote_merges_rows  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tdropped\tdropped\tdropped\tdropped\tOTU1\t2',
    'Bacteria\tPseudomonadota\tGammaproteobacteria\tEnterobacterales\tEnterobacteriaceae\tEscherichia\tEscherichia coli\tOTU2\t1',
    'Bacteria\tPseudomonadota\tGammaproteobacteria\tEnterobacterales\tEnterobacteriaceae\tEscherichia\tEscherichia coli\tOTU3\t1',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU1\t1',
    'standalone exit 0',
    '=== D00_diff0  (qcov 100, pident 97, difference 0)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU\t2',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU\t2',
    'standalone exit 0',
    '=== D01_diff1_floor80_gap14  (qcov 100, pident 80, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU\t2',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU\t2',
    'standalone exit 0',
    '=== D02_diff2_floor80_gap14  (qcov 100, pident 80, difference 2)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tdropped\tdropped\tdropped\tdropped\tOTU\t2',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tdropped\tdropped\tdropped\tdropped\tOTU\t2',
    'standalone exit 0',
    '=== D02b_diff2_floor97_gap2.5  (qcov 100, pident 97, difference 2)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU\t2',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU\t2',
    'standalone exit 0',
    '=== D09_diff9_floor80_gap14  (qcov 100, pident 80, difference 9)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tdropped\tdropped\tdropped\tdropped\tOTU\t2',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tdropped\tdropped\tdropped\tdropped\tOTU\t2',
    'standalone exit 0',
    '=== D09b_diff9_floor80_gap9.5  (qcov 100, pident 80, difference 9)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU\t2',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU\t2',
    'standalone exit 0',
    '=== D10_diff10_floor97_gap2  (qcov 100, pident 97, difference 10)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU\t2',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU\t2',
    'standalone exit 0',
    '=== D10b_diff10_floor80_gap14  (qcov 100, pident 80, difference 10)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU\t2',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU\t2',
    'standalone exit 0',
    '=== M01_blast_feature_missing_from_table  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU_A\t1',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU_A\t1',
    'standalone exit 0',
    '=== M02_duplicate_table_ids  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU_A\t1',
    'upstream exit 0',
    'standalone:',
    '-c: error: Duplicate feature ID: OTU_A',
    'standalone exit 2',
    '=== O01_row_order  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU_A\t1',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU_B\t1',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU_B\t1',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU_A\t1',
    'standalone exit 0',
    '=== P02_embedded_quote  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tdropped\tdropped\tdropped\tdropped\tOTU\t2',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tdropped\tdropped\tdropped\tdropped\tOTU\t2',
    'standalone exit 0',
    '=== P03_tab_inside_title  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU\t2',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU\t2',
    'standalone exit 0',
    '=== P04_blank_line  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'IndexError: list index out of range',
    'upstream exit 1',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tdropped\tdropped\tdropped\tdropped\tOTU_A\t2',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU_B\t1',
    'standalone exit 0',
    '=== P05_CRLF  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tdropped\tdropped\tdropped\tdropped\tOTU_A\t2',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU_B\t1',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tdropped\tdropped\tdropped\tdropped\tOTU_A\t2',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU_B\t1',
    'standalone exit 0',
    '=== P06_BOM_on_blast  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU_A\t1',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU_B\t1',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tdropped\tdropped\tdropped\tdropped\tOTU_A\t2',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU_B\t1',
    'standalone exit 0',
    '=== P07_short_blast_row  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'IndexError: list index out of range',
    'upstream exit 1',
    'standalone:',
    '-c: error: BLAST row 3 has 20 columns; eDNAFlow requires at least 21',
    'standalone exit 2',
    '=== P08_ragged_table_row  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tdropped\tdropped\tdropped\tdropped\tOTU_A\t2',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU_B\t1',
    'upstream exit 0',
    'standalone:',
    '-c: error: Feature-table row 3 has 2 columns; expected 3',
    'standalone exit 2',
    '=== P09_quoted_table_R_style  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tdropped\tdropped\tdropped\tdropped\tOTU_A\t2',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU_B\t1',
    'standalone exit 0',
    '=== P10_table_quote_spans_rows  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU_B\t1',
    'upstream exit 0',
    'standalone:',
    'standalone exit 0',
    '=== P11_latin1_byte_in_title  (qcov 100, pident 97, difference 1)',
    'upstream:',
    "UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position 83: invalid continuation byte",
    'upstream exit 1',
    'standalone:',
    "-c: error: 'utf-8' codec can't decode byte 0xe9 in position 83: invalid continuation byte",
    'standalone exit 2',
    '=== Q01_lower_coverage_removed_despite_higher_identity  (qcov 90, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU\t2',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU\t2',
    'standalone exit 0',
    '=== Q02_identity_tie  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tdropped\tdropped\tdropped\tdropped\tOTU\t2',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tdropped\tdropped\tdropped\tdropped\tOTU\t2',
    'standalone exit 0',
    '=== Q03_neighbour_chain  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tdropped\tdropped\tdropped\tdropped\tdropped\tdropped\tOTU\t4',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tdropped\tdropped\tdropped\tdropped\tdropped\tdropped\tOTU\t4',
    'standalone exit 0',
    '=== S01_genus_node_plus_species  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Bacteria\tPseudomonadota\tGammaproteobacteria\tEnterobacterales\tEnterobacteriaceae\tdropped\tdropped\tOTU\t2',
    'upstream exit 0',
    'standalone:',
    'Bacteria\tPseudomonadota\tGammaproteobacteria\tEnterobacterales\tEnterobacteriaceae\tdropped\tdropped\tOTU\t2',
    'standalone exit 0',
    '=== S02_genus_node_alone  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Bacteria\tPseudomonadota\tGammaproteobacteria\tEnterobacterales\tEnterobacteriaceae\t\tEscherichia\tOTU\t1',
    'upstream exit 0',
    'standalone:',
    'Bacteria\tPseudomonadota\tGammaproteobacteria\tEnterobacterales\tEnterobacteriaceae\t\tEscherichia\tOTU\t1',
    'standalone exit 0',
    '=== S03_subspecies_and_species  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tCarnivora\tCanidae\tCanis\tdropped\tOTU\t2',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tCarnivora\tCanidae\tCanis\tdropped\tOTU\t2',
    'standalone exit 0',
    '=== T01_semicolon_taxid_top_hit  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'IndexError: list index out of range',
    'upstream exit 1',
    'standalone:',
    'standalone exit 0',
    '=== T01_semicolon_taxid_top_hit_with_other_feature  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU_OK\t1',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU_OK\t1',
    'standalone exit 0',
    '=== T02_NA_taxid_top_hit  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'IndexError: list index out of range',
    'upstream exit 1',
    'standalone:',
    'standalone exit 0',
    '=== T02_NA_taxid_top_hit_with_other_feature  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU_OK\t1',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU_OK\t1',
    'standalone exit 0',
    '=== T03_semicolon_taxid_tie  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU\t2',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU\t2',
    'standalone exit 0',
    '=== X01_term_only_in_stitle  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU\t2',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tdropped\tdropped\tdropped\tdropped\tOTU\t2',
    'standalone exit 0',
    '=== X02_term_only_in_sscinames  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tDasyuromorphia\tDasyuridae\tAntechinus\tAntechinus flavipes\tOTU\t2',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\tChordata\tMammalia\tdropped\tdropped\tdropped\tdropped\tOTU\t2',
    'standalone exit 0',
    '=== X03_excluded_top_hit_removes_good_hit  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'IndexError: list index out of range',
    'upstream exit 1',
    'standalone:',
    'Eukaryota\t\t\t\t\t\tuncultured eukaryote\tOTU\t2',
    'standalone exit 0',
    '=== X03_excluded_top_hit_removes_good_hit_with_other_feature  (qcov 100, pident 97, difference 1)',
    'upstream:',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU_OK\t1',
    'upstream exit 0',
    'standalone:',
    'Eukaryota\t\t\t\t\t\tuncultured eukaryote\tOTU\t2',
    'Eukaryota\tChordata\tMammalia\tPrimates\tHominidae\tHomo\tHomo sapiens\tOTU_OK\t1',
    'standalone exit 0',
    '',
), 'f46043e074de455d66d2e31bd9496f06e11837c1acb5179460212e0f88f01f6c')

# ---- results/results.tsv -----------------------------------------------------------------------
FILES['results/results.tsv'] = (L(
    'set\tcase\tthresholds (qcov pident diff)\tfeature\tupstream result\tupstream exit\tednaflow-lca result\tednaflow-lca exit\tagree\terror messages',
    'set1\tA_exclusion_via_taxonomy_name\t100 97 1\tOTU_A\tspecies Antechinus flavipes\t0\tdomain Eukaryota\t0\tNO\t',
    'set1\tB_eukaryote_marine_clone\t100 97 1\tOTU_B\tspecies Antechinus flavipes\t0\tclass Mammalia\t0\tNO\t',
    'set1\tC_case_of_excluded_term\t100 97 1\tOTU_C\tclass Mammalia\t0\tspecies Antechinus flavipes\t0\tNO\t',
    'set1\tD_strain_and_species\t100 97 1\tOTU_D\tgenus Escherichia\t0\tgenus Escherichia\t0\tyes\t',
    'set1\tE_domain_conflict\t100 97 1\tOTU_E\tdomain Bacteria\t0\tdomain Bacteria\t0\tyes\t',
    'set1\tF_non_contiguous_feature\t100 97 1\tOTU_F\tspecies Homo sapiens | species Antechinus flavipes  [2 rows]\t0\tclass Mammalia\t0\tNO\t',
    'set1\tF_non_contiguous_feature\t100 97 1\tOTU_X\tspecies Antechinus flavipes\t0\tspecies Antechinus flavipes\t0\tyes\t',
    'set1\tG_text_comparison_of_difference\t100 80 3\tOTU_G\tclass Mammalia\t0\tclass Mammalia\t0\tyes\t',
    'set1\tH_empty_superkingdom\t100 97 1\tOTU_H\tabsent\t0\tspecies Test virus\t0\tNO\t',
    'set1\tI_quote_in_title\t100 97 1\tOTU_I\tclass Mammalia\t0\tabsent\t2\tNO\t-c: error: BLAST row 1 has 18 columns; eDNAFlow requires at least 21',
    'set1\tI_quote_in_title\t100 97 1\tOTU_I2\tspecies Antechinus flavipes\t0\tabsent\t2\tNO\t-c: error: BLAST row 1 has 18 columns; eDNAFlow requires at least 21',
    'set1\tJ_first_hit_per_taxid\t100 97 1\tOTU_J\tspecies Antechinus flavipes\t0\tspecies Antechinus flavipes\t0\tyes\t',
    'set1\tK_synthetic_construct_second\t100 97 1\tOTU_K\tspecies Homo sapiens | species Antechinus flavipes  [2 rows]\t0\tdomain Eukaryota\t0\tNO\t',
    'set1\tL_synthetic_construct_first\t100 97 1\tOTU_L\tspecies Homo sapiens\t0\tnothing assigned (blank: domain)\t0\tNO\t',
    'set1\tM_quote_merges_rows\t100 97 1\tOTU1\tclass Mammalia\t0\tspecies Homo sapiens\t0\tNO\t',
    'set1\tM_quote_merges_rows\t100 97 1\tOTU2\tspecies Escherichia coli\t0\tabsent\t0\tNO\t',
    'set1\tM_quote_merges_rows\t100 97 1\tOTU3\tspecies Escherichia coli\t0\tabsent\t0\tNO\t',
    'set2\tD00_diff0\t100 97 0\tOTU\tspecies Homo sapiens\t0\tspecies Homo sapiens\t0\tyes\t',
    'set2\tD01_diff1_floor80_gap14\t100 80 1\tOTU\tspecies Homo sapiens\t0\tspecies Homo sapiens\t0\tyes\t',
    'set2\tD02_diff2_floor80_gap14\t100 80 2\tOTU\tclass Mammalia\t0\tclass Mammalia\t0\tyes\t',
    'set2\tD02b_diff2_floor97_gap2.5\t100 97 2\tOTU\tspecies Homo sapiens\t0\tspecies Homo sapiens\t0\tyes\t',
    'set2\tD09_diff9_floor80_gap14\t100 80 9\tOTU\tclass Mammalia\t0\tclass Mammalia\t0\tyes\t',
    'set2\tD09b_diff9_floor80_gap9.5\t100 80 9\tOTU\tspecies Homo sapiens\t0\tspecies Homo sapiens\t0\tyes\t',
    'set2\tD10_diff10_floor97_gap2\t100 97 10\tOTU\tspecies Homo sapiens\t0\tspecies Homo sapiens\t0\tyes\t',
    'set2\tD10b_diff10_floor80_gap14\t100 80 10\tOTU\tspecies Homo sapiens\t0\tspecies Homo sapiens\t0\tyes\t',
    'set2\tM01_blast_feature_missing_from_table\t100 97 1\tOTU_A\tspecies Antechinus flavipes\t0\tspecies Antechinus flavipes\t0\tyes\t',
    'set2\tM02_duplicate_table_ids\t100 97 1\tOTU_A\tspecies Antechinus flavipes\t0\tabsent\t2\tNO\t-c: error: Duplicate feature ID: OTU_A',
    'set2\tO01_row_order\t100 97 1\tOTU_A\tspecies Antechinus flavipes\t0\tspecies Antechinus flavipes\t0\tyes\t',
    'set2\tO01_row_order\t100 97 1\tOTU_B\tspecies Homo sapiens\t0\tspecies Homo sapiens\t0\tyes\t',
    'set2\tP02_embedded_quote\t100 97 1\tOTU\tclass Mammalia\t0\tclass Mammalia\t0\tyes\t',
    'set2\tP03_tab_inside_title\t100 97 1\tOTU\tspecies Homo sapiens\t0\tspecies Homo sapiens\t0\tyes\t',
    'set2\tP04_blank_line\t100 97 1\tOTU_A\tabsent\t1\tclass Mammalia\t0\tNO\tIndexError: list index out of range',
    'set2\tP04_blank_line\t100 97 1\tOTU_B\tabsent\t1\tspecies Antechinus flavipes\t0\tNO\tIndexError: list index out of range',
    'set2\tP05_CRLF\t100 97 1\tOTU_A\tclass Mammalia\t0\tclass Mammalia\t0\tyes\t',
    'set2\tP05_CRLF\t100 97 1\tOTU_B\tspecies Antechinus flavipes\t0\tspecies Antechinus flavipes\t0\tyes\t',
    'set2\tP06_BOM_on_blast\t100 97 1\tOTU_A\tspecies Homo sapiens\t0\tclass Mammalia\t0\tNO\t',
    'set2\tP06_BOM_on_blast\t100 97 1\tOTU_B\tspecies Antechinus flavipes\t0\tspecies Antechinus flavipes\t0\tyes\t',
    'set2\tP07_short_blast_row\t100 97 1\t(no rows)\tabsent\t1\tabsent\t2\tNO\tIndexError: list index out of range / -c: error: BLAST row 3 has 20 columns; eDNAFlow requires at least 21',
    'set2\tP08_ragged_table_row\t100 97 1\tOTU_A\tclass Mammalia\t0\tabsent\t2\tNO\t-c: error: Feature-table row 3 has 2 columns; expected 3',
    'set2\tP08_ragged_table_row\t100 97 1\tOTU_B\tspecies Antechinus flavipes\t0\tabsent\t2\tNO\t-c: error: Feature-table row 3 has 2 columns; expected 3',
    'set2\tP09_quoted_table_R_style\t100 97 1\tOTU_A\tabsent\t0\tclass Mammalia\t0\tNO\t',
    'set2\tP09_quoted_table_R_style\t100 97 1\tOTU_B\tabsent\t0\tspecies Antechinus flavipes\t0\tNO\t',
    'set2\tP10_table_quote_spans_rows\t100 97 1\tOTU_B\tspecies Homo sapiens\t0\tabsent\t0\tNO\t',
    "set2\tP11_latin1_byte_in_title\t100 97 1\t(no rows)\tabsent\t1\tabsent\t2\tNO\tUnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position 83: invalid continuation byte / -c: error: 'utf-8' codec can't decode byte 0xe9 in position 83: invalid continuation byte",
    'set2\tQ01_lower_coverage_removed_despite_higher_identity\t90 97 1\tOTU\tspecies Antechinus flavipes\t0\tspecies Antechinus flavipes\t0\tyes\t',
    'set2\tQ02_identity_tie\t100 97 1\tOTU\tclass Mammalia\t0\tclass Mammalia\t0\tyes\t',
    'set2\tQ03_neighbour_chain\t100 97 1\tOTU\tdomain Eukaryota\t0\tdomain Eukaryota\t0\tyes\t',
    'set2\tS01_genus_node_plus_species\t100 97 1\tOTU\tfamily Enterobacteriaceae\t0\tfamily Enterobacteriaceae\t0\tyes\t',
    'set2\tS02_genus_node_alone\t100 97 1\tOTU\tspecies Escherichia (blank: genus)\t0\tspecies Escherichia (blank: genus)\t0\tyes\t',
    'set2\tS03_subspecies_and_species\t100 97 1\tOTU\tgenus Canis\t0\tgenus Canis\t0\tyes\t',
    'set2\tT01_semicolon_taxid_top_hit\t100 97 1\t(no rows)\tabsent\t1\tabsent\t0\tNO\tIndexError: list index out of range',
    'set2\tT01_semicolon_taxid_top_hit_with_other_feature\t100 97 1\tOTU_OK\tspecies Homo sapiens\t0\tspecies Homo sapiens\t0\tyes\t',
    'set2\tT02_NA_taxid_top_hit\t100 97 1\t(no rows)\tabsent\t1\tabsent\t0\tNO\tIndexError: list index out of range',
    'set2\tT02_NA_taxid_top_hit_with_other_feature\t100 97 1\tOTU_OK\tspecies Homo sapiens\t0\tspecies Homo sapiens\t0\tyes\t',
    'set2\tT03_semicolon_taxid_tie\t100 97 1\tOTU\tspecies Homo sapiens\t0\tspecies Homo sapiens\t0\tyes\t',
    'set2\tX01_term_only_in_stitle\t100 97 1\tOTU\tspecies Antechinus flavipes\t0\tclass Mammalia\t0\tNO\t',
    'set2\tX02_term_only_in_sscinames\t100 97 1\tOTU\tspecies Antechinus flavipes\t0\tclass Mammalia\t0\tNO\t',
    'set2\tX03_excluded_top_hit_removes_good_hit\t100 97 1\tOTU\tabsent\t1\tspecies uncultured eukaryote (blank: phylum,class,order,family,genus)\t0\tNO\tIndexError: list index out of range',
    'set2\tX03_excluded_top_hit_removes_good_hit_with_other_feature\t100 97 1\tOTU\tabsent\t0\tspecies uncultured eukaryote (blank: phylum,class,order,family,genus)\t0\tNO\t',
    'set2\tX03_excluded_top_hit_removes_good_hit_with_other_feature\t100 97 1\tOTU_OK\tspecies Homo sapiens\t0\tspecies Homo sapiens\t0\tyes\t',
    '',
), 'f45e8d162001213a92d3d67280a557f284b52358842e9e616cbf0ebc74f63f57')

# ---- evidence/bench.txt ------------------------------------------------------------------------
FILES['evidence/bench.txt'] = (L(
    'adaptation n=1000: parse 0.00 s, select_hits 0.03 s, kept 300',
    'upstream   n=1000: filterBlast 0.05 s, kept 300',
    'adaptation n=10000: parse 0.03 s, select_hits 3.32 s, kept 3000',
    'upstream   n=10000: filterBlast 4.84 s, kept 3000',
    'adaptation n=30000: parse 0.08 s, select_hits 31.37 s, kept 9000',
    'upstream   n=30000: filterBlast 43.53 s, kept 9000',
    'adaptation n=100000: parse 0.25 s, select_hits 351.60 s, kept 30000',
    '',
), 'd3cfdb8d4bafc2eef61fecd30d467030decccf795dec0d2984c31c48f957054f')

# ---- evidence/cff_validate.txt -----------------------------------------------------------------
FILES['evidence/cff_validate.txt'] = (L(
    'cffconvert 2.0.0, cffconvert --validate -i CITATION.cff (stops at the first error):',
    "  'authors' is a required property",
    '',
    'jsonschema Draft7Validator with format checker, CFF 1.2.0 schema bundled with cffconvert (all errors):',
    "- (top level) : 'authors' is a required property",
    "- repository-code : 'REPLACE_WITH_APPROVED_CSIRO_PUBLIC_REPOSITORY' is not a 'uri'",
    "- repository-code : 'REPLACE_WITH_APPROVED_CSIRO_PUBLIC_REPOSITORY' does not match '^(https|http|ftp|sftp)://.+'",
    '',
), '2ec8a312987e9231aeb82c9e5ae75c9df19031689b87c450528626314c3b97ff')

# ---- evidence/diff_compare.txt -----------------------------------------------------------------
FILES['evidence/diff_compare.txt'] = (L(
    '1. Text versus numeric, identity floor 80 (all identities 80.000 to 100.000 in 0.5 steps):',
    '   diff      0:    0 of 820 pairs disagree',
    '   diff    0.5:    0 of 820 pairs disagree',
    '   diff      1:    0 of 820 pairs disagree',
    '   diff    1.5:    0 of 820 pairs disagree',
    '   diff  1.999:    0 of 820 pairs disagree',
    '   diff      2:  230 of 820 pairs disagree; e.g. 80.0 vs 90.0 (gap 10): text says keep',
    '   diff      3:  231 of 820 pairs disagree; e.g. 80.0 vs 90.0 (gap 10): text says keep',
    '   diff      5:  231 of 820 pairs disagree; e.g. 80.0 vs 90.0 (gap 10): text says keep',
    '   diff      9:  231 of 820 pairs disagree; e.g. 80.0 vs 90.0 (gap 10): text says keep',
    '   diff  9.999:  231 of 820 pairs disagree; e.g. 80.0 vs 90.0 (gap 10): text says keep',
    '   diff     10:  472 of 820 pairs disagree; e.g. 80.0 vs 82.0 (gap 2): text says remove',
    '   diff     15:  472 of 820 pairs disagree; e.g. 80.0 vs 82.0 (gap 2): text says remove',
    '   diff     20:  399 of 820 pairs disagree; e.g. 80.0 vs 83.0 (gap 3): text says remove',
    '2. Same with identity floor 97 (97.000 to 100.000, 0.001 steps, sampled):',
    '   diff 1: 0 disagreeing pairs',
    '   diff 2: 0 disagreeing pairs',
    '   diff 3: 0 disagreeing pairs',
    '   diff 9: 0 disagreeing pairs',
    '   diff 10: 10296 disagreeing pairs',
    '3. Raw float comparison (no 3-decimal rounding) versus upstream at the default diff 1:',
    '   99.1 vs 98.1: float gap 1.0; upstream removes? False; raw float gap > 1? False',
    '   98.6 vs 97.6: float gap 1.0; upstream removes? False; raw float gap > 1? False',
    '   100.0 vs 99.0: float gap 1.0; upstream removes? False; raw float gap > 1? False',
    '   98.765 vs 97.765: float gap 1.0; upstream removes? False; raw float gap > 1? False',
    '   99.3 vs 98.3: float gap 1.0; upstream removes? False; raw float gap > 1? False',
    '4. Parity BLAST file: 1467 same-feature neighbour pairs; raw-float and upstream rules disagree on 0',
    '',
), '5284e3de8b4ed27ab64963aed50054f9272f74ae2de7bd09e6e72e4cb9c18586')

# ---- evidence/dm_content_validation.txt --------------------------------------------------------
FILES['evidence/dm_content_validation.txt'] = (L(
    'empty_member: exit 0 | SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 | installed file size: 0',
    'html_member: exit 0 | SHA256: 6c63573007904b9f17d696330d49b324adf6018115aca90a59e1b683ce8aa4bb | installed file size: 46',
    'missing_member: exit 1 | RuntimeError: rankedlineage.dmp was not found in the NCBI taxonomy archive | installed file size: none',
    'traversal_member: exit 1 | RuntimeError: rankedlineage.dmp was not found in the NCBI taxonomy archive | installed file size: none',
    'not_a_zip: exit 1 | zipfile.BadZipFile: File is not a zip file | installed file size: none',
    'assigned_features\t0',
    'missing_taxids\t2',
    '',
), 'caddcc077fd9f1da8c004987bec79e371c55da014b7ed8127e91c4f6826de641')

# ---- evidence/dm_probe_wrong_folder.txt --------------------------------------------------------
FILES['evidence/dm_probe_wrong_folder.txt'] = (L(
    'Probe DM (my fixture, not project code): writes to ${out_file}_files, valid value_translation syntax (function abspath only), Galaxy release_26.1',
    'probe_dm (Test #1): passed',
    '--- loc file:',
    'v1\t/tmp/tmphfhbbt7k/galaxy-dev/rankedlineage.dmp',
    '--- target directory contents:',
    'total 8',
    'drwxr-xr-x 2 gxtest gxtest 4096 Nov  8 12:38 .',
    'drwxr-xr-x 3 gxtest gxtest 4096 Nov  8 12:38 ..',
    '--- does the registered path exist?',
    "ls: cannot access '/tmp/tmphfhbbt7k/galaxy-dev/rankedlineage.dmp': No such file or directory",
    '--- file left behind in the job folder:',
    '/tmp/tmphfhbbt7k/job_working_directory/000/1/outputs/dataset_05ec66c6-6c6f-43cb-9943-a6c523a6e2a6.dat_files/rankedlineage.dmp',
    '',
), '9339e170fcd6478695374fd17273e3317e668ef62694da526e1ec75b82359369')

# ---- evidence/dm_run1_default_layout.txt -------------------------------------------------------
FILES['evidence/dm_run1_default_layout.txt'] = (L(
    '2047:galaxy.tool_util.data ERROR 2026-11-08 12:22:52,497 [pN:main.1,p:2241,tN:LocalRunner.work_thread-0] Processing by data manager \'data_manager_ednaflow_lca_taxonomy\' returned an unknown data table "ednaflow_lca_taxonomy" with new entries "[{\'value\': \'ncbi-2026-11-08\', \'name\': \'NCBI Taxonomy Test\', \'date\': \'2026-11-08\', \'path\': \'rankedlineage.dmp\', \'sha256\': \'07b647b5732adb65d2b25b6e3fdd11d1f7e8b1826f00dbac633f95231526c6ab\'}]". These entries will not be created. Please confirm that an entry for "ednaflow_lca_taxonomy" exists in your "tool_data_table_conf.xml" file.',
    '2050:data_manager_ednaflow_lca_taxonomy (Test #1): passed',
    '',
), 'f6e35b4e6c87360432de3234f5a5e906a38396756a42827643d7e3d257a591e2')

# ---- evidence/dm_run2_table_loaded.txt ---------------------------------------------------------
FILES['evidence/dm_run2_table_loaded.txt'] = (L(
    '2053:galaxy.jobs ERROR 2026-11-08 12:25:10,352 [pN:main.1,p:2644,tN:LocalRunner.work_thread-0] exec_after_process hook failed for job 2',
    '2054-Traceback (most recent call last):',
    '2055-  File "/tmp/tmpyck5ejg7/galaxy-dev/lib/galaxy/jobs/__init__.py", line 2394, in finish',
    '2056-    task_wrapper = self.tool.exec_after_process(',
    '2057-        self.app, inp_data, out_data, param_dict, job=job, final_job_state=final_job_state',
    '2058-    )',
    '2059-  File "/tmp/tmpyck5ejg7/galaxy-dev/lib/galaxy/tools/__init__.py", line 3946, in exec_after_process',
    '2060-    data_manager.process_result(out_data)',
    '2061-    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^',
    '2062-  File "/tmp/tmpyck5ejg7/galaxy-dev/lib/galaxy/tools/data_manager/manager.py", line 234, in process_result',
    '2063-    updated_data_tables = tool_data_tables.process_bundle(',
    '2064-        out_data,',
    '2065-    ...<2 lines>...',
    '2066-        options,',
    '2067-    )',
    '2068-  File "/tmp/tmpyck5ejg7/galaxy-dev/lib/galaxy/tool_util/data/__init__.py", line 1507, in process_bundle',
    '2069-    return _process_bundle(out_data, bundle, options, self)',
    '2070-  File "/tmp/tmpyck5ejg7/galaxy-dev/lib/galaxy/tool_util/data/__init__.py", line 1653, in _process_bundle',
    '2071-    data_table_value[name] = _process_value_translations(',
    '2072-                             ~~~~~~~~~~~~~~~~~~~~~~~~~~~^',
    '2073-        data_table_name, name, bundle_description, options, **data_table_value',
    '2074-        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^',
    '2075-    )',
    '2076-    ^',
    '2077-  File "/tmp/tmpyck5ejg7/galaxy-dev/lib/galaxy/tool_util/data/__init__.py", line 1796, in _process_value_translations',
    '2078-    assert value',
    '2079-           ^^^^^',
    '2080-AssertionError',
    '2081-galaxy.jobs INFO 2026-11-08 12:25:10,358 [pN:main.1,p:2644,tN:LocalRunner.work_thread-0] Collecting metrics for Job 2 in /tmp/tmpyck5ejg7/job_working_directory/000/2',
    "[2026-11-08 12:24:52,321: DEBUG/main] Loaded tool data table 'ednaflow_lca_taxonomy' from file '/home/gxtest/lca_review/galaxy/data_manager/tool_data_table_conf.xml.sample'",
    'data_manager_ednaflow_lca_taxonomy (Test #1): failed',
    '/tmp/tmpyck5ejg7/galaxy-dev/tool-data/ednaflow_lca_taxonomy',
    '/tmp/tmpyck5ejg7/galaxy-dev/tool-data/ednaflow_lca_taxonomy/ncbi-2026-11-08',
    '/tmp/tmpyck5ejg7/job_working_directory/000/2/outputs',
    '/tmp/tmpyck5ejg7/job_working_directory/000/2/outputs/tool_stderr',
    '/tmp/tmpyck5ejg7/job_working_directory/000/2/outputs/tool_stdout',
    '/tmp/tmpyck5ejg7/job_working_directory/000/2/outputs/dataset_c90f0715-a34a-4cc4-81a1-f1697d02c353.dat_files',
    '/tmp/tmpyck5ejg7/job_working_directory/000/2/outputs/dataset_c90f0715-a34a-4cc4-81a1-f1697d02c353.dat_files/rankedlineage.dmp',
    '',
), 'db615bfd17107c2ff82be2e203d5a2b85cd190b7375f265f07a23d42ce44d8e5')

# ---- evidence/exclusion_lists.txt --------------------------------------------------------------
FILES['evidence/exclusion_lists.txt'] = (L(
    "upstream entries: 30 | distinct: 28 | duplicates: ['uncultured eukaryote', 'uncultured prasinophyte']",
    'adaptation entries (before lower-casing): 28 | distinct after lower-casing: 27',
    "in upstream, not in adaptation: ['eukaryote marine clone']",
    "in adaptation, not in upstream: ['eukaryote marine clone OLI11008']",
    "upstream pairs differing only by case: [('uncultured Chlorophyta', 'uncultured chlorophyta')]",
    '',
), '72aa43b114b603dfd19432ccbc4415a6814e256166abde1d35cc8d53143450e8')

# ---- evidence/probe_dm_fixture/data_manager/probe_dm.xml ---------------------------------------
FILES['evidence/probe_dm_fixture/data_manager/probe_dm.xml'] = (L(
    '<tool id="probe_dm" name="Probe: data manager writing to output path plus _files" version="0.1.0" tool_type="manage_data" profile="23.0">',
    '    <command><![CDATA[',
    "mkdir -p '${out_file}_files' && echo 'probe' > '${out_file}_files/rankedlineage.dmp' &&",
    'echo \'{"data_tables": {"probe_table": [{"value": "v1", "path": "rankedlineage.dmp"}]}}\' > \'$out_file\'',
    '    ]]></command>',
    '    <inputs><param name="label" type="text" value="x" label="Label"/></inputs>',
    '    <outputs><data name="out_file" format="data_manager_json"/></outputs>',
    '    <tests><test><output name="out_file"><assert_contents><has_text text="probe_table"/></assert_contents></output></test></tests>',
    '    <help>Probe only.</help>',
    '</tool>',
    '',
), '309451ecd0f6deed734204d903e839e24e252d22fc36bf1263096faf728936a1')

# ---- evidence/probe_dm_fixture/data_manager_conf.xml -------------------------------------------
FILES['evidence/probe_dm_fixture/data_manager_conf.xml'] = (L(
    '<?xml version="1.0"?>',
    '<data_managers>',
    '    <data_manager tool_file="data_manager/probe_dm.xml" id="probe_dm">',
    '        <data_table name="probe_table">',
    '            <output>',
    '                <column name="value" />',
    '                <column name="path" output_ref="out_file">',
    '                    <move type="file">',
    '                        <source>${path}</source>',
    '                        <target base="${GALAXY_DATA_MANAGER_DATA_PATH}">probe_table/${value}/rankedlineage.dmp</target>',
    '                    </move>',
    '                    <value_translation type="function">abspath</value_translation>',
    '                </column>',
    '            </output>',
    '        </data_table>',
    '    </data_manager>',
    '</data_managers>',
    '',
), 'b0cfcec06c3662cdfcbf37db246c6076153d862d7ae3c96dd2890634c153b7ee')

# ---- evidence/probe_dm_fixture/tool_data_table_conf.xml.sample ---------------------------------
FILES['evidence/probe_dm_fixture/tool_data_table_conf.xml.sample'] = (L(
    '<tables>',
    '    <table name="probe_table" comment_char="#">',
    '        <columns>value, path</columns>',
    '        <file path="tool-data/probe_table.loc" />',
    '    </table>',
    '</tables>',
    '',
), '56673a5025b95f640809d4490aafd7ee1d4037db4374c51780bd04b162765025')

# ---- evidence/python_versions.txt --------------------------------------------------------------
FILES['evidence/python_versions.txt'] = (L(
    'Python 3.9.25: 7 passed in 0.05s',
    'Python 3.10.22: 7 passed in 0.06s',
    'Python 3.11.18: 7 passed in 0.05s',
    'Python 3.12.3: 7 passed in 0.04s',
    'Python 3.13.18: 7 passed in 0.04s',
    'Python 3.14.10: 7 passed in 0.05s',
    '',
), '29b635063370e75e98c883ca33004c5991bdb1e5066c920bc4844a5b122d0080')


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else 'ednaflow-lca-comparison-harness'
    if os.path.exists(target):
        sys.exit(f"{target} already exists; choose another folder or remove it first")
    for rel, (content, digest) in FILES.items():
        data = content if isinstance(content, bytes) else content.encode('utf-8')
        if hashlib.sha256(data).hexdigest() != digest:
            sys.exit(f"checksum mismatch for {rel}; this file has been altered")
        path = os.path.join(target, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as h:
            h.write(data)
        if rel.endswith('.sh'):
            os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"Rebuilt {len(FILES)} files in {target}, all checksums verified. Start with {os.path.join(target, 'README.md')}")


if __name__ == '__main__':
    main()
