from ednaflow_lca.cli import lca


def test_cross_domain_evidence_drops_all_taxonomic_ranks():
    bacteria = (
        "Bacteria",
        "Pseudomonadota",
        "Gammaproteobacteria",
        "Enterobacterales",
        "Enterobacteriaceae",
        "Escherichia",
        "Escherichia coli",
    )

    eukaryota = (
        "Eukaryota",
        "Chordata",
        "Mammalia",
        "Primates",
        "Hominidae",
        "Homo",
        "Homo sapiens",
    )

    result = lca([bacteria, eukaryota])

    assert result == (
        "dropped",
        "dropped",
        "dropped",
        "dropped",
        "dropped",
        "dropped",
        "dropped",
    )