from __future__ import annotations

import gzip
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "finalize_docs_release", ROOT / "scripts" / "finalize_docs_release.py"
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_finalize_publishes_root_metadata_and_versioned_sitemap(tmp_path: Path) -> None:
    source = tmp_path / "source"
    pages = tmp_path / "pages"
    version = pages / "0.1.0"
    source.mkdir()
    version.mkdir(parents=True)
    (source / "CNAME").write_text("docs.geyserlabs.ai\n", encoding="utf-8")
    (source / "robots.txt").write_text("User-agent: *\n", encoding="utf-8")
    (source / "llms.txt").write_text("# Geyser\n", encoding="utf-8")
    (version / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<url><loc>https://docs.geyserlabs.ai/</loc></url>"
        "<url><loc>https://docs.geyserlabs.ai/sdk/</loc></url>"
        "</urlset>",
        encoding="utf-8",
    )

    outputs = MODULE.finalize(pages, source, "0.1.0")

    assert len(outputs) == 7
    assert (pages / "CNAME").read_text() == "docs.geyserlabs.ai\n"
    assert (pages / "robots.txt").read_text() == "User-agent: *\n"
    assert (pages / "llms.txt").read_text() == "# Geyser\n"
    sitemap = (pages / "sitemap.xml").read_text()
    assert "https://docs.geyserlabs.ai/0.1.0/" in sitemap
    assert "https://docs.geyserlabs.ai/0.1.0/sdk/" in sitemap
    assert sitemap == (version / "sitemap.xml").read_text()
    with gzip.open(pages / "sitemap.xml.gz", "rt", encoding="utf-8") as archive:
        assert archive.read() == sitemap
    with gzip.open(version / "sitemap.xml.gz", "rt", encoding="utf-8") as archive:
        assert archive.read() == sitemap


def test_finalize_rejects_non_release_version(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="exact release"):
        MODULE.finalize(tmp_path / "pages", tmp_path / "source", "../preview")
