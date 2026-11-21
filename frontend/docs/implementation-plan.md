# Kompas Kompetencji — frontend implementation plan

## Source of truth

The reference is `../docs/inspo/kompas_kompetencji_v02.html`, relative to
the frontend root. Reproduce its effective v0.2 screens, Polish content,
responsive layouts, light/dark themes, and browser-only interactions.
The source contains older function declarations overridden later in the script;
the last declarations determine the actual reference UI.

## Scope

- Workspace: dashboard, assessments, employees, deadlines, help, HR overview.
- Assessment setup: assessment type, employee, position, B/C form selection,
  OSP overview, required criteria, up to three optional criteria, dates,
  confirmations, and save confirmation.
- Periodic assessment: observation journal, conversation preparation,
  behavioral indicators, suggested scores, supervisor approval, summary,
  document parts I/II/III, formal confirmations, and completion.
- First assessment: qualification, introductory conversation, five scores
  on the 3/5/7 scale, report/exam conditions, and result.
- Shared interactions: mobile navigation, theme switch, command search
  with Ctrl/Cmd+K, contextual mock assistant, dialogs, notifications,
  browser-local persistence, reset confirmation, and browser print/PDF.
- No backend endpoints, authentication, live AI, or document-generation service.

## Architecture

Use Next.js App Router, TypeScript strict mode, and Tailwind CSS v4.
Keep route entry points thin. Group feature-specific UI, state, fixtures,
and pure calculations by feature. Shared components must have actual reuse.

```text
src/
  app/
    layout.tsx
    globals.css
    (workspace)/
      layout.tsx
      page.tsx
      assessments/
      employees/
      deadlines/
      help/
      hr/
  components/
    layout/             # shell, sidebar, topbar, mobile navigation
    ui/                 # buttons, badges, avatars, fields, dialogs
  features/
    dashboard/
    assessments/
      components/       # setup, observation, conversation, scoring, documents
      model/            # types, calculations, state transitions
      data/             # reference people, competency catalog, demo scenarios
    employees/
    deadlines/
    help/
    hr/
    assistant/          # deterministic demo replies and drawer
    search/
  lib/
    storage.ts          # versioned browser storage and boundary validation
  styles/
    tokens.css
tests/
  e2e/
docs/
  implementation-plan.md
```

Create route files and subdirectories only as their screens are implemented.
Assessment steps belong under the assessments route; their presentation names
and internal state identifiers need not copy the prototype's string dispatcher.
Top-level navigation uses real links and supports browser history.

### Component tree

```text
RootLayout (server: language, metadata, global styles)
  WorkspaceLayout
    WorkspaceProviders (client: shared demo state and theme)
      AppShell
        Sidebar / MobileNavigation
        Topbar
        Route content
          Dashboard / Assessments / Employees / Deadlines / Help / HR
          AssessmentFlow
            PhaseRail
            Setup / PositionAnalysis / Criteria / Timing
            ObservationJournal / Conversation
            BehavioralRating / Recommendation / Summary
            AssessmentDocument / Completion
          FirstAssessmentFlow
        CommandSearch
        AssistantDrawer
        Dialogs / ToastRegion
```

Keep layouts and static content server-rendered where practical. Put client
boundaries around browser state, forms, overlays, and interactive navigation.
Pure scoring and criterion selection must not depend on React or browser APIs.
Use typed feature state instead of copying the mutable global object,
HTML string rendering, delegated action strings, or `innerHTML`.
Do not add repositories, dependency injection, or an API abstraction without
an actual data source requiring them.

## Design tokens

Preserve source colors and dimensions; do not redesign the application.
Use CSS-first configuration with `@import "tailwindcss"` and `@theme`.
Use `@theme inline` to map runtime semantic variables into utilities.

| Family      | Semantic names                                                                        | Source values / intention                                                      |
| ----------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Backgrounds | `canvas`, `sidebar`, `surface`, `surface-muted`                                       | `#f8f9fb`, `#f5f6f8`, `#ffffff`, `#fbfbfc`                                     |
| Content     | `foreground`, `muted-foreground`, `subtle-foreground`                                 | `#242832`, `#656d7a`, `#757c88`                                                |
| Borders     | `border`, `border-interactive`                                                        | `#e8eaee`, source interactive border                                           |
| Brand       | `primary`, `primary-hover`, `primary-foreground`, `primary-muted`, `primary-border`   | Source brand and button values, explicitly preserving their slight differences |
| Status      | `success`, `warning`, `danger`, `info` and their surface/border roles                 | Match rendered source status treatments                                        |
| Focus       | `ring`                                                                                | `#7c91ff` in light mode                                                        |
| Radii       | `control`, `card`, `choice`, `dialog`, `badge`                                        | Source 10px, 18px, 15px, and pill treatments                                   |
| Shadows     | `card`, `navigation`, `overlay`, `toast`                                              | Source layered shadows                                                         |
| Type        | `font-sans`, `font-document`; `text-caption`, `text-label`, `text-body`, `text-title` | Reference system fallback, Arial document, reference sizes/line heights        |
| Layout      | `spacing-sidebar`, `container-workspace`, navigation/compact breakpoints              | 254px sidebar, 1250px content width, 800px/520px source transitions            |

