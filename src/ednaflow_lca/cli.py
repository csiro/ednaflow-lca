"""Offline, reproducible CLI adaptation of the eDNAFlow LCA scripts.

Algorithmic behaviour follows Mahsa Mousavi-Derazmahalleh's GPL-3.0 eDNAFlow
implementation. Runtime taxonomy download and fixed intermediate filenames have
been replaced with explicit inputs and outputs suitable for Galaxy.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

RANKS = ("domain", "phylum", "class", "order", "family", "genus", "species")
EXCLUDED = (
    "uncultured bacterium",
    "uncultured organism",
    "uncultured prokaryote",
    "uncultured eukaryote",
    "uncultured marine eukaryote",
    "uncultured marine picoeukaryote",
    "uncultured Chlorophyta",
    "marine metazoan environmental sample",
    "zooplankton environmental sample",
    "uncultured fungus",
    "uncultured metazoan",
    "eukaryote marine clone",
    "eukaryotic picoplankton environmental sample",
    "uncultured alveolate",
    "uncultured ciliate",
    "uncultured Banisveld eukaryote",
    "uncultured chlorophyta",
    "uncultured prasinophyte",
    "uncultured Rhizaria",
    "uncultured stramenopile",
    "uncultured microeukaryote",
    "uncultured marine dinoflagellate",
    "uncultured prasinophyte",
    "uncultured Cryptophyta",
    "Stramenopiles sp. MAST",
    "eukaryote clone OLI11008",
    "marine Metazoa environmental sample",
    "Dinophyta sp.",
    "invertebrate environmental sample",
    "uncultured eukaryote",
)


def read_feature_table(path: Path):
    """Read the abundance table as literal tab-separated physical lines.

    Quotes have no special meaning. This matches the upstream eDNAFlow input
    contract and prevents a leading quote from joining multiple physical rows.
    """
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as h:
        for line in h:
            line = line.rstrip("\r\n")
            if not line:
                continue
            rows.append(line.split("\t"))
    if not rows or len(rows[0]) < 2:
        raise ValueError("Feature table requires a header and at least one sample column")
    header = rows[0]
    if not header[0].startswith("#"):
        raise ValueError("Feature-table first header must begin with '#', as required by eDNAFlow")
    data = {}
    for n, row in enumerate(rows[1:], 2):
        if len(row) != len(header):
            raise ValueError(f"Feature-table row {n} has {len(row)} columns; expected {len(header)}")
        if row[0] in data:
            raise ValueError(f"Duplicate feature ID: {row[0]}")
        data[row[0]] = row[1:]
    return header[1:], data


def read_taxonomy(path: Path):
    taxa = {}
    with path.open(encoding="utf-8-sig") as h:
        for n, line in enumerate(h, 1):
            line = line.rstrip("\r\n")
            if not line:
                continue
            if "\t" in line and "|" not in line:
                p = line.split("\t")
                if n == 1 and p[0].lower() in ("taxid", "tax_id"):
                    continue
                if len(p) < 8:
                    raise ValueError(f"Taxonomy row {n} requires taxid plus seven ranks")
                taxa[p[0].strip()] = tuple(x.strip() for x in p[1:8])
            else:
                p = [x.strip() for x in line.split("|")]
                if len(p) < 10:
                    raise ValueError(f"NCBI ranked-lineage row {n} has fewer than 10 pipe fields")
                taxid = p[0]
                species = p[1]
                domain = p[9] or p[8]
                taxa[taxid] = (domain, p[7], p[6], p[5], p[4], p[3], species)
    return taxa


def read_blast(path: Path):
    """Read BLAST output as literal tab-separated physical lines.

    BLAST tabular output does not use CSV quoting. Quotes therefore remain
    ordinary field content and cannot merge adjacent physical records.
    """
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as h:
        for n, line in enumerate(h, 1):
            line = line.rstrip("\r\n")
            if not line:
                continue
            row = line.split("\t")
            if len(row) < 21:
                raise ValueError(f"BLAST row {n} has {len(row)} columns; eDNAFlow requires at least 21")
            try:
                pident = float(row[6])
                qcov = float(row[20])
            except ValueError as e:
                raise ValueError(f"BLAST row {n} has non-numeric pident or qcov") from e
            rows.append(
                {
                    "feature": row[0],
                    "subject": row[1],
                    "taxid": row[2],
                    "common": row[4],
                    "pident": pident,
                    "qcov": qcov,
                    "raw": row,
                }
            )
    return rows


def select_hits(rows, qcov_min, pident_min, diff):
    # Preserve the upstream iterative adjacent-hit algorithm, while correcting
    # its accidental lexicographic comparison of formatted identity differences.
    unique = []
    seen = set()
    total_taxa = defaultdict(set)
    for hit in rows:
        total_taxa[hit["feature"]].add(hit["taxid"])
        key = (hit["feature"], hit["taxid"])
        if key not in seen:
            seen.add(key)
            unique.append(hit)
    selected = [
        h
        for h in unique
        if round(h["qcov"], 2) >= round(qcov_min, 2)
        and round(h["pident"], 2) >= round(pident_min, 2)
    ]
    changed = True
    while changed:
        changed = False
        c = 0
        while c < len(selected) - 1:
            x, y = selected[c], selected[c + 1]
            if x["feature"] == y["feature"]:
                if x["qcov"] == y["qcov"]:
                    identity_gap = round(abs(x["pident"] - y["pident"]), 3)
                    difference_limit = round(float(diff), 3)
                    if identity_gap > difference_limit:
                        del selected[c + 1 if x["pident"] > y["pident"] else c]
                        changed = True
                        break
                elif x["qcov"] > y["qcov"]:
                    del selected[c + 1]
                    changed = True
                    break
                else:
                    del selected[c]
                    changed = True
                    break
            c += 1
    return selected, {k: len(v) for k, v in total_taxa.items()}


def lca(lineages):
    # Compare every represented rank, including domain (index 0). The upstream
    # implementation stops before domain, which can retain whichever domain
    # occurs first when qualifying hits span divergent domains.
    if not lineages:
        return ("unassigned",) * 7
    acc = list(lineages[0])
    for lineage in lineages[1:]:
        loc = 6
        while loc >= 0:
            if lineage[loc] != acc[loc] and (lineage[loc] != "" or acc[loc] != ""):
                for c in range(6, loc - 1, -1):
                    acc[c] = "dropped"
            elif lineage[loc] == acc[loc] and lineage[loc] != "" and acc[loc] != "":
                break
            loc -= 1
    return tuple(acc)


def run(args):
    samples, table = read_feature_table(Path(args.feature_table))
    taxonomy = read_taxonomy(Path(args.taxonomy))
    hits = read_blast(Path(args.blast_results))
    selected, unique_counts = select_hits(
        hits,
        args.query_coverage,
        args.percent_identity,
        args.identity_difference,
    )

    usable = []
    missing = set()
    for h in selected:
        if h["taxid"] not in taxonomy:
            missing.add(h["taxid"])
            continue
        exclusion_text = "\t".join(taxonomy[h["taxid"]]) + "\t" + "\t".join(h["raw"])
        if any(term in exclusion_text for term in EXCLUDED):
            continue
        usable.append(h)

    grouped = defaultdict(list)
    for h in usable:
        grouped[h["feature"]].append(h)

    assigned = 0
    with open(args.assignments, "w", newline="", encoding="utf-8") as out:
        w = csv.writer(out, delimiter="\t", lineterminator="\n")
        w.writerow([*RANKS, "feature_id", "number_of_unique_blast_taxa", *samples])
        for feature, counts in table.items():
            if feature not in grouped:
                continue
            ranks = lca([taxonomy[h["taxid"]] for h in grouped[feature]])
            w.writerow([*ranks, feature, unique_counts.get(feature, 0), *counts])
            assigned += 1

    with open(args.filtered_hits, "w", newline="", encoding="utf-8") as out:
        w = csv.writer(out, delimiter="\t", lineterminator="\n")
        w.writerow(["feature_id", "subject_id", "taxid", "percent_identity", "query_coverage", "common_name"])
        for h in usable:
            w.writerow([h["feature"], h["subject"], h["taxid"], h["pident"], h["qcov"], h["common"]])

    with open(args.summary, "w", newline="", encoding="utf-8") as out:
        w = csv.writer(out, delimiter="\t", lineterminator="\n")
        w.writerow(["metric", "value"])
        for k, v in [
            ("feature_table_features", len(table)),
            ("blast_rows", len(hits)),
            ("selected_hits", len(selected)),
            ("usable_hits", len(usable)),
            ("assigned_features", assigned),
            ("missing_taxids", len(missing)),
            ("query_coverage_min", args.query_coverage),
            ("percent_identity_min", args.percent_identity),
            ("identity_difference", args.identity_difference),
        ]:
            w.writerow([k, v])

    if missing:
        print(
            "Warning: taxonomy missing for taxids: " + ",".join(sorted(missing)[:20]),
            file=sys.stderr,
        )


def main(argv=None):
    p = argparse.ArgumentParser(description="Offline eDNAFlow lowest-common-ancestor taxonomy assignment")
    p.add_argument("--feature-table", required=True)
    p.add_argument("--blast-results", required=True)
    p.add_argument("--taxonomy", required=True)
    p.add_argument("--query-coverage", type=float, default=100)
    p.add_argument("--percent-identity", type=float, default=97)
    p.add_argument("--identity-difference", type=float, default=1)
    p.add_argument("--assignments", required=True)
    p.add_argument("--filtered-hits", required=True)
    p.add_argument("--summary", required=True)
    a = p.parse_args(argv)
    for name in ("query_coverage", "percent_identity"):
        if not 0 <= getattr(a, name) <= 100:
            p.error(name.replace("_", "-") + " must be 0..100")
    if a.identity_difference < 0:
        p.error("identity-difference must be >= 0")
    try:
        run(a)
    except (OSError, ValueError) as e:
        p.error(str(e))


if __name__ == "__main__":
    main()
