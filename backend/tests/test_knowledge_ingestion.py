import io
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError
from reportlab.pdfgen.canvas import Canvas
from sqlalchemy import delete, event, func, select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session, SessionTransaction
from test_documents import MemoryStorage

from app.core.database import create_database_engine
from app.integrations.storage import StorageUnavailable
from app.modules.knowledge.extraction import extract_source, sha256
from app.modules.knowledge.ingestion import ingest_source
from app.modules.knowledge.manifest import Provenance, SourceSpec
from app.modules.knowledge.models import KnowledgeChunk, KnowledgeSource
from app.modules.knowledge.review import SourceReview, validate_review


@pytest.fixture
def original(tmp_path):
    stream = io.BytesIO()
    canvas = Canvas(stream)
    for text in ("Condition: score greater than 4.", "Exception: no score 1."):
        canvas.drawString(20, 700, text)
        canvas.showPage()
    canvas.save()
    path = tmp_path / "original.pdf"
    path.write_bytes(stream.getvalue())
    spec = SourceSpec(
        source_id=f"test-{uuid4().hex}",
        title="Test original",
        path=path.name,
        source_type="legal_act",
        document_version="test-1",
        legal_status="historical",
    )
    extraction = extract_source(path, stream.getvalue())
    review = SourceReview(
        source_id=spec.source_id,
        original_sha256=sha256(stream.getvalue()),
        reviewed_by="Test reviewer",
        reviewed_at=datetime.now(UTC) - timedelta(seconds=1),
        fragments=[
            dict(
                locator=extraction.fragments[0].locator,
                content_sha256=extraction.fragments[0].content_sha256,
                status="approved",
                reason="Compared condition with original page, including threshold.",
            )
        ],
    )
    return SimpleNamespace(
        root=tmp_path,
        path=path,
        spec=spec,
        extraction=extraction,
        review=review,
        storage=MemoryStorage(),
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("original_sha256", "0" * 64),
        ("extractor_version", "invented"),
        ("source_id", "other-source"),
    ],
)
def test_review_must_match_original_and_extractor(original, field, value):
    review = original.review.model_copy(update={field: value})
    with pytest.raises(ValueError, match="does not match"):
        validate_review(
            review,
            original.spec.source_id,
            original.review.original_sha256,
            original.extraction,
        )


@pytest.mark.parametrize(
    "field,value", [("locator", "invented"), ("content_sha256", "0" * 64)]
)
def test_review_must_match_exact_fragment(original, field, value):
    original.review.fragments[0] = original.review.fragments[0].model_copy(
        update={field: value}
    )
    with pytest.raises(ValueError, match="fragment"):
        validate_review(
            original.review,
            original.spec.source_id,
            original.review.original_sha256,
            original.extraction,
        )


def test_review_rejects_duplicate_and_future_decisions(original):
    data = original.review.model_dump()
    with pytest.raises(ValidationError, match="Duplicate"):
        SourceReview(**{**data, "fragments": data["fragments"] * 2})
    with pytest.raises(ValidationError, match="future"):
        SourceReview(**{**data, "reviewed_at": datetime.now(UTC) + timedelta(days=1)})


@pytest.mark.integration
def test_repeat_import_preserves_partial_approval_and_original(database, original):
    _, _, session = database
    for review in (None, original.review, original.review, None):
        ingest_source(session, original.root, original.spec, original.storage, review)
    chunks = list(
        session.scalars(select(KnowledgeChunk).order_by(KnowledgeChunk.chunk_index))
    )
    assert len(chunks) == 2
    assert [c.verification_status for c in chunks] == ["approved", "needs_review"]
    source = session.get(KnowledgeSource, original.spec.source_id)
    assert source.verification_status == "needs_review"
    assert source.legal_status == "historical"
    assert original.storage.objects[source.storage_key] == original.path.read_bytes()
    assert [name for name, _ in original.storage.calls].count("put") == 1
    assert len(original.storage.objects) == 1


