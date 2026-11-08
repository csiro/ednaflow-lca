#!/usr/bin/env python3
"""Install a versioned NCBI rank-aware taxonomy snapshot for eDNAFlow LCA."""

import argparse
import hashlib
import json
import shutil
import urllib.request
import zipfile
from datetime import date
from pathlib import Path


def ncbi_url():
    scheme = "https" + "://"
    hostname = "ftp." + "ncbi.nlm.nih.gov"
    route = "/pub/taxonomy/new_taxdump/new_taxdump.zip"
    return scheme + hostname + route


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def combined_snapshot_digest(rankedlineage_sha256, nodes_sha256):
    digest = hashlib.sha256()
    digest.update(f"rankedlineage.dmp:{rankedlineage_sha256}\n".encode("ascii"))
    digest.update(f"nodes.dmp:{nodes_sha256}\n".encode("ascii"))
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(
        description="Install NCBI rankedlineage.dmp and nodes.dmp for eDNAFlow LCA"
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--extra-files-path", required=True)
    parser.add_argument("--name", default=None)
    parser.add_argument("--source-archive", default=None)
    args = parser.parse_args()

    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    extra_files = Path(args.extra_files_path).resolve()
    extra_files.mkdir(parents=True, exist_ok=True)

    archive = extra_files / "new_taxdump.zip"
    rankedlineage = extra_files / "rankedlineage.dmp"
    nodes = extra_files / "nodes.dmp"

    if args.source_archive:
        shutil.copyfile(args.source_archive, archive)
    else:
        urllib.request.urlretrieve(ncbi_url(), archive)

    required_members = ("rankedlineage.dmp", "nodes.dmp")
    try:
        with zipfile.ZipFile(archive) as zf:
            missing_members = [name for name in required_members if name not in zf.namelist()]
            if missing_members:
                raise RuntimeError(
                    "Required files were not found in the NCBI taxonomy archive: "
                    + ", ".join(missing_members)
                )
            for member, destination in (
                ("rankedlineage.dmp", rankedlineage),
                ("nodes.dmp", nodes),
            ):
                with zf.open(member) as source, open(destination, "wb") as target:
                    shutil.copyfileobj(source, target)
    finally:
        if archive.exists():
            archive.unlink()

    for path in (rankedlineage, nodes):
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"Extracted {path.name} is missing or empty")

    rankedlineage_sha256 = sha256_file(rankedlineage)
    nodes_sha256 = sha256_file(nodes)
    snapshot_sha256 = combined_snapshot_digest(rankedlineage_sha256, nodes_sha256)

    snapshot_date = date.today().isoformat()
    checksum_prefix = snapshot_sha256[:8]
    value = f"ncbi-{snapshot_date}-{checksum_prefix}"
    display_name = args.name or f"NCBI Taxonomy {snapshot_date} ({checksum_prefix})"

    data_manager_entry = {
        "data_tables": {
            "ednaflow_lca_taxonomy": [
                {
                    "value": value,
                    "name": display_name,
                    "date": snapshot_date,
                    "rankedlineage_sha256": rankedlineage_sha256,
                    "nodes_sha256": nodes_sha256,
                    "path": "rankedlineage.dmp",
                    "nodes_path": "nodes.dmp",
                }
            ]
        }
    }

    with open(output, "w", encoding="utf-8") as handle:
        json.dump(data_manager_entry, handle, indent=2)

    print(f"Installed {display_name}")
    print(f"Snapshot ID: {value}")
    print(f"rankedlineage.dmp SHA256: {rankedlineage_sha256}")
    print(f"nodes.dmp SHA256: {nodes_sha256}")
    print(f"Combined snapshot SHA256: {snapshot_sha256}")


if __name__ == "__main__":
    main()
