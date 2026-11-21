from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    LongTable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from app.modules.assessments.first_rules import FIRST_ELEMENTS, first_deadlines
from app.modules.assessments.first_schemas import FirstData
from app.modules.assessments.models import Assessment
from app.modules.documents.pdf import document_font, validate_pdf_text
from app.modules.documents.schemas import FirstPdfGeneration
from app.modules.users.models import User

FIRST_TEMPLATE = (
    "pierwsza-ocena-2015-12a6f89a-v1",
    "12a6f89a8bb8b667e2e20b6efd504259c6cc061b36460b8d9b87fed50a5b1721",
)


def render_first_pdf(
    assessment: Assessment, user: User, details: FirstPdfGeneration, font_path: Path
) -> bytes:
    data = FirstData.model_validate(assessment.first)
    font = document_font(font_path)
    style = ParagraphStyle(
        "first", fontName=font.fontName, fontSize=9, leading=13, spaceAfter=7
    )

    def paragraph(value: object) -> Paragraph:
        text = str(value) if value is not None else ""
        validate_pdf_text(text, font)
        return Paragraph(escape(text).replace("\n", "<br/>"), style)

    def table(rows: list[tuple[object, object]]) -> LongTable:
        return LongTable(
            [[paragraph(label), paragraph(value)] for label, value in rows],
            colWidths=[68 * mm, 102 * mm],
            splitInRow=1,
            style=[
                ("GRID", (0, 0), (-1, -1), 0.4, "black"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ],
        )

    deadlines = first_deadlines(
        data.hired_on, data.contract_end, data.replacement_agreed_on
    )
    employee = assessment.employee_snapshot
    result = assessment.result
    story = [
        paragraph("Załącznik nr 2 · ARKUSZ PIERWSZEJ OCENY W SŁUŻBIE CYWILNEJ"),
        paragraph("Rozporządzenie PRM z 23 lipca 2015 r. (Dz.U. poz. 1144)"),
        paragraph("CZĘŚĆ OGÓLNA"),
        table(
            [
                ("Nazwa urzędu", details.office_name),
                ("Imię i nazwisko ocenianego", employee["name"]),
                ("Komórka organizacyjna", employee["department"]),
                ("Stanowisko", employee["position"]),
                ("Data nawiązania stosunku pracy", data.hired_on),
                (
                    "Data ustalenia pierwszej oceny przy zastępstwie",
                    data.replacement_agreed_on,
                ),
                ("Bezpośredni przełożony", user.display_name),
                (
                    "Komórka / stanowisko przełożonego",
                    f"{details.assessor_department} / {details.assessor_position}",
                ),
                (
                    "Kierujący komórką",
                    f"{data.unit_head_name} / {data.unit_head_position}",
                ),
            ]
        ),
        Spacer(1, 5 * mm),
        paragraph("ROZMOWA WSTĘPNA"),
        table(
            [
                ("Data rozmowy", data.intro_on),
                (
                    "Termin złożenia sprawozdania",
                    f"{data.report_from} – {data.report_to}",
                ),
                (
                    "Okres dokonania pierwszej oceny",
                    f"{deadlines.assessment_from} – {deadlines.assessment_by}",
                ),
            ]
        ),
        paragraph(
            "Potwierdzenie rozmowy i zapoznania z terminem: "
            "miejscowość / data / podpis przełożonego / podpis ocenianego: "
            "................................"
        ),
        PageBreak(),
        paragraph("ROZMOWA OCENIAJĄCA"),
        table(
            [
                ("Data rozmowy", data.conversation_on),
                ("Wnioski z rozmowy", data.conversation_notes),
            ]
        ),
        paragraph(
            "Potwierdzenie omówienia wymaganych zagadnień: "
            "miejscowość / data / podpis przełożonego / podpis ocenianego: "
            "................................"
        ),
        paragraph(
            "OCENY CZĄSTKOWE · 3 – poniżej, 5 – na poziomie, 7 – powyżej oczekiwań"
        ),
        table([(name, data.scores[key]) for key, name in FIRST_ELEMENTS.items()]),
        table(
            [
                ("Ocena łączna – średnia arytmetyczna", format(result.mean, ".2f")),
                (
                    "Egzamin",
                    {
                        "passed": "Zaliczony",
                        "failed": "Niezaliczony",
                        "not_applicable": "Nie dotyczy",
                    }[data.exam],
                ),
                ("Podstawa zwolnienia z egzaminu", data.exam_basis),
                (
                    "Sprawozdanie w wyznaczonym terminie",
                    "Tak"
                    if data.report_submitted_on
                    and data.report_from <= data.report_submitted_on <= data.report_to
                    else "Nie",
                ),
                (
                    "PIERWSZA OCENA",
                    "POZYTYWNA" if result.outcome == "positive" else "NEGATYWNA",
                ),
                ("Uzasadnienie", data.justification),
                ("Wnioski dotyczące rozwoju zawodowego", data.development_conclusions),
                ("Data oceny", data.assessed_on),
            ]
        ),
        paragraph(
            "Potwierdzenie dokonania oceny: miejscowość / data / "
            "podpis przełożonego / podpis kierującego komórką: "
            "................................"
        ),
        paragraph(
            "Zapoznanie ocenianego z oceną: miejscowość / data / "
            "podpis ocenianego: ................................"
        ),
        PageBreak(),
        paragraph("Załącznik nr 3 · SPRAWOZDANIE OCENIANEGO"),
        table(
            [
                ("Imię i nazwisko", employee["name"]),
                (
                    "Przepracowany okres objęty sprawozdaniem",
                    f"{data.report_period_from or '—'} – "
                    f"{data.report_period_to or '—'}",
                ),
                (
                    "Data złożenia / brak sprawozdania",
                    data.report_submitted_on or "Nie złożono",
                ),
                ("Zadania", data.report_tasks),
                ("Problemy i ich rozwiązanie", data.report_problems),
                ("Nowe umiejętności i wiedza", data.report_learning),
                ("Wnioski usprawniające", data.report_conclusions),
            ]
        ),
        paragraph(
            "Miejscowość / data / podpis ocenianego: ................................"
        ),
        paragraph(
            "Zapis aplikacji nie zastępuje podpisów, doręczenia "
            "ani włączenia do akt osobowych."
        ),
    ]
    output = BytesIO()
    SimpleDocTemplate(
        output, pagesize=A4, rightMargin=20 * mm, leftMargin=20 * mm
    ).build(story)
    return output.getvalue()
