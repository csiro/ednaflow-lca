from argparse import Namespace
from pathlib import Path

from ednaflow_lca.cli import run


def test_filtered_hits_preserve_terminal_taxon_name_and_rank(tmp_path):
    features = tmp_path / "features.tsv"
    blast = tmp_path / "blast.tsv"
    ranked = tmp_path / "rankedlineage.dmp"
    nodes = tmp_path / "nodes.dmp"

    assignments = tmp_path / "assignments.tsv"
    filtered = tmp_path / "filtered.tsv"
    summary = tmp_path / "summary.tsv"

    features.write_text(
        "#ID\tS1\n"
        "OTU\t5\n",
        encoding="utf-8",
    )

    blast.write_text(
        "OTU\ts1\t9615\tN/A\tN/A\tN/A\t99\t100\t100\t500\t"
        "N/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100\n"
        "OTU\ts2\t9612\tN/A\tN/A\tN/A\t99\t100\t100\t500\t"
        "N/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\tN/A\t1e-50\t200\t100\t100\n",
        encoding="utf-8",
    )

    ranked.write_text(
        "9612\t|\tCanis lupus\t|\t\t|\tCanis\t|\tCanidae\t|"
        "\tCarnivora\t|\tMammalia\t|\tChordata\t|\tMetazoa\t|\tEukaryota\t|\n"
        "9615\t|\tCanis lupus familiaris\t|\tCanis lupus\t|\tCanis\t|"
        "\tCanidae\t|\tCarnivora\t|\tMammalia\t|\tChordata\t|"
        "\tMetazoa\t|\tEukaryota\t|\n",
        encoding="utf-8",
    )

    nodes.write_text(
        "9612\t|\t9611\t|\tspecies\t|\n"
        "9615\t|\t9612\t|\tsubspecies\t|\n",
        encoding="utf-8",
    )

    args = Namespace(
        feature_table=str(features),
        blast_results=str(blast),
        taxonomy=str(ranked),
        taxonomy_nodes=str(nodes),
        query_coverage=100,
        percent_identity=97,
        identity_difference=1,
        assignments=str(assignments),
        filtered_hits=str(filtered),
        summary=str(summary),
    )

    run(args)

    rows = filtered.read_text(encoding="utf-8").splitlines()

    assert rows[0].split("\t") == [
        "feature_id",
        "subject_id",
        "taxid",
        "taxon_name",
        "taxon_rank",
        "domain",
        "phylum",
        "class",
        "order",
        "family",
        "genus",
        "species",
        "percent_identity",
        "query_coverage",
        "common_name",
    ]

    assert "Canis lupus familiaris" in rows[1]
    assert "subspecies" in rows[1]
    assert "Canis lupus" in rows[1]

    assert "Canis lupus" in rows[2]
    assert "species" in rows[2]