from ednaflow_lca.cli import lca


def test_genus_node_is_represented_at_genus_rank():
    escherichia = (
        "Bacteria",
        "Pseudomonadota",
        "Gammaproteobacteria",
        "Enterobacterales",
        "Enterobacteriaceae",
        "Escherichia",
        "",
    )

    assert lca([escherichia]) == escherichia


def test_genus_node_plus_species_resolves_to_genus():
    escherichia = (
        "Bacteria",
        "Pseudomonadota",
        "Gammaproteobacteria",
        "Enterobacterales",
        "Enterobacteriaceae",
        "Escherichia",
        "",
    )

    escherichia_coli = (
        "Bacteria",
        "Pseudomonadota",
        "Gammaproteobacteria",
        "Enterobacterales",
        "Enterobacteriaceae",
        "Escherichia",
        "Escherichia coli",
    )

    assert lca([escherichia, escherichia_coli]) == (
        "Bacteria",
        "Pseudomonadota",
        "Gammaproteobacteria",
        "Enterobacterales",
        "Enterobacteriaceae",
        "Escherichia",
        "dropped",
    )


def test_subspecies_and_species_resolve_to_species():
    dog = (
        "Eukaryota",
        "Chordata",
        "Mammalia",
        "Carnivora",
        "Canidae",
        "Canis",
        "Canis lupus",
    )

    wolf = (
        "Eukaryota",
        "Chordata",
        "Mammalia",
        "Carnivora",
        "Canidae",
        "Canis",
        "Canis lupus",
    )

    assert lca([dog, wolf]) == dog