@pytest.mark.integration
def test_provenance_is_hash_bound_and_persisted_without_duplicate_upload(
    database, original
):
    _, _, session = database
    evidence = Provenance(
        canonical_document_id="eli:DU/2016/470",
        original_sha256=original.review.original_sha256,
        official_url="https://eli.gov.pl/eli/DU/2016/470/ogl",
        note="Test evidence",
    )
    spec = original.spec.model_copy(update={"provenance": evidence})
    for _ in range(2):
        ingest_source(session, original.root, spec, original.storage)
    stored = session.get(KnowledgeSource, spec.source_id)
    assert stored.provenance == evidence.model_dump(mode="json")
    assert len(original.storage.objects) == 1


def test_provenance_mismatch_never_reaches_storage(original):
    evidence = Provenance(
        canonical_document_id="eli:DU/2016/470",
        original_sha256="0" * 64,
        note="Wrong download",
    )
    spec = original.spec.model_copy(update={"provenance": evidence})
    with pytest.raises(ValueError, match="provenance checksum"):
        ingest_source(None, original.root, spec, original.storage)
    assert not original.storage.calls


@pytest.mark.integration
def test_changed_original_cannot_overwrite_existing_source(database, original):
    _, _, session = database
    ingest_source(session, original.root, original.spec, original.storage)
    changed = original.spec.model_copy(update={"title": "Changed metadata"})
    with pytest.raises(ValueError, match="new version ID"):
        ingest_source(session, original.root, changed, original.storage)
    assert len(original.storage.objects) == 1


@pytest.mark.integration
def test_tampered_fragment_blocks_repeat_import(database, original):
    _, _, session = database
    ingest_source(session, original.root, original.spec, original.storage)
    chunk = session.scalar(select(KnowledgeChunk))
    chunk.content = "Invented content despite unchanged hash"
    session.commit()
    with pytest.raises(ValueError, match="inconsistent"):
        ingest_source(session, original.root, original.spec, original.storage)


@pytest.mark.integration
def test_database_cannot_approve_without_review(database, original):
    _, _, session = database
    ingest_source(session, original.root, original.spec, original.storage)
    chunk = session.scalar(select(KnowledgeChunk))
    with pytest.raises(IntegrityError), session.begin_nested():
        chunk.verification_status = "approved"
        session.flush()


@pytest.mark.integration
@pytest.mark.parametrize("failure", ["missing", "checksum"])
def test_repeat_import_detects_missing_or_corrupt_original(database, original, failure):
    _, _, session = database
    ingest_source(session, original.root, original.spec, original.storage)
    key = next(iter(original.storage.objects))
    if failure == "missing":
        original.storage.objects.clear()
    else:
        original.storage.objects[key] = b"corrupt"
    with pytest.raises(StorageUnavailable):
        ingest_source(session, original.root, original.spec, original.storage)
    assert session.get(KnowledgeSource, original.spec.source_id).storage_key == key


@pytest.mark.integration
def test_invalid_review_never_writes_storage(database, original):
    _, _, session = database
    original.review.original_sha256 = "0" * 64
    with pytest.raises(ValueError, match="Review"):
        ingest_source(
            session, original.root, original.spec, original.storage, original.review
        )
    assert original.storage.calls == []
    assert session.scalar(select(func.count()).select_from(KnowledgeSource)) == 0


@pytest.mark.integration
@pytest.mark.parametrize("failed_model", [KnowledgeSource, KnowledgeChunk])
def test_database_failure_compensates_only_fresh_object(
    database, original, failed_model
):
    _, _, session = database

    def fail(db, *_):
        if any(isinstance(row, failed_model) for row in db.new):
            raise IntegrityError("private statement", {}, Exception("private details"))

    event.listen(session, "before_flush", fail)
    try:
        with pytest.raises(StorageUnavailable, match="Knowledge metadata"):
            ingest_source(session, original.root, original.spec, original.storage)
    finally:
        event.remove(session, "before_flush", fail)
    assert original.storage.objects == {}
    assert [name for name, _ in original.storage.calls] == ["put", "delete"]
    assert session.scalar(select(func.count()).select_from(KnowledgeSource)) == 0


