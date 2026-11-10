from ednaflow_lca.cli import read_taxonomy


def test_blank_domain_is_not_filled_from_kingdom(tmp_path):
    ranked = tmp_path / "rankedlineage.dmp"

    ranked.write_text(
        "999999\t|\tTest taxon\t|\tTest species\t|\tTest genus\t|"
        "\tTest family\t|\tTest order\t|\tTest class\t|"
        "\tTest phylum\t|\tTest kingdom\t|\t\t|\n",
        encoding="utf-8",
    )

    taxonomy = read_taxonomy(ranked)

    assert taxonomy["999999"][0] == ""
    assert taxonomy["999999"][1] == "Test phylum"


def test_real_domain_is_preserved(tmp_path):
    ranked = tmp_path / "rankedlineage.dmp"

    ranked.write_text(
        "9606\t|\tHomo sapiens\t|\t\t|\tHomo\t|\tHominidae\t|"
        "\tPrimates\t|\tMammalia\t|\tChordata\t|\tMetazoa\t|"
        "\tEukaryota\t|\n",
        encoding="utf-8",
    )

    taxonomy = read_taxonomy(ranked)

    assert taxonomy["9606"][0] == "Eukaryota"