Runtime variables use role names such as `--surface` and `--foreground`;
Tailwind mappings use namespaces such as `--color-surface` and
`--color-foreground`. Dark mode overrides runtime values through
`data-theme="dark"`. Fixed promotional and print surfaces have their own
semantic tokens because they do not follow the general surface theme.
Retain Tailwind's standard spacing scale. Promote repeated custom values,
not every one-off illustration coordinate, into tokens. Prefer rem units.

## Fidelity and behavior findings

- The HTML names Inter but does not load a font file or external stylesheet.
  Preserve its fallback behavior for the baseline; loading Inter would change
  metrics on machines where the original falls back to a system font.
- Icons are inline SVG symbols. Reuse their exact geometry in typed SVG
  components rather than substituting a different icon library.
- No external images or network-loaded assets are required. OSP files and
  legal citations are demo content, not actual downloadable source documents.
- The source mixes standard Tailwind breakpoints with 1100/800/700/650/520px
  custom media queries. Preserve the effective behavior during visual checks.
- The source includes utility names absent from its compiled CSS. Compare
  rendered output, not only copied class names; compiling them normally may
  change dimensions relative to the reference.
- Later declarations override earlier dashboard, flow, criteria, rating,
  document, assistant, and first-assessment implementations.
- A final duplicate `scoreReadyForNext` uses the original five-item catalog,
  potentially skipping additional/manager criteria. Use the active criterion
  list consistently and test both B/C paths and optional criteria.
- Some source actions reuse another employee's state, and displayed counts
  are static demo numbers. Keep demo presentation, but isolate editable
  assessment state so changes cannot leak between employees.
- The conversation step's final action must be inspected in the browser;
  source markup and the newer `conversation-done` handler may not be wired
  consistently. Preserve the intended conversation-before-scoring flow.
- Local storage restoration needs schema validation and hydration-safe
  initialization. A corrupt or unavailable store must not crash the app.
- Preserve reduced-motion support, keyboard navigation, visible focus,
  dialog focus containment/restoration, and disabled progression rules.
- Printing is a browser dialog; PDF output depends on browser settings.

## Phases and commits

Each phase ends with one short English Conventional Commit with no body.
The Git repository lives at the project root (`hacknation/`). Stage and commit
only frontend paths for this task. Following the user's updated instructions,
continue through all phases without approval gates and do not launch a browser.

1. **Analysis and architecture** — this implementation plan, source inventory,
   architecture, tokens, fidelity risks, and acceptance criteria.
   Commit: `docs: define frontend implementation plan`
2. **Configuration and foundation** — supported stable Next.js/React versions,
   TypeScript, Tailwind v4/PostCSS, lint/format scripts, lockfile, semantic
   tokens, base styles, root layout, and frontend `.gitignore`.
   Inspect installed Next.js documentation before implementation when present.
   Commit: `chore: initialize frontend foundation`
3. **Components and behavior** — shared UI, workspace shell, all reference
   screens, typed demo fixtures, state, calculations, storage, and interactions.
   Add focused calculation/state tests alongside nontrivial logic.
   Commit: `feat: implement competency assessment interface`
4. **Integration and verification** — static source fidelity review,
   calculation/state tests, type checks, lint, production build, and a verification
   record. Browser-based visual, interaction, and print checks are excluded
   at the user's request.
   Commit: `test: verify frontend flows and visual fidelity`

## Verification criteria

- Lint, TypeScript checks, focused unit tests, and production build pass.
- Compare the HTML and Next.js output at the same viewport, fresh demo state,
  browser, system fonts, and color theme. Cover desktop and narrow mobile.
- Inspect every effective screen; preserve Polish copy and section order.
- Exercise periodic C, manager B, optional criteria, first assessment,
  observation entry, conversation editing, approval, documents, and completion.
- Test score suggestions with no observations and ties; test incomplete
  results, one-point negative result, and first-assessment boundary conditions.
- Check criterion limit, required dates, date ordering, confirmation gating,
  reset, reload persistence, invalid storage, theme, search, overlays, and history.
- Check keyboard-only use, radio/tab semantics, focus restoration, mobile menu,
  reduced motion, and no unintended horizontal page overflow.
- Inspect print rendering for the selected document part.
- Before every commit review status, diff, staged paths, and recent history;
  exclude dependencies, build/cache/test output, local environment files,
  credentials, and IDE artifacts.

## Documentation references

- [Next.js project structure](https://nextjs.org/docs/app/getting-started/project-structure)
- [Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components)
- [Tailwind CSS theme variables](https://tailwindcss.com/docs/theme)
- [Tailwind CSS dynamic color variables](https://tailwindcss.com/docs/colors)

Current guidance was checked through Context7 during the analysis phase.