@pytest.mark.integration
def test_put_acknowledgement_failure_is_compensated(database, original):
    _, _, session = database
    original.storage.fail.add("put")
    with pytest.raises(StorageUnavailable):
        ingest_source(session, original.root, original.spec, original.storage)
    assert original.storage.objects == {}


@pytest.mark.integration
def test_cleanup_failure_logs_only_generated_key(database, original, caplog):
    _, _, session = database
    original.storage.fail.update(("put", "delete"))
    with pytest.raises(StorageUnavailable):
        ingest_source(session, original.root, original.spec, original.storage)
    assert "Storage cleanup required for object knowledge/" in caplog.text
    assert "private connection" not in caplog.text
    assert original.path.name not in caplog.text


@pytest.mark.integration
def test_lost_commit_acknowledgement_keeps_committed_original(
    database, original, monkeypatch
):
    _, _, session = database
    commit = SessionTransaction.commit

    def lost_ack(transaction, *args, **kwargs):
        outermost = transaction.parent is None
        commit(transaction, *args, **kwargs)
        if outermost:
            raise OperationalError("COMMIT", {}, Exception("ack lost"))

    with monkeypatch.context() as patch:
        patch.setattr(SessionTransaction, "commit", lost_ack)
        with pytest.raises(StorageUnavailable):
            ingest_source(session, original.root, original.spec, original.storage)
    assert len(original.storage.objects) == 1
    assert session.get(KnowledgeSource, original.spec.source_id) is not None
    session.rollback()
    ingest_source(session, original.root, original.spec, original.storage)
    assert len(original.storage.objects) == 1


@pytest.mark.integration
def test_old_or_conflicting_review_cannot_revert_approval(database, original):
    _, _, session = database
    ingest_source(
        session, original.root, original.spec, original.storage, original.review
    )
    older = original.review.model_copy(deep=True)
    older.reviewed_at -= timedelta(days=1)
    older.fragments[0].status = "rejected"
    with pytest.raises(ValueError, match="older"):
        ingest_source(session, original.root, original.spec, original.storage, older)
    older.reviewed_at = original.review.reviewed_at
    with pytest.raises(ValueError, match="Conflicting"):
        ingest_source(session, original.root, original.spec, original.storage, older)


@pytest.mark.integration
def test_parallel_imports_create_one_original_and_one_set_of_chunks(database, original):
    settings, _, _ = database
    engine = create_database_engine(settings)

    def run():
        with Session(engine) as session:
            return ingest_source(
                session, original.root, original.spec, original.storage
            )

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            assert (
                list(pool.map(lambda _: run(), range(2)))
                == [original.spec.source_id] * 2
            )
        with Session(engine) as session:
            assert (
                session.scalar(
                    select(func.count())
                    .select_from(KnowledgeChunk)
                    .where(KnowledgeChunk.source_id == original.spec.source_id)
                )
                == 2
            )
        assert len(original.storage.objects) == 1
        assert [name for name, _ in original.storage.calls].count("put") == 1
    finally:
        with engine.begin() as connection:
            connection.execute(
                delete(KnowledgeChunk).where(
                    KnowledgeChunk.source_id == original.spec.source_id
                )
            )
            connection.execute(
                delete(KnowledgeSource).where(
                    KnowledgeSource.source_id == original.spec.source_id
                )
            )
        engine.dispose()


@pytest.mark.integration
def test_import_reloads_review_after_lock_even_with_cached_chunks(database, original):
    _, connection, session = database
    session.expire_on_commit = False
    ingest_source(
        session, original.root, original.spec, original.storage, original.review
    )
    cached = session.scalar(
        select(KnowledgeChunk).where(KnowledgeChunk.chunk_index == 0)
    )
    session.commit()
    updated = original.review.model_copy(deep=True)
    updated.reviewed_at += timedelta(microseconds=1)
    updated.fragments[0].status = "rejected"
    with Session(bind=connection, join_transaction_mode="create_savepoint") as other:
        ingest_source(other, original.root, original.spec, original.storage, updated)
    assert cached.verification_status == "approved"
    with pytest.raises(ValueError, match="older"):
        ingest_source(
            session, original.root, original.spec, original.storage, original.review
        )
