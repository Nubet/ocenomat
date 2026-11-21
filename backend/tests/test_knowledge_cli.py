import json
from contextlib import nullcontext
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from app.modules.knowledge import ingestion


@pytest.fixture
def cli_manifest(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "sources": [
                    dict(
                        source_id=source_id,
                        title=source_id,
                        path=source_id + ".pdf",
                        source_type="legal_act",
                        document_version="1",
                        parent_source_id=parent,
                    )
                    for source_id, parent in [
                        ("child", "parent"),
                        ("parent", None),
                        ("unselected", None),
                    ]
                ]
            }
        )
    )
    return path


def test_cli_imports_only_selected_sources_once_in_parent_order(
    monkeypatch, tmp_path, cli_manifest
):
    engine, storage, session, ingest = Mock(), Mock(), Mock(), Mock()
    monkeypatch.setattr(ingestion, "Settings", Mock())
    monkeypatch.setattr(ingestion, "create_database_engine", lambda _: engine)
    monkeypatch.setattr(ingestion, "ObjectStorage", lambda _: storage)
    monkeypatch.setattr(ingestion, "Session", lambda _: nullcontext(session))
    monkeypatch.setattr(ingestion, "ingest_source", ingest)
    monkeypatch.setattr(
        "sys.argv",
        [
            "ingestion",
            str(tmp_path),
            "--manifest",
            str(cli_manifest),
            "--source",
            "child",
            "--source",
            "parent",
            "--source",
            "child",
        ],
    )
    ingestion.main()
    assert [call.args[2].source_id for call in ingest.call_args_list] == [
        "parent",
        "child",
    ]
    assert all(call.args[0] is session for call in ingest.call_args_list)
    storage.initialize_bucket.assert_called_once()
    storage.close.assert_called_once()
    engine.dispose.assert_called_once()


@pytest.mark.parametrize("source_id", ["missing", "child"])
def test_invalid_selection_fails_before_accessing_database_or_storage(
    monkeypatch, tmp_path, cli_manifest, source_id
):
    settings = Mock(side_effect=AssertionError("Must fail before settings/storage"))
    monkeypatch.setattr(ingestion, "Settings", settings)
    monkeypatch.setattr(
        "sys.argv",
        [
            "ingestion",
            str(tmp_path),
            "--manifest",
            str(cli_manifest),
            "--source",
            source_id,
        ],
    )
    with pytest.raises((SystemExit, ValidationError)):
        ingestion.main()
    settings.assert_not_called()
