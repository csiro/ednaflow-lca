# ednaflow-lca comparison harness

This folder holds the test cases and scripts behind the two reviews of `ednaflow-lca` (the blind review and the informed review of 8 November 2026). Each case is a small input that isolates one behaviour. The runner puts the same case through the upstream eDNAFlow LCA scripts and through the `ednaflow-lca` command-line tool, so you can see side by side where they agree and where they differ.

It is review scaffolding, not finished test code. Use it to:

- write failing tests before each fix;
- start the upstream-comparison CI job recommended in the informed review (section P);
- show reviewers exactly where the tool matches eDNAFlow and where it deliberately differs.

Nothing here changes the `ednaflow-lca` code.

## What is in the folder

| Path | Contents |
|---|---|
| `cases/index.tsv` | One line per case: what it tests and which review finding it supports |
| `cases/set1/` | 13 cases from the blind review (A to M) and their taxonomy file |
| `cases/set2/` | 36 cases from the informed review (D, M, O, P, Q, S, T and X series) and their taxonomy file |
| `cases/set*/rankedlineage.dmp` | Synthetic taxonomy lines in NCBI's `rankedlineage.dmp` layout, covering only the taxa the cases use |
| `scripts/run_both.sh` | Runs one case through upstream and `ednaflow-lca` |
| `scripts/run_all.sh` | Runs every case and writes the results table |
| `scripts/summarise.py` | Builds `results/results.tsv` from the case outputs |
| `scripts/make_cases.py`, `scripts/make_cases2.py` | The generators used to write most of the cases (for reference) |
| `scripts/diff_compare.py` | Maps where the text and numeric identity-difference comparisons disagree |
| `scripts/bench.py` | The hit-filtering benchmark in section N of the informed review |
| `scripts/parity_checks.py`, `scripts/species_rule_check.py` | Checks run against the 76-row parity fixture |
| `results/results.tsv` | Results from a full run on 8 November 2026 |
| `results/console_output.txt` | The raw output of that run |
| `evidence/` | Supporting records for the informed review (Galaxy Data Manager runs, the Data Manager probe fixture, benchmark and validation output) |

Each case folder holds `blast.tsv` (eDNAFlow's 22-column BLAST layout), `features.tsv` (a small abundance table) and, where the thresholds differ from the defaults of 100, 97 and 1, a `params` file with three numbers: query coverage, percent identity and identity difference.

The case folders themselves are the inputs. Case M, P11 and the three `_with_other_feature` cases were written by hand, so the generators do not recreate them.

## Requirements

- Linux or macOS, with `bash` and Python 3.9 or later. No other packages are needed.
- A checkout of the `ednaflow-lca` repository. The runner needs two things from it:
  - its `src` folder;
  - the vendored upstream scripts `upstream_runAssign_collapsedTaxonomy.py` and `upstream_working_function.py` (at the repository root).

  The runner also accepts upstream's own file names, from a clone of `mahsa-mousavi/eDNAFlow` (folder `LCA_taxonomyAssignment_scripts`).

## Running it

Work on a copy, because the runner writes output folders into every case folder:

```
cp -r ednaflow-lca-comparison-harness /tmp/harness
bash /tmp/harness/scripts/run_all.sh /path/to/ednaflow-lca /path/to/ednaflow-lca/src
```

The first argument is the folder that holds the upstream scripts (here the repository root), and the second is the `src` folder. To run a single case:

```
bash /tmp/harness/scripts/run_both.sh /tmp/harness/cases/set1/A_exclusion_via_taxonomy_name /path/to/ednaflow-lca /path/to/ednaflow-lca/src
```

Each case folder then gains two output folders:

- `up/` from upstream: `out.tsv`, `run.log` and upstream's intermediate files;
- `sa/` from `ednaflow-lca`: `a.tsv` (assignments), `h.tsv` (filtered hits), `s.tsv` (summary) and `run.log`.

A full run takes a few seconds.

## Reading the results table

`results/results.tsv` has one row per case and feature. For each side it gives:

- the lowest rank that is neither empty nor `dropped` (for example `species Antechinus flavipes`), and any blank ranks;
- the exit status.

A feature missing from a side's output shows as `absent`. Two rows for one feature show as `[2 rows]`. The `agree` column is `yes` only when both seven-rank lineages and both exit statuses match. Where upstream crashes and `ednaflow-lca` stops with a clear message, `agree` is `NO` even though both fail. Read those cases with the error column.

The run included here matches the findings in the informed review. In particular, A, B, C, X01, X02, X03, I and M show the exclusion and quoting divergences (D1 and D2), and P03 shows the inherited column shift.

## How upstream is run safely

Upstream's script downloads NCBI's taxonomy with `wget` and `unzip`, then runs `mkdir`, `mv`, `tr` and `rm` in its working directory. For each case, `run_both.sh`:

1. copies both upstream scripts into a fresh `up/` folder inside the case;
2. puts stub `wget` and `unzip` commands that simply fail first on `PATH`, so nothing is downloaded;
3. clears proxy variables for that command;
4. copies the case set's `rankedlineage.dmp` into `up/`, which upstream's own `tr` step then converts.

All of upstream's file operations stay inside `up/`. You will see "mv: cannot stat" messages in `up/run.log`; they come from the stubbed download and are expected. For a CI job, also run this step without network access, with a timeout, and in a throwaway directory.

`ednaflow-lca` is run with `python3 -I` and the `src` folder added to `sys.path`, so nothing is imported from the case folder.

## Turning this into tests and CI

1. **Unit tests.** For each fix, copy the relevant case into `tests/`, and assert the result the informed review recommends (section P lists the expected outputs). Write the test first, and confirm it fails before the fix.
2. **Differential CI job.**
   - Run `run_all.sh`, or an equivalent pytest fixture, on every push.
   - Keep an allow-list of intentional divergences: case, reason, and policy (for example, P06 because the byte-order mark handling is a deliberate improvement).
   - Fail the job on any difference not on the list.
   - Treat upstream crashes (P04, P07, T01, T02 and X03 without a second feature) as expected failures.
3. **Golden files.** Commit upstream's outputs for each case too, so the tests can still run where executing upstream is not possible. The live run then proves the golden files are genuine.

## Limits

- **The taxonomy lines are synthetic.** They follow NCBI's layout, but they are not copied from a real dump. Cases about viruses, synthetic constructs and NCBI's newer ranks (H, K and L) should be re-checked against lines from a current snapshot (informed review, item V1).
- **Hand-built test data.** The cases test behaviour, not realistic data volumes. For speed, use `scripts/bench.py`.
- **Dated results.** `results/results.tsv` reflects the archive reviewed on 8 November 2026. Expect it to change as fixes land; that is the point.
- **`evidence/probe_dm_fixture/`.** This is a diagnostic Data Manager written to demonstrate a Galaxy behaviour (informed review, section D). It is not a proposed implementation.

## Licence

The scripts and cases in this folder were written for the review and contain no code from `ednaflow-lca` or eDNAFlow. The upstream scripts they run are GPL-3.0 and are not included here.
