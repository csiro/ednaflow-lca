import subprocess
import sys
import zipfile
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "galaxy" / "data_manager" / "data_manager_ncbi_rankedlineage.py"


def write_archive(path, rankedlineage, nodes):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("rankedlineage.dmp", rankedlineage)
        archive.writestr("nodes.dmp", nodes)


def run_manager(tmp_path, rankedlineage, nodes):
    archive = tmp_path / "new_taxdump_test.zip"
    output = tmp_path / "result.json"
    extra_files = tmp_path / "result_files"
    write_archive(archive, rankedlineage, nodes)
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--output",
            str(output),
            "--extra-files-path",
            str(extra_files),
            "--name",
            "NCBI Taxonomy Validation Test",
            "--source-archive",
            str(archive),
        ],
        text=True,
        capture_output=True,
    )


VALID_RANKED = (
    "11\t|\tTest species\t|\t\t|\tTest genus\t|\tTest family\t|"
    "\tTest order\t|\tTest class\t|\tTest phylum\t|\tTest kingdom\t|"
    "\tTest domain\t|\n"
)
VALID_NODES = "11\t|\t1\t|\tspecies\t|\n"


def test_valid_minimal_taxonomy_is_accepted(tmp_path):
    result = run_manager(tmp_path, VALID_RANKED, VALID_NODES)
    assert result.returncode == 0, result.stderr


def test_html_rankedlineage_is_rejected(tmp_path):
    result = run_manager(
        tmp_path,
        "<html><body>503 Service Unavailable</body></html>\n",
        VALID_NODES,
    )
    assert result.returncode != 0
    assert "rankedlineage.dmp" in (result.stdout + result.stderr)


def test_rankedlineage_nonnumeric_taxid_is_rejected(tmp_path):
    result = run_manager(
        tmp_path,
        "not-a-taxid\t|\tTest species\t|\t\t|\tTest genus\t|\tTest family\t|"
        "\tTest order\t|\tTest class\t|\tTest phylum\t|\tTest kingdom\t|"
        "\tTest domain\t|\n",
        VALID_NODES,
    )
    assert result.returncode != 0
    assert "rankedlineage.dmp" in (result.stdout + result.stderr)


def test_nodes_nonnumeric_taxid_is_rejected(tmp_path):
    result = run_manager(tmp_path, VALID_RANKED, "bad\t|\t1\t|\tspecies\t|\n")
    assert result.returncode != 0
    assert "nodes.dmp" in (result.stdout + result.stderr)


def test_nodes_nonnumeric_parent_taxid_is_rejected(tmp_path):
    result = run_manager(tmp_path, VALID_RANKED, "11\t|\tbad\t|\tspecies\t|\n")
    assert result.returncode != 0
    assert "nodes.dmp" in (result.stdout + result.stderr)


def test_nodes_blank_rank_is_rejected(tmp_path):
    result = run_manager(tmp_path, VALID_RANKED, "11\t|\t1\t|\t\t|\n")
    assert result.returncode != 0
    assert "nodes.dmp" in (result.stdout + result.stderr)
