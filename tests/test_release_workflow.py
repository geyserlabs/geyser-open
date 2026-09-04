from pathlib import Path


def test_pypi_projects_publish_without_environment_approval_gates() -> None:
    workflow = Path(".github/workflows/release.yml").read_text()

    assert "  publish-pypi-sdk:\n" in workflow
    assert "environment:" not in workflow
    assert "packages-dir: pypi-dist-sdk/" in workflow
    assert "  publish-pypi-open:\n" in workflow
    assert "packages-dir: pypi-dist-open/" in workflow
    assert workflow.count("pypa/gh-action-pypi-publish@") == 2
    assert workflow.count(
        "pypa/gh-action-pypi-publish@dc37677b2e1c63e2034f94d8a5b11f265b73ba33"
    ) == 2
    assert "needs: [assemble, publish-pypi-sdk, publish-pypi-open]" in workflow


def test_standalone_release_artifacts_use_an_upload_visible_directory() -> None:
    workflow = Path(".github/workflows/release.yml").read_text()

    assert "--output-dir release-standalone" in workflow
    assert "path: release-standalone/*" in workflow
    assert ".release-standalone" not in workflow


def test_release_has_no_evidence_or_attestation_pipeline() -> None:
    workflow = Path(".github/workflows/release.yml").read_text()
    assert "assemble-and-attest" not in workflow
    assert "actions/attest" not in workflow
    assert "SBOM" not in workflow
    assert "provenance" not in workflow.lower()


def test_documentation_publishes_a_stable_default_alias() -> None:
    workflow = Path(".github/workflows/docs.yml").read_text()

    assert '"$DOCS_VERSION" stable' in workflow
    assert "mike set-default --push stable" in workflow
    assert '"$DOCS_VERSION" preview' not in workflow
