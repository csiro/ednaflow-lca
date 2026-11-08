from pathlib import Path
from types import SimpleNamespace

import pytest

from ednaflow_lca.cli import read_blast, read_feature_table, run


DATA = Path(__file__).parent / "data"


def test_duplicate_feature_ids(tmp_path):
    path = tmp_path / "features.tsv"
    path.write_text(
        "#ID\tS1\n"
        "A\t1\n"
        "A\t2\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate feature ID: A"):
        read_feature_table(path)


def test_malformed_blast_columns(tmp_path):
    path = tmp_path / "blast.tsv"
    path.write_text("A\tB\t1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="expected exactly 22"):
        read_blast(path)


def test_excluded_hit(tmp_path):
    row = ["N/A"] * 22
    row[0] = "ZotuA"
    row[1] = "s"
    row[2] = "11"
    row[4] = "uncultured organism"
    row[6] = "99"
    row[7] = row[8] = row[9] = "10"
    row[18] = "1e-5"
    row[20] = "100"

    blast = tmp_path / "blast.tsv"
    blast.write_text("\t".join(row) + "\n", encoding="utf-8")

    args = SimpleNamespace(
        feature_table=str(DATA / "features.tsv"),
        blast_results=str(blast),
        taxonomy=str(DATA / "taxonomy.tsv"),
        query_coverage=100,
        percent_identity=97,
        identity_difference=1,
        assignments=str(tmp_path / "assignments.tsv"),
        filtered_hits=str(tmp_path / "filtered_hits.tsv"),
        summary=str(tmp_path / "summary.tsv"),
    )

    run(args)

    assert len((tmp_path / "assignments.tsv").read_text().splitlines()) == 1
    assert "usable_hits\t0" in (tmp_path / "summary.tsv").read_text()
