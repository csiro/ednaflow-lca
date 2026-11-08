import importlib.util
from pathlib import Path


SCRIPT = (
    Path(__file__).parents[1]
    / "galaxy"
    / "data_manager"
    / "data_manager_ncbi_rankedlineage.py"
)


def load_data_manager():
    spec = importlib.util.spec_from_file_location(
        "data_manager_ncbi_rankedlineage",
        SCRIPT,
    )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def test_download_uses_finite_timeout_and_streams_response(
    tmp_path,
    monkeypatch,
):
    module = load_data_manager()

    destination = tmp_path / "new_taxdump.zip"

    expected_payload = b"test-taxonomy-archive"

    observed = {}


    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def read(self, size=-1):
            if observed.get("read"):
                return b""

            observed["read"] = True
            return expected_payload


    def fake_urlopen(url, timeout):
        observed["url"] = url
        observed["timeout"] = timeout

        return FakeResponse()


    monkeypatch.setattr(
        module.urllib.request,
        "urlopen",
        fake_urlopen,
    )

    module.download_archive(destination)

    assert observed["url"] == module.ncbi_url()
    assert observed["timeout"] == 60
    assert destination.read_bytes() == expected_payload