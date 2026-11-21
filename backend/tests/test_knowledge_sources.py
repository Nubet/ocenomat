import os
from pathlib import Path

import pytest

from app.modules.knowledge.audit import DEFAULT_MANIFEST, audit_source
from app.modules.knowledge.extraction import extract_source, normalize_text
from app.modules.knowledge.manifest import Manifest, material_path
from app.modules.knowledge.review import Reviews, validate_review


def test_committed_reviews_are_explicit_and_partial():
    reviews = Reviews.model_validate_json(
        (DEFAULT_MANIFEST.parent / "knowledge-reviews.json").read_text()
    )
    assert {s.source_id: len(s.fragments) for s in reviews.sources} == {
        "periodic-regulation-2016": 4,
        "first-regulation-2015": 3,
        "periodic-regulation-2016-html-v1": 5,
        "first-regulation-2015-html-v1": 5,
    }
    assert all("not legal review" in s.reviewed_by for s in reviews.sources)


def test_reviewed_originals_preserve_high_risk_conditions():
    root = os.environ.get("KOMPAS_TEST_KNOWLEDGE_MATERIALS")
    if not root:
        pytest.skip("Requires original source materials")
    root = Path(root)
    manifest = Manifest.model_validate_json(DEFAULT_MANIFEST.read_text())
    reviews = Reviews.model_validate_json(
        (DEFAULT_MANIFEST.parent / "knowledge-reviews.json").read_text()
    )
    pages = {}
    for review in reviews.sources:
        spec = next(s for s in manifest.sources if s.source_id == review.source_id)
        path = material_path(root, spec.path)
        report = audit_source(root, spec)
        extraction = extract_source(
            path, path.read_bytes(), profile=spec.extraction_profile
        )
        validate_review(review, spec.source_id, report["original_sha256"], extraction)
        if spec.extraction_profile == "original":
            pages[spec.assessment_kind] = {
                f.page: normalize_text(f.content) for f in extraction.fragments
            }
        else:
            reviewed = {f.locator for f in review.fragments}
            assert len(reviewed) == 5
            assert all(locator.startswith("html:#para_") for locator in reviewed)
            assert all(
                not f.warnings for f in extraction.fragments if f.locator in reviewed
            )
    assert "nie więcej niż 3 kryteria dodatkowe" in pages["periodic"][2]
    assert "powyżej 4 punktów do 6 punktów" in pages["periodic"][3]
    assert "pod warunkiem nieuzyskania" in pages["periodic"][3]
    assert "nie krótszy niż 7 miesięcy" in pages["first"][2]
    assert "po upływie 8 miesięcy" in pages["first"][2]
    assert "nie więcej niż jednej oceny cząstkowej" in pages["first"][3]
    assert "nie niższej niż 5 punktów" in pages["first"][3]
    assert "nie stosuje się" in pages["first"][3]
