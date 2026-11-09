import pytest

from ednaflow_lca.cli import read_taxonomy


def test_supplied_nodes_must_contain_rankedlineage_taxid(tmp_path):
    ranked = tmp_path / "rankedlineage.dmp"
    nodes = tmp_path / "nodes.dmp"

    ranked.write_text(
        "9606\t|\tHomo sapiens\t|\t\t|\tHomo\t|\tHominidae\t|"
        "\tPrimates\t|\tMammalia\t|\tChordata\t|\tMetazoa\t|"
        "\tEukaryota\t|\n",
        encoding="utf-8",
    )

    nodes.write_text(
        "9598\t|\t9596\t|\tspecies\t|\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match=r"nodes\.dmp has no rank entry for taxonomy id 9606",
    ):
        read_taxonomy(ranked, nodes)


def test_nodes_consistency_check_does_not_apply_when_nodes_omitted(tmp_path):
    ranked = tmp_path / "rankedlineage.dmp"

    ranked.write_text(
        "9606\t|\tHomo sapiens\t|\t\t|\tHomo\t|\tHominidae\t|"
        "\tPrimates\t|\tMammalia\t|\tChordata\t|\tMetazoa\t|"
        "\tEukaryota\t|\n",
        encoding="utf-8",
    )

    taxonomy = read_taxonomy(ranked)

    assert taxonomy["9606"][-1] == "Homo sapiens"