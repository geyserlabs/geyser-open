from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_external_preview_gate_is_published_and_fail_closed() -> None:
    navigation = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    page = (ROOT / "docs" / "external-preview.md").read_text(encoding="utf-8")

    assert "Independent developer preview gate: external-preview.md" in navigation
    assert page.count("### ") == 10
    for requirement in (
        "0.1.0b4",
        "customer 1",
        "without private hand-holding or operator credentials",
        "customer=all",
        "deny_without_explicit_authority",
        "network_used: false",
        "sigstore==4.5.0",
        "runs trace",
        "approvals decide",
        "logout",
        "opaque hashes",
    ):
        assert requirement in page


def test_documented_agent_bundle_scaffold_uses_a_real_cli_kind() -> None:
    page = (ROOT / "docs" / "bundles.md").read_text(encoding="utf-8")
    assert "geyser init agent-bundle careful-assistant" in page
    assert "geyser init bundle careful-assistant" not in page


def test_compatibility_matrix_reports_live_api_without_claiming_ga() -> None:
    page = (ROOT / "docs" / "compatibility.md").read_text(encoding="utf-8")

    assert "https://agents.geyserlabs.ai/api/v1/openapi.json" in page
    assert "Developer Preview routes yes; GA no" in page
    assert "positive independent-developer sandbox gate pending" in page
    assert "844f8123-f853-4c59-bdbc-a364da4d2517" in page
    assert "not public" not in page
