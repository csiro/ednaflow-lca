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
    "uncultured bacterium", "uncultured organism", "uncultured prokaryote",
    "uncultured eukaryote", "uncultured marine eukaryote",
    "uncultured marine picoeukaryote", "uncultured Chlorophyta",
    "marine metazoan environmental sample", "zooplankton environmental sample",
    "uncultured fungus", "uncultured metazoan", "eukaryote marine clone",
    "eukaryotic picoplankton environmental sample", "uncultured alveolate",
    "uncultured ciliate", "uncultured Banisveld eukaryote",
    "uncultured chlorophyta", "uncultured prasinophyte", "uncultured Rhizaria",
    "uncultured stramenopile", "uncultured microeukaryote",
    "uncultured marine dinoflagellate", "uncultured prasinophyte",
    "uncultured Cryptophyta", "Stramenopiles sp. MAST",
    "eukaryote clone OLI11008", "marine Metazoa environmental sample",
    "Dinophyta sp.", "invertebrate environmental sample", "uncultured eukaryote",
)


def read_feature_table(path: Path):
    """Read the abundance table as literal tab-separated physical lines."""
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for line in handle:
            line = line.rstrip("\r\n")
            if line:
                rows.append(line.split("\t"))
    if not rows or len(rows[0]) < 2:
        raise ValueError("Feature table requires a header and at least one sample column")
    header = rows[0]
    if not header[0].startswith("#"):
        raise ValueError("Feature-table first header must begin with '#', as required by eDNAFlow")
    data = {}
    for number, row in enumerate(rows[1:], 2):
        if len(row) != len(header):
            raise ValueError(f"Feature-table row {number} has {len(row)} columns; expected {len(header)}")
        if row[0] in data:
            raise ValueError(f"Duplicate feature ID: {row[0]}")
        data[row[0]] = row[1:]
    return header[1:], data


def _read_taxonomy_with_provenance(path: Path, nodes_path: Path | None = None):
    """Return seven-rank lineages and per-taxid terminal-name provenance."""
    current_ranks = {}
    if nodes_path is not None:
        with Path(nodes_path).open(encoding="utf-8-sig") as handle:
            for number, line in enumerate(handle, 1):
                line = line.rstrip("\r\n")
                if not line:
                    continue
                fields = [value.strip() for value in line.split("|")]
                if len(fields) < 3:
                    raise ValueError(f"NCBI nodes row {number} has fewer than 3 pipe fields")
                current_ranks[fields[0]] = fields[2]

    taxa = {}
    provenance = {}
    with path.open(encoding="utf-8-sig") as handle:
        for number, line in enumerate(handle, 1):
            line = line.rstrip("\r\n")
            if not line:
                continue
            if "\t" in line and "|" not in line:
                fields = line.split("\t")
                if number == 1 and fields[0].lower() in ("taxid", "tax_id"):
                    continue
                if len(fields) < 8:
                    raise ValueError(f"Taxonomy row {number} requires taxid plus seven ranks")
                taxid = fields[0].strip()
                taxa[taxid] = tuple(value.strip() for value in fields[1:8])
                provenance[taxid] = {"taxon_name": "", "taxon_rank": ""}
                continue

            fields = [value.strip() for value in line.split("|")]
            if len(fields) < 10:
                raise ValueError(f"NCBI ranked-lineage row {number} has fewer than 10 pipe fields")
            taxid = fields[0]
            taxon_name = fields[1]
            species = fields[2]
            domain = fields[9] or fields[8]
            lineage = [domain, fields[7], fields[6], fields[5], fields[4], fields[3], species]
            current_rank = current_ranks.get(taxid, "")
            rank_index = {
                "superkingdom": 0, "domain": 0, "phylum": 1, "class": 2,
                "order": 3, "family": 4, "genus": 5, "species": 6,
            }.get(current_rank)
            if rank_index is not None:
                lineage[rank_index] = taxon_name
            if nodes_path is None:
                lineage[6] = taxon_name
            taxa[taxid] = tuple(lineage)
            provenance[taxid] = {"taxon_name": taxon_name, "taxon_rank": current_rank}
    return taxa, provenance


def read_taxonomy(path: Path, nodes_path: Path | None = None):
    """Read taxonomy lineages, optionally using nodes.dmp for current ranks."""
    taxa, _ = _read_taxonomy_with_provenance(path, nodes_path)
    return taxa


def read_blast(path: Path):
    """Read BLAST output as literal tab-separated physical lines."""
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for number, line in enumerate(handle, 1):
            line = line.rstrip("\r\n")
            if not line:
                continue
            row = line.split("\t")
            if len(row) < 21:
                raise ValueError(f"BLAST row {number} has {len(row)} columns; eDNAFlow requires at least 21")
            try:
                pident = float(row[6])
                qcov = float(row[20])
            except ValueError as error:
                raise ValueError(f"BLAST row {number} has non-numeric pident or qcov") from error
            rows.append({
                "feature": row[0], "subject": row[1], "taxid": row[2],
                "common": row[4], "pident": pident, "qcov": qcov, "raw": row,
            })
    return rows


