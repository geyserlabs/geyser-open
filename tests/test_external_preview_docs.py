from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_preview_uses_own_workspace_and_real_execution() -> None:
    page = (ROOT / "docs/external-preview.md").read_text()
    assert "external-preview.md" in (ROOT / "mkdocs.yml").read_text()
    for required in (
        "0.2.0 source preview",
        "own authorized test workspace",
        "typed result",
        "idempotency key",
        "Revoke",
        "logout",
        "No completed independent",
    ):
        assert required in page
    assert "customer 1" not in page and "customer=all" not in page


def test_documented_agent_bundle_scaffold_uses_a_real_cli_kind() -> None:
    page = (ROOT / "docs/bundles.md").read_text()
    assert "geyser init agent-bundle careful-assistant" in page
    assert "geyser init bundle careful-assistant" not in page


def test_compatibility_distinguishes_source_published_and_running() -> None:
    page = (ROOT / "docs/compatibility.md").read_text()
    for required in (
        "0.2.0",
        "0.1.0",
        "source merge",
        "running Cell/Agent",
        "No public replay dispatch",
        "Windows",
        "reference.md",
    ):
        assert required in page
