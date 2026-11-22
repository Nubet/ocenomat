# Architektura OcenoMat

Ten katalog opisuje prototyp Kompasu Kompetencji. Opisy odnoszą się do kodu
w katalogu roboczym z 22 listopada 2026 r. Część zmian asystenta jest jeszcze
niezacommitowana i nie przeszła pełnej weryfikacji. Status prac i ograniczenia
znajdziesz w [rejestrze postępu](../backend-progress.md).

## Przewodnik

| Dokument | Zakres |
| --- | --- |
| [System i kontenery](system.md) | Komponenty, Docker Compose i uruchamianie. |
| [Proces oceny](assessment.md) | Przepływ pracy, model kompetencji i decyzja przełożonego. |
| [Asystent i RAG](assistant.md) | Pytania formalne, źródła i rozmowa o ocenie. |
| [Analiza OSP](osp.md) | Dokument stanowiska, rekomendacje i cytaty. |
| [Dane i bezpieczeństwo](security.md) | Sesja, role, pliki i granice danych. |
| [Weryfikacja i rozwój](verification.md) | Testy, znane ograniczenia i wdrożenie. |

## Czytanie diagramów

Diagramy są uproszczone. Każdy pokazuje jeden główny przepływ. Linie nie
przedstawiają wszystkich wyjątków, kontroli ani połączeń sieciowych. Pliki
PlantUML znajdują się w [`diagrams/`](diagrams/). Obrazy PNG są w tym samym
katalogu. Diagramy nie zawierają danych pracowników ani sekretów.

Do ponownego wygenerowania obrazów użyj lokalnego PlantUML, na przykład:

```sh
java -jar plantuml.jar -charset UTF-8 -tpng docs/architecture/diagrams/*.puml
```

Pozostałe materiały: [instrukcja demonstracji](../demo-guide.md),
[instrukcja backendu](../../backend/README.md) oraz
[instrukcja środowiska lokalnego](../../infra/README.md).
