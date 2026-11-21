import json
import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.modules.knowledge.audit import (
    DEFAULT_MANIFEST,
    audit_download_manifest,
    audit_source,
)
from app.modules.knowledge.extraction import sha256
from app.modules.knowledge.manifest import Manifest, Provenance, SourceSpec


def provenance(**overrides):
    return Provenance(
        canonical_document_id="eli:DU/2016/470",
        original_sha256="0" * 64,
        note="Test evidence",
        **overrides,
    )


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "http://www.gov.pl/x",
        "https://www.gov.pl.example.com/x",
        "https://user:password@www.gov.pl/x",
        "https://www.gov.pl:999/x",
    ],
)
def test_provenance_rejects_nonofficial_links(url):
    with pytest.raises(ValidationError):
        provenance(official_url=url)


def test_current_status_needs_official_evidence_and_markdown_cannot_be_canonical():
    source = dict(
        source_id="test-law",
        title="Test",
        path="law.pdf",
        source_type="legal_act",
        document_version="1",
    )
    with pytest.raises(ValidationError, match="dated official evidence"):
        SourceSpec(**source, legal_status="verified_current")
    with pytest.raises(ValidationError, match="share the original checksum"):
        SourceSpec(
            **source,
            provenance=provenance(
                representations=[
                    dict(path="copy.pdf", sha256="1" * 64, relation="identical_bytes")
                ]
            ),
        )
    with pytest.raises(ValidationError, match="Markdown"):
        SourceSpec(
            **source,
            provenance=provenance(
                preferred_text_path="ai.md",
                representations=[
                    dict(path="ai.md", sha256="0" * 64, relation="alternative_format")
                ],
            ),
        )
    with pytest.raises(ValidationError, match="relative path"):
        SourceSpec(
            **source,
            provenance=provenance(
                representations=[
                    dict(
                        path="../outside.pdf",
                        sha256="0" * 64,
                        relation="alternative_format",
                    )
                ]
            ),
        )


def test_download_inventory_follows_moves_without_approving_content(tmp_path):
    historical = tmp_path / "historical"
    historical.mkdir()
    original = historical / "law.pdf"
    original.write_bytes(b"original")
    path = tmp_path / "downloads.json"
    path.write_text(
        json.dumps(
            {
                "entries": [
                    dict(
                        filename=original.name,
                        sha256=sha256(b"original"),
                        bytes=8,
                        url="https://www.gov.pl/attachment/test",
                    )
                ]
            }
        )
    )
    report = audit_download_manifest(path)
    assert report["verification_status"] == "needs_review"
    assert report["files"][0]["path"] == "historical/law.pdf"
    assert report["files"][0]["matches_download"]
    original.write_bytes(b"tampered")
    assert not audit_download_manifest(path)["files"][0]["matches_download"]
    (tmp_path / "law.pdf").write_bytes(b"original")
    with pytest.raises(ValueError, match="ambiguous"):
        audit_download_manifest(path)


def test_committed_sources_keep_ids_and_distinguish_legal_authority():
    sources = {
        s.source_id: s
        for s in Manifest.model_validate_json(DEFAULT_MANIFEST.read_text()).sources
    }
    assert sources["periodic-regulation-2016"].legal_status == "verified_current"
    assert sources["first-regulation-2015"].legal_status == "verified_current"
    assert (
        sources["periodic-criteria-appendix"].provenance.canonical_document_id
        == sources["periodic-regulation-2016"].provenance.canonical_document_id
    )
    assert sources["periodic-criteria-appendix"].provenance.usage == "duplicate_subset"
    assert sources["competency-model"].provenance.usage == "validation_only"
    for source in sources.values():
        if source.source_type in ("official_guideline", "official_form"):
            assert source.legal_status == "unknown"


def test_local_downloads_and_manifest_representations_match_originals():
    root = os.environ.get("KOMPAS_TEST_KNOWLEDGE_MATERIALS")
    if not root:
        pytest.skip("Requires original source materials")
    root = Path(root)
    downloads = audit_download_manifest(
        root / "oficjalne-zrodla/MANIFEST_POBRANYCH.json"
    )
    assert len(downloads["files"]) == 25
    assert all(f["matches_download"] for f in downloads["files"])
    assert downloads["unlisted_files"] == []
    manifest = Manifest.model_validate_json(DEFAULT_MANIFEST.read_text())
    for source in manifest.sources:
        report = audit_source(root, source)
        json.dumps(report)
        assert report["provenance_checksum_matches"]
        assert all(r["matches"] for r in report["representation_checksums"])
