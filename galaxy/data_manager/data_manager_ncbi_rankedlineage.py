#!/usr/bin/env python3
"""Install a versioned NCBI rankedlineage.dmp snapshot for eDNAFlow LCA."""

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


def main():
    parser = argparse.ArgumentParser(
        description="Install an NCBI rankedlineage.dmp snapshot for eDNAFlow LCA"
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--extra-files-path", required=True)
    parser.add_argument("--name", default=None)
    parser.add_argument("--source-archive", default=None)
    args = parser.parse_args()

    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    # Galaxy supplies the real output dataset extra-files directory. Data Manager
    # move sources are resolved relative to this directory.
    extra_files = Path(args.extra_files_path).resolve()
    extra_files.mkdir(parents=True, exist_ok=True)

    archive = extra_files / "new_taxdump.zip"
    taxonomy = extra_files / "rankedlineage.dmp"

    if args.source_archive:
        shutil.copyfile(args.source_archive, archive)
    else:
        urllib.request.urlretrieve(ncbi_url(), archive)

    try:
        with zipfile.ZipFile(archive) as zf:
            if "rankedlineage.dmp" not in zf.namelist():
                raise RuntimeError(
                    "rankedlineage.dmp was not found in the NCBI taxonomy archive"
                )
            with zf.open("rankedlineage.dmp") as source, open(taxonomy, "wb") as target:
                shutil.copyfileobj(source, target)
    finally:
        if archive.exists():
            archive.unlink()

    if not taxonomy.is_file() or taxonomy.stat().st_size == 0:
        raise RuntimeError("Extracted rankedlineage.dmp is missing or empty")

    checksum = sha256_file(taxonomy)
    snapshot_date = date.today().isoformat()
    checksum_prefix = checksum[:8]
    value = f"ncbi-{snapshot_date}-{checksum_prefix}"
    display_name = args.name or f"NCBI Taxonomy {snapshot_date} ({checksum_prefix})"

    data_manager_entry = {
        "data_tables": {
            "ednaflow_lca_taxonomy": [
                {
                    "value": value,
                    "name": display_name,
                    "date": snapshot_date,
                    "path": "rankedlineage.dmp",
                    "sha256": checksum,
                }
            ]
        }
    }

    with open(output, "w", encoding="utf-8") as handle:
        json.dump(data_manager_entry, handle, indent=2)

    print(f"Installed {display_name}")
    print(f"Snapshot ID: {value}")
    print(f"SHA256: {checksum}")


if __name__ == "__main__":
    main()
