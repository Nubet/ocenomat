import argparse
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

from app.modules.knowledge.extraction import extract_source, normalize_text, sha256
from app.modules.knowledge.manifest import (
    Manifest,
    SourceSpec,
    material_path,
    validate_official_url,
)

DEFAULT_MANIFEST = (
    Path(__file__).resolve().parents[3] / "resources/knowledge-manifest.json"
)


def audit_download_manifest(path: Path) -> dict:
    """Check saved download evidence, including files moved into historical/."""
    path = path.resolve()
    entries = json.loads(path.read_text())["entries"]
    files = [p for p in sorted(path.parent.rglob("*")) if p.is_file()]
    records = []
    for entry in entries:
        filename = entry["filename"]
        if Path(filename).name != filename or "\\" in filename:
            raise ValueError("Download filename must be a basename")
        validate_official_url(entry["url"])
        candidates = [p for p in files if p.name == filename]
        if len(candidates) != 1:
            raise ValueError(f"Missing or ambiguous downloaded original: {filename}")
        original = material_path(
            path.parent, candidates[0].relative_to(path.parent).as_posix()
        )
        content = original.read_bytes()
        records.append(
            {
                "path": original.relative_to(path.parent).as_posix(),
                "url": entry["url"],
                "sha256": sha256(content),
                "bytes": len(content),
                "matches_download": entry["sha256"] == sha256(content)
                and entry["bytes"] == len(content),
            }
        )
    if len({r["path"] for r in records}) != len(records):
        raise ValueError("Duplicate download manifest entry")
    return {
        "files": records,
        "unlisted_files": [
            p.relative_to(path.parent).as_posix()
            for p in files
            if p != path
            and p.relative_to(path.parent).as_posix()
            not in {r["path"] for r in records}
        ],
        "verification_status": "needs_review",
    }


def compare_markdown(original: str, markdown: str) -> dict:
    source_words = normalize_text(original).split()
    markdown_words = normalize_text(markdown).split()
    matcher = SequenceMatcher(None, source_words, markdown_words)
    changes = [op for op in matcher.get_opcodes() if op[0] != "equal"]
    return {
        "normalized_equal": source_words == markdown_words,
        "word_similarity": round(matcher.ratio(), 4),
        "difference_count": len(changes),
        "differences_truncated": len(changes) > 40,
        "differences": [
            {
                "operation": op,
                "original_words": [a, b],
                "markdown_words": [c, d],
                "original_excerpt": " ".join(source_words[a:b])[:300],
                "markdown_excerpt": " ".join(markdown_words[c:d])[:300],
            }
            for op, a, b, c, d in changes[:40]
        ],
    }


def audit_source(root: Path, spec: SourceSpec) -> dict:
    path = material_path(root, spec.path)
    if path.stat().st_size > 10 * 1024 * 1024:
        raise ValueError("Original exceeds 10 MiB")
    content = path.read_bytes()
    if spec.provenance and sha256(content) != spec.provenance.original_sha256:
        raise ValueError("Original does not match the provenance checksum")
    extraction = extract_source(path, content, profile=spec.extraction_profile)
    comparison = None
    if spec.markdown_path:
        markdown = material_path(root, spec.markdown_path).read_text(encoding="utf-8")
        comparison = compare_markdown(
            "\n".join(f.content for f in extraction.fragments), markdown
        )
    return {
        "source": spec.model_dump(mode="json"),
        "original_sha256": sha256(content),
        "original_size": len(content),
        "provenance_checksum_matches": sha256(content)
        == spec.provenance.original_sha256
        if spec.provenance
        else None,
        "representation_checksums": [
            {
                "path": r.path,
                "matches": sha256(material_path(root, r.path).read_bytes()) == r.sha256,
            }
            for r in spec.provenance.representations
        ]
        if spec.provenance
        else [],
        **extraction.model_dump(),
        "fragments": [
            {
                **fragment.model_dump(),
                "content_sha256": fragment.content_sha256,
                "verification_status": "needs_review",
                "review_reasons": [
                    label
                    for label, pattern in (
                        ("numbers_thresholds_or_deadlines", r"\d"),
                        ("negation_exception_or_discretion", r"\bnie\b|wyjąt|\bmoże\b"),
                        ("form_fields", r"☑|☐|\[symbol:|footnoteReference"),
                    )
                    if re.search(pattern, fragment.content, re.IGNORECASE)
                ],
            }
            for fragment in extraction.fragments
        ],
        "markdown_comparison": comparison,
        "verification_status": "needs_review",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit originals independently of Markdown; never approves content"
    )
    parser.add_argument("materials", type=Path)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--downloads-manifest", type=Path)
    args = parser.parse_args()
    manifest = Manifest.model_validate_json(args.manifest.read_text())
    reports = [audit_source(args.materials, spec) for spec in manifest.sources]
    args.output.write_text(
        json.dumps(
            {
                "sources": reports,
                "downloads": audit_download_manifest(args.downloads_manifest)
                if args.downloads_manifest
                else None,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(
        f"Audited {len(reports)} originals; explicit review required. "
        f"Report: {args.output}"
    )
    for report in reports:
        comparison = report["markdown_comparison"]
        differences = comparison["difference_count"] if comparison else "n/a"
        print(
            f"{report['source']['source_id']}: "
            f"{len(report['fragments'])} fragments; "
            f"Markdown difference groups={differences}; "
            f"warnings={','.join(report['warnings']) or 'none'}"
        )


if __name__ == "__main__":
    main()
