from ednaflow_lca.cli import select_hits


def hit(feature, subject, taxid, pident, qcov=100):
    return {
        "feature": feature,
        "subject": subject,
        "taxid": str(taxid),
        "common": "N/A",
        "pident": float(pident),
        "qcov": float(qcov),
        "raw": [],
    }


def selected_taxids(rows, feature):
    selected, _ = select_hits(
        rows,
        qcov_min=100,
        pident_min=97,
        diff=1,
    )

    return [
        row["taxid"]
        for row in selected
        if row["feature"] == feature
    ]


def test_interleaving_does_not_change_feature_hit_selection():
    grouped = [
        hit("OTU_A", "a1", 9606, 99.0),
        hit("OTU_A", "a2", 9598, 97.0),
        hit("OTU_B", "b1", 38775, 99.0),
    ]

    interleaved = [
        hit("OTU_A", "a1", 9606, 99.0),
        hit("OTU_B", "b1", 38775, 99.0),
        hit("OTU_A", "a2", 9598, 97.0),
    ]

    grouped_result = selected_taxids(grouped, "OTU_A")
    interleaved_result = selected_taxids(interleaved, "OTU_A")

    assert grouped_result == ["9606"]
    assert interleaved_result == grouped_result


def test_interleaving_preserves_within_feature_hit_order():
    interleaved = [
        hit("OTU_A", "a1", 9606, 99.0),
        hit("OTU_B", "b1", 38775, 99.0),
        hit("OTU_A", "a2", 9598, 98.5),
        hit("OTU_B", "b2", 562, 98.0),
        hit("OTU_A", "a3", 9612, 98.0),
    ]

    selected, _ = select_hits(
        interleaved,
        qcov_min=100,
        pident_min=97,
        diff=1,
    )

    otu_a_subjects = [
        row["subject"]
        for row in selected
        if row["feature"] == "OTU_A"
    ]

    assert otu_a_subjects == ["a1", "a2", "a3"]