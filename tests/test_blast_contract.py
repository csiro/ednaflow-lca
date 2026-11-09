import pytest

from ednaflow_lca.cli import read_blast


def test_blast_requires_exactly_22_columns(tmp_path):
    blast = tmp_path / "blast.tsv"

    valid = [
        "OTU1",
        "subject1",
        "9606",
        "Homo sapiens",
        "human",
        "Eukaryota",
        "99.0",
        "100",
        "100",
        "500",
        "0",
        "0",
        "0",
        "1",
        "100",
        "1",
        "100",
        "Homo sapiens test sequence",
        "1e-50",
        "200",
        "100",
        "100",
    ]

    blast.write_text("\t".join(valid) + "\n", encoding="utf-8")

    rows = read_blast(blast)

    assert len(rows) == 1
    assert rows[0]["feature"] == "OTU1"
    assert rows[0]["pident"] == 99.0
    assert rows[0]["qcov"] == 100.0


def test_blast_rejects_shifted_23_column_row(tmp_path):
    blast = tmp_path / "blast.tsv"

    shifted = [
        "OTU1",
        "subject1",
        "9606",
        "Homo sapiens",
        "human",
        "Eukaryota",
        "99.0",
        "100",
        "100",
        "500",
        "0",
        "0",
        "0",
        "1",
        "100",
        "1",
        "100",
        "Homo",
        "sapiens test sequence",
        "1e-50",
        "200",
        "100",
        "100",
    ]

    blast.write_text("\t".join(shifted) + "\n", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match=r"BLAST row 1 has 23 columns; expected exactly 22",
    ):
        read_blast(blast)


def test_blast_rejects_short_21_column_row(tmp_path):
    blast = tmp_path / "blast.tsv"

    short = ["x"] * 21
    short[6] = "99"
    short[20] = "100"

    blast.write_text("\t".join(short) + "\n", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match=r"BLAST row 1 has 21 columns; expected exactly 22",
    ):
        read_blast(blast)