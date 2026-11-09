from pathlib import Path
from types import SimpleNamespace

from ednaflow_lca.cli import run


def rows(path):
    with open(path, encoding="utf-8") as handle:
        return [line.rstrip("\n") for line in handle]


def test_full_rank_aware_assignment_parity(tmp_path):
    d = Path(__file__).parent / "parity"

    args = SimpleNamespace(
        feature_table=str(d / "curated_zotuTable_2test_LCAscript.tab"),
        blast_results=str(d / "blastResult_2test_LCAscript.tab"),
        taxonomy=str(d / "rankedlineage_subset_2026-11-05.dmp"),
        taxonomy_nodes=str(d / "nodes_subset_2026-11-05.dmp"),
        query_coverage=100,
        percent_identity=97,
        identity_difference=1,
        assignments=str(tmp_path / "assignments.tsv"),
        filtered_hits=str(tmp_path / "filtered_hits.tsv"),
        summary=str(tmp_path / "summary.tsv"),
    )

    run(args)

    assert rows(tmp_path / "assignments.tsv") == rows(
        d / "upstream_expected.tsv"
    )