def select_hits(rows, qcov_min, pident_min, diff):
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
        hit for hit in unique
        if round(hit["qcov"], 2) >= round(qcov_min, 2)
        and round(hit["pident"], 2) >= round(pident_min, 2)
    ]
    changed = True
    while changed:
        changed = False
        index = 0
        while index < len(selected) - 1:
            left, right = selected[index], selected[index + 1]
            if left["feature"] == right["feature"]:
                if left["qcov"] == right["qcov"]:
                    identity_gap = round(abs(left["pident"] - right["pident"]), 3)
                    difference_limit = round(float(diff), 3)
                    if identity_gap > difference_limit:
                        del selected[index + 1 if left["pident"] > right["pident"] else index]
                        changed = True
                        break
                elif left["qcov"] > right["qcov"]:
                    del selected[index + 1]
                    changed = True
                    break
                else:
                    del selected[index]
                    changed = True
                    break
            index += 1
    return selected, {key: len(values) for key, values in total_taxa.items()}


def lca(lineages):
    if not lineages:
        return ("unassigned",) * 7
    accumulator = list(lineages[0])
    for lineage in lineages[1:]:
        rank = 6
        while rank >= 0:
            if lineage[rank] != accumulator[rank] and (lineage[rank] != "" or accumulator[rank] != ""):
                for index in range(6, rank - 1, -1):
                    accumulator[index] = "dropped"
            elif lineage[rank] == accumulator[rank] and lineage[rank] != "" and accumulator[rank] != "":
                break
            rank -= 1
    return tuple(accumulator)


def run(args):
    samples, table = read_feature_table(Path(args.feature_table))
    taxonomy_nodes = getattr(args, "taxonomy_nodes", None)
    taxonomy, taxon_provenance = _read_taxonomy_with_provenance(
        Path(args.taxonomy), Path(taxonomy_nodes) if taxonomy_nodes else None
    )
    hits = read_blast(Path(args.blast_results))
    selected, unique_counts = select_hits(
        hits, args.query_coverage, args.percent_identity, args.identity_difference
    )

    usable = []
    missing = set()
    for hit in selected:
        taxid = hit["taxid"]
        if taxid not in taxonomy:
            missing.add(taxid)
            continue
        metadata = taxon_provenance.get(taxid, {"taxon_name": "", "taxon_rank": ""})
        exclusion_text = "\t".join(taxonomy[taxid]) + "\t" + metadata["taxon_name"] + "\t" + "\t".join(hit["raw"])
        if any(term in exclusion_text for term in EXCLUDED):
            continue
        usable.append(hit)

    grouped = defaultdict(list)
    for hit in usable:
        grouped[hit["feature"]].append(hit)

    assigned = 0
    with open(args.assignments, "w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output, delimiter="\t", lineterminator="\n")
        writer.writerow([*RANKS, "feature_id", "number_of_unique_blast_taxa", *samples])
        for feature, counts in table.items():
            if feature not in grouped:
                continue
            ranks = lca([taxonomy[hit["taxid"]] for hit in grouped[feature]])
            writer.writerow([*ranks, feature, unique_counts.get(feature, 0), *counts])
            assigned += 1

    with open(args.filtered_hits, "w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output, delimiter="\t", lineterminator="\n")
        writer.writerow([
            "feature_id", "subject_id", "taxid", "taxon_name", "taxon_rank",
            *RANKS, "percent_identity", "query_coverage", "common_name",
        ])
        for hit in usable:
            taxid = hit["taxid"]
            metadata = taxon_provenance.get(taxid, {"taxon_name": "", "taxon_rank": ""})
            writer.writerow([
                hit["feature"], hit["subject"], taxid,
                metadata["taxon_name"], metadata["taxon_rank"],
                *taxonomy[taxid], hit["pident"], hit["qcov"], hit["common"],
            ])

    with open(args.summary, "w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output, delimiter="\t", lineterminator="\n")
        writer.writerow(["metric", "value"])
        for key, value in [
            ("feature_table_features", len(table)), ("blast_rows", len(hits)),
            ("selected_hits", len(selected)), ("usable_hits", len(usable)),
            ("assigned_features", assigned), ("missing_taxids", len(missing)),
            ("query_coverage_min", args.query_coverage),
            ("percent_identity_min", args.percent_identity),
            ("identity_difference", args.identity_difference),
        ]:
            writer.writerow([key, value])
    if missing:
        print("Warning: taxonomy missing for taxids: " + ",".join(sorted(missing)[:20]), file=sys.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline eDNAFlow lowest-common-ancestor taxonomy assignment")
    parser.add_argument("--feature-table", required=True)
    parser.add_argument("--blast-results", required=True)
    parser.add_argument("--taxonomy", required=True)
    parser.add_argument("--taxonomy-nodes", default=None)
    parser.add_argument("--query-coverage", type=float, default=100)
    parser.add_argument("--percent-identity", type=float, default=97)
    parser.add_argument("--identity-difference", type=float, default=1)
    parser.add_argument("--assignments", required=True)
    parser.add_argument("--filtered-hits", required=True)
    parser.add_argument("--summary", required=True)
    args = parser.parse_args(argv)
    for name in ("query_coverage", "percent_identity"):
        if not 0 <= getattr(args, name) <= 100:
            parser.error(name.replace("_", "-") + " must be 0..100")
    if args.identity_difference < 0:
        parser.error("identity-difference must be >= 0")
    try:
        run(args)
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
