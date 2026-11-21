"""Periodic forms B/C, parts I–II; no promotion request in part III."""

import unicodedata
from dataclasses import dataclass
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Literal
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFError, TTFont
from reportlab.platypus import (
    LongTable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from app.modules.assessments.rules import Result
from app.modules.documents.schemas import PdfGeneration
from app.modules.documents.validation import InvalidDocument

PERIODIC_TEMPLATES = {
    "B": (
        "arkusz-b-2016-47c2b62b-v1",
        "47c2b62b81c49c62f03218dc7a1b5bacc0e21ab7d0c9c1437f56f4e52e1245c3",
    ),
    "C": (
        "arkusz-c-2016-4845015f-v1",
        "4845015f886a56c8715006a5b803e77c6d628eab9aa4989763214c170ba662f0",
    ),
}
LEVELS = (
    "znacznie poniżej oczekiwań",
    "poniżej oczekiwań",
    "na poziomie oczekiwań",
    "powyżej oczekiwań",
    "znacznie powyżej oczekiwań",
)


class PdfUnavailable(Exception):
    pass


def document_font(font_path: Path) -> TTFont:
    try:
        font = TTFont("KompasDocument", str(font_path))
        pdfmetrics.registerFont(font)
        return font
    except (OSError, TTFError):
        raise PdfUnavailable("PDF font unavailable") from None


def validate_pdf_text(value: str, font: TTFont) -> None:
    if any(
        ord(char) not in font.face.charToGlyph
        or (unicodedata.category(char).startswith("C") and char not in "\n\r\t")
        for char in value
        if not char.isspace()
    ):
        raise InvalidDocument(
            "Document contains characters unsupported by the PDF font"
        )


@dataclass(frozen=True)
class PeriodicPdfData:
    assessment_id: str
    revision: int
    employee: dict[str, str]
    assessor_name: str
    criteria: list[tuple[str, bool, int]]
    date_talk: date
    date_assessment: date
    conversation_date: date
    result: Result
    justification: str
    development_conclusions: str
    details: PdfGeneration
    form: Literal["B", "C"]


def render_periodic_pdf(data: PeriodicPdfData, font_path: Path) -> bytes:
    template_version, _ = PERIODIC_TEMPLATES[data.form]
    font = document_font(font_path)
    style = ParagraphStyle(
        "body", fontName=font.fontName, fontSize=9, leading=13, spaceAfter=6
    )
    heading = ParagraphStyle(
        "heading",
        parent=style,
        fontSize=11,
        leading=15,
        spaceBefore=12,
        spaceAfter=10,
        keepWithNext=True,
    )

    def paragraph(value: str, *, title: bool = False) -> Paragraph:
        validate_pdf_text(value, font)
        return Paragraph(
            escape(value).replace("\n", "<br/>"), heading if title else style
        )

    def table(
        rows: list[list[str]], widths: list[float] | None = None, *, repeat: int = 0
    ) -> LongTable:
        return LongTable(
            [[paragraph(cell) for cell in row] for row in rows],
            colWidths=widths or [65 * mm, 105 * mm],
            repeatRows=repeat,
            splitInRow=1,
            style=[
                ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ],
        )

    def signatures(employee: bool = True) -> list:
        roles = (
            ["podpis oceniającego", "podpis ocenianego"]
            if employee
            else ["podpis oceniającego"]
        )
        return [
            Spacer(1, 12 * mm),
            table(
                [
                    [
                        "Miejscowość: ........................",
                        "Data: ........................",
                        role + ": ........................",
                    ]
                    for role in roles
                ],
                [55 * mm, 50 * mm, 65 * mm],
            ),
        ]

    details = data.details
    assessor = [
        ["Imię i nazwisko", data.assessor_name],
        ["Komórka organizacyjna", details.assessor_department],
        ["Stanowisko pracy", details.assessor_position],
    ]
    required = [name for name, mandatory, _ in data.criteria if mandatory]
    additional = [name for name, mandatory, _ in data.criteria if not mandatory]
    story = [
        paragraph(
            f"Załącznik nr {3 if data.form == 'B' else 4} · ARKUSZ {data.form}",
            title=True,
        ),
        paragraph(
            "OCENA OKRESOWA URZĘDNIKA SŁUŻBY CYWILNEJ LUB PRACOWNIKA SŁUŻBY CYWILNEJ",
            title=True,
        ),
        paragraph("CZĘŚĆ I", title=True),
        table([["NAZWA URZĘDU", details.office_name]]),
        paragraph("DANE OCENIANEGO", title=True),
        table(
            [
                ["Imię i nazwisko", data.employee["name"]],
                ["Komórka organizacyjna", data.employee["department"]],
                ["Stanowisko pracy", data.employee["position"]],
            ]
        ),
        paragraph("DANE OCENIAJĄCEGO", title=True),
        table(assessor),
        paragraph("KRYTERIA OCENY I TERMIN SPORZĄDZENIA OCENY", title=True),
        table(
            [
                [
                    "Kryteria obowiązkowe",
                    "Kryteria dodatkowe wybrane przez oceniającego (nie więcej niż 3)",
                ]
            ]
            + [
                [name, additional[index] if index < len(additional) else ""]
                for index, name in enumerate(required)
            ],
            [85 * mm, 85 * mm],
            repeat=1,
        ),
        paragraph(
            "Termin sporządzenia oceny: " + data.date_assessment.strftime("%d.%m.%Y")
        ),
        paragraph("Potwierdzamy:"),
        paragraph(
            "1. Przeprowadzenie rozmowy, o której mowa w § 5 ust. 1 rozporządzenia "
            "Prezesa Rady Ministrów z dnia 4 kwietnia 2016 r. w sprawie warunków "
            "i sposobu przeprowadzania ocen okresowych urzędników służby cywilnej "
            "i pracowników służby cywilnej (Dz. U. poz. 470), i omówienie "
            "w trakcie tej rozmowy wszystkich wymaganych zagadnień."
        ),
        paragraph(
            "2. Zapoznanie ocenianego z kryteriami oceny oraz terminem "
            "sporządzenia oceny."
        ),
        paragraph(
            "Data rozmowy zapisana w aplikacji: "
            + data.date_talk.strftime("%d.%m.%Y")
            + ". Potwierdzenie w aplikacji nie zastępuje podpisów poniżej."
        ),
        *signatures(),
        PageBreak(),
        paragraph("CZĘŚĆ II", title=True),
        table(
            [
                [
                    "DATA PRZEPROWADZENIA ROZMOWY OCENIAJĄCEJ",
                    data.conversation_date.strftime("%d.%m.%Y"),
                ],
                [
                    "OKRES, W KTÓRYM OCENIANY PODLEGAŁ OCENIE",
                    "OD: "
                    + data.date_talk.strftime("%d.%m.%Y")
                    + "   DO: "
                    + details.period_end.strftime("%d.%m.%Y"),
                ],
            ]
        ),
    ]
    for mandatory, title in (
        (True, "KRYTERIA OBOWIĄZKOWE"),
        (False, "KRYTERIA DODATKOWE WYBRANE PRZEZ OCENIAJĄCEGO"),
    ):
        story.append(paragraph(title, title=True))
        rows = [["Kryterium / ocena cząstkowa", "1", "3", "5", "7", "9"]]
        rows.extend(
            [
                [name] + ["X" if score == value else "" for value in (1, 3, 5, 7, 9)]
                for name, is_required, score in data.criteria
                if is_required == mandatory
            ]
        )
        if len(rows) == 1:
            rows.append(["Nie wybrano", "", "", "", "", ""])
        story.append(table(rows, [95 * mm] + [15 * mm] * 5, repeat=1))
    story.append(
        paragraph(
            "Skala: "
            + "; ".join(
                f"{score} — {level}"
                for score, level in zip((1, 3, 5, 7, 9), LEVELS, strict=True)
            )
        )
    )
    mean = data.result.mean
    level = next(index for index, limit in enumerate((2, 4, 6, 8, 9)) if mean <= limit)
    story.extend(
        [
            paragraph(
                f"Średnia arytmetyczna z ocen cząstkowych: {float(mean):.2f}".replace(
                    ".", ","
                ),
                title=True,
            ),
            paragraph("PRZYZNANIE OCENY", title=True),
            table(
                [
                    [
                        "X",
                        "Liczba punktów — średnia arytmetyczna",
                        "Ogólny poziom spełnienia kryteriów oceny",
                    ]
                ]
                + [
                    ["X" if index == level else "", interval, label]
                    for index, (interval, label) in enumerate(
                        zip(
                            (
                                "od 1 do 2",
                                "powyżej 2 do 4",
                                "powyżej 4 do 6",
                                "powyżej 6 do 8",
                                "powyżej 8 do 9",
                            ),
                            LEVELS,
                            strict=True,
                        )
                    )
                ],
                [10 * mm, 65 * mm, 95 * mm],
                repeat=1,
            ),
            paragraph("OCENA OKRESOWA W SŁUŻBIE CYWILNEJ", title=True),
            table(
                [
                    ["POZYTYWNA", "X" if data.result.outcome == "positive" else ""],
                    ["NEGATYWNA", "X" if data.result.outcome == "negative" else ""],
                ]
            ),
            paragraph("UZASADNIENIE PRZYZNANEJ OCENY OKRESOWEJ", title=True),
            paragraph(data.justification or "—"),
            paragraph(
                "WNIOSKI DOTYCZĄCE INDYWIDUALNEGO PROGRAMU ROZWOJU ZAWODOWEGO",
                title=True,
            ),
            paragraph(data.development_conclusions or "—"),
            paragraph(
                "DANE DOTYCZĄCE POPRZEDNIEJ OCENY OKRESOWEJ URZĘDNIKA SŁUŻBY CYWILNEJ",
                title=True,
            ),
        ]
    )
    previous = details.previous_assessment
    if previous is not None:
        story.append(
            table(
                [
                    [
                        "Ocena",
                        "pozytywna" if previous.outcome == "positive" else "negatywna",
                    ],
                    ["Poziom", LEVELS[previous.level - 1]],
                    ["Data sporządzenia", previous.assessed_on.strftime("%d.%m.%Y")],
                ]
            )
        )
    else:
        story.append(
            paragraph(
                "Nie dotyczy — pracownik służby cywilnej."
                if details.civil_service_status == "employee"
                else "Brak poprzedniej oceny — zgodnie z informacją oceniającego."
            )
        )
    story.extend(
        [
            paragraph(
                "CZY DO OCENY OKRESOWEJ DOŁĄCZONO WNIOSEK O PRZYZNANIE "
                "KOLEJNEGO STOPNIA SŁUŻBOWEGO?",
                title=True,
            ),
            table(
                [
                    ["TAK", ""],
                    ["NIE", "X" if details.civil_service_status == "official" else ""],
                    [
                        "NIE DOTYCZY (oceniany jest pracownikiem służby cywilnej)",
                        "X" if details.civil_service_status == "employee" else "",
                    ],
                ]
            ),
            paragraph("DANE OCENIAJĄCEGO", title=True),
            table(assessor),
            *signatures(employee=False),
            paragraph(
                "Przeprowadzono ze mną rozmowę oceniającą oraz zapoznałem(-łam) "
                "się z oceną okresową i wnioskami dotyczącymi indywidualnego "
                "programu rozwoju zawodowego."
            ),
            *signatures(),
            paragraph("Pouczenie", title=True),
            paragraph(
                "Zgodnie z art. 83 ust. 1 ustawy z dnia 21 listopada 2008 r. "
                "o służbie cywilnej od oceny okresowej służy, w terminie 7 dni "
                "od dnia zapoznania się z oceną, sprzeciw do dyrektora generalnego "
                "urzędu. W urzędzie, w którym przepisy nie przewidują tworzenia "
                "stanowiska dyrektora generalnego urzędu, sprzeciw składa się "
                "do kierownika tego urzędu."
            ),
            paragraph("Objaśnienia wzoru", title=True),
            paragraph(
                "Data „od” oznacza datę zapoznania z kryteriami z części I. "
                "Data „do” oznacza datę sporządzenia oceny na piśmie; w przypadku "
                "art. 81 ust. 6, gdy oceny nie sporządzono przed zmianą stanowiska "
                "— ostatni dzień pracy na zajmowanym stanowisku. "
                "Datę „do” wskazał oceniający."
            ),
            paragraph(
                "Wynik pozytywny: średnia powyżej 4 i żadna ocena cząstkowa 1. "
                "Uzasadnienie jest obligatoryjne przy wyniku negatywnym, "
                "fakultatywne przy pozytywnym. Kierunki rozwoju określa się "
                "z uwzględnieniem oceny, zadań i oczekiwań ocenianego."
            ),
            paragraph(
                "Części III nie drukuje się i nie dołącza do arkusza w przypadku "
                "pracownika służby cywilnej oraz w razie nieskładania wniosku "
                "o kolejny stopień służbowy. Oceniający zadeklarował brak "
                "takiego wniosku."
            ),
            paragraph(
                "Dokument wygenerowany z zatwierdzonych danych. "
                "Nie jest podpisany ani doręczony. "
                f"Źródło: dostarczony wzór {data.form} "
                "z 2016 r.; aktualność prawna wymaga odrębnej weryfikacji."
            ),
        ]
    )
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=20 * mm,
        title=f"Arkusz {data.form} — ocena okresowa",
    )

    def footer(canvas, _document):
        canvas.saveState()
        canvas.setFont(font.fontName, 6)
        canvas.drawString(
            20 * mm,
            10 * mm,
            f"Ocena {data.assessment_id} · rewizja {data.revision} · "
            f"{template_version} · strona {canvas.getPageNumber()}",
        )
        canvas.restoreState()

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
