import re
from collections import Counter
from itertools import pairwise
from pathlib import Path

from lxml import html

from app.modules.knowledge.extraction import (
    Extraction,
    Fragment,
    extract_pdf,
    normalize_text,
    sha256,
)

STATUTE_SHA256 = "153e60d6fa8c196c4e022c006e363bccec816f30584c9634a3d2d9b24c8b0f3c"
ARTICLE = re.compile(r"(?m)^[ \t]*Art\.[ \t]*(\d+[a-z]*(?:–\d+)?)\.")
FOOTNOTE = re.compile(r"(?m)^(\d+)\) {1,2}\S")


def html_text(element) -> str:
    pieces = []

    def walk(node):
        if not isinstance(node.tag, str) or node.tag in (
            "script",
            "style",
            "nav",
            "noscript",
        ):
            return
        block = node.tag in (
            "div",
            "p",
            "h1",
            "h2",
            "h3",
            "h4",
            "li",
            "tr",
            "details",
            "summary",
            "br",
        )
        if block:
            pieces.append("\n")
        pieces.append(node.text or "")
        for child in node:
            walk(child)
            pieces.append(child.tail or "")
        if node.tag in ("td", "th"):
            pieces.append("\t")
        if block:
            pieces.append("\n")

    walk(element)
    return "\n".join(
        "\t".join(normalize_text(cell) for cell in line.split("\t"))
        for line in "".join(pieces).splitlines()
        if line.strip()
    )


def one(elements, label):
    if len(elements) != 1:
        raise ValueError(f"Expected exactly one {label}")
    return elements[0]


def extract_eli(document) -> list[Fragment]:
    section = one(document.xpath('//section[@id="part_1"]'), "ELI normative section")
    paragraphs = section.xpath(
        './/div[starts-with(@id,"para_") and not(contains(@id,"-"))]'
    )
    if not paragraphs or [p.get("id") for p in paragraphs] != [
        f"para_{i}" for i in range(1, len(paragraphs) + 1)
    ]:
        raise ValueError("Missing or unordered ELI paragraphs")
    # Keep each paragraph whole: separating points would orphan conditions/exceptions.
    fragments = [
        Fragment(
            locator=f"html:#{p.get('id')}",
            content=html_text(p),
            warnings=["temporal_scope_requires_review"]
            if re.search(r"wejścia w życie|wchodzi w życie", html_text(p))
            else [],
        )
        for p in paragraphs
    ]
    preamble = section.xpath(
        './/*[@data-template="xText" and not(ancestor::div[starts-with(@id,"para_")])]'
    )
    if preamble:
        fragments.insert(
            0,
            Fragment(
                locator="html:#part_1/preamble",
                content="\n".join(html_text(p) for p in preamble),
            ),
        )
    for appendix in document.xpath(
        '//section[starts-with(@id,"part_") and @id!="part_1"]'
    ):
        warnings = ["html_annex_tables_and_form_layout_require_review"]
        if appendix.xpath('.//a[contains(@href,"text.pdf")]'):
            warnings.append("unsupported_external_annex_requires_original_pdf")
        fragments.append(
            Fragment(
                locator=f"html:#{appendix.get('id')}",
                content=html_text(appendix),
                warnings=warnings,
            )
        )
    return fragments


def extract_faq(document) -> list[Fragment]:
    article = one(document.xpath('//article[@id="main-content"]'), "FAQ article")
    intro = one(
        article.xpath(
            './p[contains(concat(" ",normalize-space(@class)," ")," intro ")]'
        ),
        "FAQ disclaimer",
    )
    disclaimer = html_text(intro)
    if (
        "charakter opinii" not in disclaimer
        or "nie wiążącej wykładni prawa" not in disclaimer
    ):
        raise ValueError("Missing FAQ non-binding disclaimer")
    questions = article.xpath(".//details")
    if not questions:
        raise ValueError("Missing FAQ questions")
    fragments = []
    for index, question in enumerate(questions, 1):
        summary = one(question.xpath("./summary"), "FAQ question")
        if not re.match(rf"^{index}\.\s", html_text(summary)):
            raise ValueError("Missing or unordered FAQ question numbers")
        if not question.xpath("./*[not(self::summary)]"):
            raise ValueError("Missing FAQ answer")
        fragments.append(
            Fragment(
                locator="html:" + question.getroottree().getpath(question),
                content=disclaimer + "\n\n" + html_text(question),
                warnings=[
                    "non_binding_opinion",
                    "html_footnotes_and_superscripts_require_review",
                ],
            )
        )
    return fragments


