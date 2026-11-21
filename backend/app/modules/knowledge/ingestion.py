import argparse
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, uuid4, uuid5

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import create_database_engine
from app.integrations.storage import ObjectStorage, StorageUnavailable
from app.modules.knowledge.audit import DEFAULT_MANIFEST
from app.modules.knowledge.extraction import Extraction, extract_source, sha256
from app.modules.knowledge.manifest import Manifest, SourceSpec, material_path
from app.modules.knowledge.models import KnowledgeChunk, KnowledgeSource
from app.modules.knowledge.review import Reviews, SourceReview, validate_review

logger = logging.getLogger(__name__)


def extraction_hash(extraction: Extraction) -> str:
    return sha256(
        json.dumps(extraction.model_dump(), ensure_ascii=False, sort_keys=True).encode()
    )


def apply_review(
    source: KnowledgeSource, chunks: list[KnowledgeChunk], review: SourceReview
) -> None:
    decisions = {f.locator: f for f in review.fragments}
    for chunk in chunks:
        item = decisions.get(chunk.locator)
        if item is not None:
            previous = chunk.review
            stamp = review.reviewed_at.astimezone(UTC).isoformat()
            if (
                previous
                and datetime.fromisoformat(previous["reviewed_at"]) > review.reviewed_at
            ):
                raise ValueError("Review is older than the stored decision")
            decision = {
                "reviewed_by": review.reviewed_by,
                "reviewed_at": stamp,
                "reason": item.reason,
            }
            if (
                previous
                and previous["reviewed_at"] == stamp
                and (previous != decision or chunk.verification_status != item.status)
            ):
                raise ValueError("Conflicting decisions at the same review time")
            chunk.verification_status = item.status
            chunk.review = decision
    statuses = {chunk.verification_status for chunk in chunks}
    complete = not any("unsupported" in w or "no_text" in w for w in source.warnings)
    source.verification_status = (
        "approved"
        if statuses == {"approved"} and complete
        else "rejected"
        if statuses == {"rejected"}
        else "needs_review"
    )


def discard_original(
    session: Session, key: str, storage: ObjectStorage, commit_pending: bool
) -> None:
    if commit_pending:
        try:
            if session.scalar(
                select(KnowledgeSource.source_id).where(
                    KnowledgeSource.storage_key == key
                )
            ):
                return
        except SQLAlchemyError:
            logger.error("Storage reconciliation required for object %s", key)
            return
    try:
        storage.delete(key)
    except StorageUnavailable:
        logger.error("Storage cleanup required for object %s", key)


def ingest_source(
    session: Session,
    root: Path,
    spec: SourceSpec,
    storage: ObjectStorage,
    review: SourceReview | None = None,
) -> str:
    path = material_path(root, spec.path)
    if path.stat().st_size > 10 * 1024 * 1024:
        raise ValueError("Original exceeds 10 MiB")
    content = path.read_bytes()
    extraction = extract_source(path, content)
    original_hash = sha256(content)
    if review is not None:
        validate_review(review, spec.source_id, original_hash, extraction)
    metadata = {
        "source_id": spec.source_id,
        "title": spec.title,
        "source_type": spec.source_type,
        "assessment_kind": spec.assessment_kind,
        "document_version": spec.document_version,
        "original_path": spec.path,
        "original_filename": path.name,
        "original_sha256": original_hash,
        "original_size": len(content),
        "media_type": extraction.media_type,
        "extractor_version": extraction.extractor_version,
        "extraction_sha256": extraction_hash(extraction),
        "parent_source_id": spec.parent_source_id,
        "legal_status": spec.legal_status,
        "warnings": extraction.warnings,
    }
    key = f"knowledge/{spec.source_id}/{uuid4()}"
    attempted = commit_pending = False
    try:
        with session.begin():
            session.execute(
                select(
                    func.pg_advisory_xact_lock(
                        func.hashtext(f"knowledge:{spec.source_id}")
                    )
                )
            )
            source = session.get(
                KnowledgeSource, spec.source_id, populate_existing=True
            )
            if source is not None:
                if any(
                    getattr(source, name) != value for name, value in metadata.items()
                ):
                    raise ValueError(
                        "Source ID has different content or metadata; "
                        "use a new version ID"
                    )
                stored = storage.get(source.storage_key, source.original_size)
                if sha256(stored) != source.original_sha256:
                    raise StorageUnavailable("Stored original is inconsistent")
                chunks = list(
                    session.scalars(
                        select(KnowledgeChunk)
                        .where(KnowledgeChunk.source_id == spec.source_id)
                        .order_by(KnowledgeChunk.chunk_index)
                        .execution_options(populate_existing=True)
                    )
                )
                if [
                    (c.locator, c.content, c.content_sha256, c.page, c.warnings)
                    for c in chunks
                ] != [
                    (f.locator, f.content, f.content_sha256, f.page, f.warnings)
                    for f in extraction.fragments
                ]:
                    raise ValueError("Stored fragments are inconsistent")
            else:
                source = KnowledgeSource(
                    **metadata, storage_key=key, verification_status="needs_review"
                )
                attempted = True
                storage.put(key, content, extraction.media_type)
                session.add(source)
                session.flush()
                chunks = [
                    KnowledgeChunk(
                        id=uuid5(
                            NAMESPACE_URL,
                            f"kompas:knowledge:{spec.source_id}:{fragment.locator}:{fragment.content_sha256}",
                        ),
                        source_id=spec.source_id,
                        chunk_index=index,
                        locator=fragment.locator,
                        page=fragment.page,
                        content=fragment.content,
                        content_sha256=fragment.content_sha256,
                        warnings=fragment.warnings,
                        verification_status="needs_review",
                    )
                    for index, fragment in enumerate(extraction.fragments)
                ]
                session.add_all(chunks)
            if review is not None:
                apply_review(source, chunks, review)
            session.flush()
            commit_pending = True
        return spec.source_id
    except Exception as error:
        if attempted:
            discard_original(session, key, storage, commit_pending)
        if isinstance(error, SQLAlchemyError):
            raise StorageUnavailable("Knowledge metadata unavailable") from None
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import immutable originals and explicitly reviewed fragments"
    )
    parser.add_argument("materials", type=Path)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--reviews", type=Path)
    args = parser.parse_args()
    manifest = Manifest.model_validate_json(args.manifest.read_text())
    reviews = (
        Reviews.model_validate_json(args.reviews.read_text()).sources
        if args.reviews
        else []
    )
    if {r.source_id for r in reviews} - {s.source_id for s in manifest.sources}:
        raise ValueError("Review refers to a source outside the manifest")
    settings = Settings()
    engine = create_database_engine(settings)
    storage = ObjectStorage(settings)
    try:
        storage.initialize_bucket()
        pending = {s.source_id: s for s in manifest.sources}
        while pending:
            ready = [s for s in pending.values() if s.parent_source_id not in pending]
            for spec in ready:
                review = next(
                    (r for r in reviews if r.source_id == spec.source_id), None
                )
                with Session(engine) as session:
                    ingest_source(session, args.materials, spec, storage, review)
                del pending[spec.source_id]
                print(
                    f"Imported {spec.source_id}; "
                    "original and extraction checksums verified"
                )
    finally:
        storage.close()
        engine.dispose()


if __name__ == "__main__":
    main()
