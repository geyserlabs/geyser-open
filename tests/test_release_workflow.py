from pathlib import Path


def test_pypi_projects_have_distinct_trusted_publisher_environments() -> None:
    workflow = Path(".github/workflows/release.yml").read_text()

    assert "  publish-pypi-sdk:\n" in workflow
    assert "    environment: pypi\n" in workflow
    assert "packages-dir: pypi-dist-sdk/" in workflow
    assert "  publish-pypi-open:\n" in workflow
    assert "    environment: pypi-geyser-open\n" in workflow
    assert "packages-dir: pypi-dist-open/" in workflow
    assert workflow.count("pypa/gh-action-pypi-publish@") == 2
    assert "needs: [assemble-and-attest, publish-pypi-sdk, publish-pypi-open]" in workflow
