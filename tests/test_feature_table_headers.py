import pytest

from ednaflow_lca.cli import read_feature_table


def test_ednaflow_hash_header_is_accepted(tmp_path):
    table = tmp_path / "features.tsv"

    table.write_text(
        "#ID\tSample1\n"
        "OTU_A\t5\n",
        encoding="utf-8",
    )

    samples, data = read_feature_table(table)

    assert samples == ["Sample1"]
    assert data == {"OTU_A": ["5"]}


def test_feature_id_header_without_hash_is_accepted(tmp_path):
    table = tmp_path / "features.tsv"

    table.write_text(
        "feature_id\tSample1\n"
        "OTU_A\t5\n",
        encoding="utf-8",
    )

    samples, data = read_feature_table(table)

    assert samples == ["Sample1"]
    assert data == {"OTU_A": ["5"]}


def test_asv_header_is_accepted(tmp_path):
    table = tmp_path / "features.tsv"

    table.write_text(
        "ASV\tSample1\n"
        "ASV_1\t8\n",
        encoding="utf-8",
    )

    samples, data = read_feature_table(table)

    assert samples == ["Sample1"]
    assert data == {"ASV_1": ["8"]}


def test_blank_feature_header_is_rejected(tmp_path):
    table = tmp_path / "features.tsv"

    table.write_text(
        "\tSample1\n"
        "OTU_A\t5\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match=r"Feature-table first header must not be blank",
    ):
        read_feature_table(table)