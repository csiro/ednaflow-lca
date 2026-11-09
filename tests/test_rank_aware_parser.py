from pathlib import Path

from ednaflow_lca.cli import read_taxonomy


def test_rankedlineage_plus_nodes_places_current_taxon_at_its_rank(tmp_path):
    ranked = tmp_path / "rankedlineage.dmp"
    nodes = tmp_path / "nodes.dmp"

    ranked.write_text(
        "561\t|\tEscherichia\t|\t\t|\t\t|\tEnterobacteriaceae\t|"
        "\tEnterobacterales\t|\tGammaproteobacteria\t|\tPseudomonadota\t|"
        "\tPseudomonadati\t|\tBacteria\t|\n"
        "562\t|\tEscherichia coli\t|\t\t|\tEscherichia\t|"
        "\tEnterobacteriaceae\t|\tEnterobacterales\t|"
        "\tGammaproteobacteria\t|\tPseudomonadota\t|"
        "\tPseudomonadati\t|\tBacteria\t|\n"
        "9612\t|\tCanis lupus\t|\t\t|\tCanis\t|\tCanidae\t|"
        "\tCarnivora\t|\tMammalia\t|\tChordata\t|\tMetazoa\t|"
        "\tEukaryota\t|\n"
        "9615\t|\tCanis lupus familiaris\t|\tCanis lupus\t|\tCanis\t|"
        "\tCanidae\t|\tCarnivora\t|\tMammalia\t|\tChordata\t|"
        "\tMetazoa\t|\tEukaryota\t|\n",
        encoding="utf-8",
    )

    nodes.write_text(
        "561\t|\t543\t|\tgenus\t|\n"
        "562\t|\t561\t|\tspecies\t|\n"
        "9612\t|\t9611\t|\tspecies\t|\n"
        "9615\t|\t9612\t|\tsubspecies\t|\n",
        encoding="utf-8",
    )

    taxonomy = read_taxonomy(ranked, nodes)

    assert taxonomy["561"] == (
        "Bacteria",
        "Pseudomonadota",
        "Gammaproteobacteria",
        "Enterobacterales",
        "Enterobacteriaceae",
        "Escherichia",
        "",
    )

    assert taxonomy["562"] == (
        "Bacteria",
        "Pseudomonadota",
        "Gammaproteobacteria",
        "Enterobacterales",
        "Enterobacteriaceae",
        "Escherichia",
        "Escherichia coli",
    )

    assert taxonomy["9612"] == (
        "Eukaryota",
        "Chordata",
        "Mammalia",
        "Carnivora",
        "Canidae",
        "Canis",
        "Canis lupus",
    )

    assert taxonomy["9615"] == (
        "Eukaryota",
        "Chordata",
        "Mammalia",
        "Carnivora",
        "Canidae",
        "Canis",
        "Canis lupus",
    )