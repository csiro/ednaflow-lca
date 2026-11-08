import pytest

from ednaflow_lca.cli import read_blast


def blast_row(feature, subject, taxid):
    row = ["N/A"] * 22

    row[0] = feature
    row[1] = subject
    row[2] = str(taxid)

    row[6] = "99"
    row[7] = "100"
    row[8] = "100"
    row[9] = "500"

    row[18] = "1e-50"
    row[19] = "200"
    row[20] = "100"
    row[21] = "100"

    return "\t".join(row)


def test_contiguous_feature_blocks_are_accepted(tmp_path):
    blast = tmp_path / "blast.tsv"

    blast.write_text(
        blast_row("OTU_A", "a1", 9606) + "\n"
        + blast_row("OTU_A", "a2", 9598) + "\n"
        + blast_row("OTU_B", "b1", 38775) + "\n",
        encoding="utf-8",
    )

    rows = read_blast(blast)

    assert [row["feature"] for row in rows] == [
        "OTU_A",
        "OTU_A",
        "OTU_B",
    ]


def test_non_contiguous_feature_blocks_are_rejected(tmp_path):
    blast = tmp_path / "blast.tsv"

    blast.write_text(
        blast_row("OTU_A", "a1", 9606) + "\n"
        + blast_row("OTU_B", "b1", 38775) + "\n"
        + blast_row("OTU_A", "a2", 9598) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match=r"BLAST feature OTU_A occurs in non-contiguous blocks",
    ):
        read_blast(blast)