def extract_statute(content: bytes) -> Extraction:
    # This profile is only for the audited edition, not a generic Polish-law parser.
    if sha256(content) != STATUTE_SHA256:
        raise ValueError("Statute profile requires the audited 2026/590 PDF checksum")
    pages = extract_pdf(content)
    if (
        len(pages.fragments) != 39
        or "Załącznik do obwieszczenia" not in pages.fragments[2].content
    ):
        raise ValueError("Missing statute annex boundary")
    fragments = [
        Fragment(
            locator=f"notice/page-{p.page}",
            page=p.page,
            content=p.content,
            warnings=[
                "publication_notice_not_statute_article",
                "temporal_scope_requires_review",
            ],
        )
        for p in pages.fragments[:2]
    ]
    current_article = None
    wordings = Counter()
    footnote_numbers = []
    for page in pages.fragments[2:]:
        text = "\n".join(
            line
            for line in page.content.splitlines()
            if not re.fullmatch(r"\s*(?:Dziennik Ustaw.*Poz\. 590|2026-04-30)\s*", line)
        )
        notes = list(FOOTNOTE.finditer(text))
        footnote_numbers.extend(int(n[1]) for n in notes)
        context = ["required_context:notice/page-1", "required_context:notice/page-2"]
        if notes:
            locator = f"annex/page-{page.page}/footnotes"
            fragments.append(
                Fragment(
                    locator=locator,
                    page=page.page,
                    content=text[notes[0].start() :].strip(),
                    warnings=["temporal_scope_requires_review"],
                )
            )
            context.append(f"required_context:{locator}")
            context.append("required_context:annex/page-4/footnotes")
            text = text[: notes[0].start()]
        starts = list(ARTICLE.finditer(text))
        wordings.update(m[1] for m in starts)
        boundaries = [
            (0, current_article),
            *((m.start(), m[1]) for m in starts),
            (len(text), None),
        ]
        occurrences = Counter()
        for (start, number), (end, _) in pairwise(boundaries):
            part = text[start:end].strip()
            if not part:
                continue
            occurrences[number] += 1
            locator = (
                f"annex/page-{page.page}/article-{number}/part-{occurrences[number]}"
                if number
                else f"annex/page-{page.page}/preamble"
            )
            warnings = ["temporal_scope_requires_review", *dict.fromkeys(context)]
            if number and "–" in number:
                warnings.append("omitted_amending_articles_not_available")
            if number and int(re.match(r"\d+", number)[0]) >= 191:
                warnings.append("transitional_or_final_provision_requires_review")
            fragments.append(
                Fragment(
                    locator=locator, page=page.page, content=part, warnings=warnings
                )
            )
        if starts:
            current_article = starts[-1][1]
    if footnote_numbers != list(range(1, 42)):
        raise ValueError("Statute footnote extraction is incomplete")
    by_article = {}
    for fragment in fragments:
        match = re.search(r"/article-([^/]+)/", fragment.locator)
        if match:
            if wordings[match[1]] > 1:
                fragment.warnings.append("parallel_wordings_require_temporal_review")
            by_article.setdefault(match[1], []).append(fragment.locator)
    for fragment in fragments:
        match = re.search(r"/article-([^/]+)/", fragment.locator)
        if match:
            fragment.warnings.extend(
                f"required_context:{locator}"
                for locator in by_article[match[1]]
                if locator != fragment.locator
            )
    return Extraction(
        media_type=pages.media_type,
        fragments=fragments,
        extractor_version="statute-2026-590-v1",
        warnings=[
            *pages.warnings,
            "selected_wording_and_effective_dates_require_review",
            "publication_notice_is_separate_from_statute_annex",
        ],
    )


def extract_official(path: Path, content: bytes, profile: str) -> Extraction:
    if profile == "statute-2026-590-v1" and path.suffix.lower() == ".pdf":
        return extract_statute(content)
    if profile not in ("eli-html-v1", "kprm-faq-v1") or path.suffix.lower() != ".html":
        raise ValueError("Unsupported official extraction profile or format")
    document = html.fromstring(
        content, parser=html.HTMLParser(no_network=True, encoding="utf-8")
    )
    ids = document.xpath("//*[@id]/@id")
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate HTML IDs make citations ambiguous")
    fragments = (
        extract_eli(document) if profile == "eli-html-v1" else extract_faq(document)
    )
    return Extraction(
        media_type="text/html",
        fragments=fragments,
        extractor_version=profile,
        warnings=[
            "official_html_content_requires_review",
            *sorted(
                {
                    warning
                    for fragment in fragments
                    for warning in fragment.warnings
                    if warning.startswith("unsupported")
                }
            ),
        ],
    )
