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
    assert workflow.count(
        "pypa/gh-action-pypi-publish@dc37677b2e1c63e2034f94d8a5b11f265b73ba33"
    ) == 2
    assert "needs: [assemble-and-attest, publish-pypi-sdk, publish-pypi-open]" in workflow


def test_standalone_release_artifacts_use_an_upload_visible_directory() -> None:
    workflow = Path(".github/workflows/release.yml").read_text()

    assert "--output-dir release-standalone" in workflow
    assert "path: release-standalone/*" in workflow
    assert ".release-standalone" not in workflow


def test_sigstore_uses_its_isolated_python_environment() -> None:
    workflow = Path(".github/workflows/release.yml").read_text()

    signing_step = workflow.split("- name: Keyless-sign every retained artifact", 1)[1]
    signing_step = signing_step.split("- uses: actions/upload-artifact@", 1)[0]
    assert 'UV_PYTHON: ""' in signing_step


def test_documentation_publishes_a_stable_default_alias() -> None:
    workflow = Path(".github/workflows/docs.yml").read_text()

    assert '"$DOCS_VERSION" stable' in workflow
    assert "mike set-default --push stable" in workflow
    assert '"$DOCS_VERSION" preview' not in workflow
