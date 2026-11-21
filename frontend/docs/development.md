# Frontend development

Run commands from `frontend/` with Node.js 22.13 or newer.

```sh
npm ci
npm run dev
```

The application is available at `http://localhost:3000`. Copy `.env.example` to
`.env.local` and configure the backend URL, Supabase Cloud HTTPS origin, and an
`sb_publishable_` key. Without Auth configuration, `/login` shows a configuration
message and workspace routes redirect there. No demo identity bypass is available.
Fonts are local; AI integration remains a separate backend phase.

## Authentication

The Supabase account must be created by an administrator; disable public sign-up
in the Supabase project. Provision the first local account with the backend
bootstrap command described in `../backend/README.md` (relative to the repo root).
The backend signing algorithm must match the project's asymmetric signing key.

Password sign-in and local sign-out use Server Actions. `@supabase/ssr` stores
the session in HttpOnly, SameSite=Lax cookies (Secure in production); the browser
does not receive tokens in props or application localStorage. Next.js Proxy
refreshes the session, copies updated cookies to the request and response, and
preserves non-cacheable headers. Server Actions use Next.js origin/host CSRF
checks; do not disable them or add broad allowed-origin exceptions.

The workspace layout verifies claims, then forwards the access token to `/me`.
The backend independently verifies it and loads active account roles. The sidebar
uses that profile. Protected routes are dynamic and data fetches use `no-store`.
Future endpoints and Server Actions must perform their own authorization; a
layout or hidden link is not an authorization boundary.

Employee list, UUID profiles (`/employees/{employeeId}`), and command search use
authorized API data. The server fetches employees with the verified session and
`no-store`, deduplicates within a request, and passes only basic employee fields
to command search. Empty lists stay empty; failures do not fall back to demo data.
Unauthorized and missing profiles render the same not-found page. The HR link
and direct `/hr` route require the `HR` role; `ADMIN` alone does not grant it.

Assessment creation, history and UUID detail routes now use API data:

- `/assessments/new` is a four-step setup for an assigned MANAGER. Choices use
  `assigned_only=true`, including for accounts with additional HR/ADMIN roles.
- The Server Action posts only employee ID and periodic type. The API chooses C,
  assessor, catalog, initial revision and status. A/B and first assessment are unavailable.
- One request key stays with the form across retries; selecting another employee
  starts a new key. Pending submission disables changes, and failures preserve input.
- `/assessments/{assessmentId}` loads a saved draft, not an employee slug or local
  workspace. Reload and `?step=` do not mutate it. History is also on employee profiles.
- `src/lib/api/server.ts` shares private authenticated transport for business APIs;
  feature loaders/actions own response handling. Redirects are not swallowed by catches.
- Legacy dashboard links lead to the real assessment list. Demo assistant responses
  are not used as context for persisted assessments.

Criterion/timing editing now uses the API with the assessment's pinned catalog:

- The position/context screen explains manual OSP review; it does not invent a
  document or AI recommendation. Criterion names come from the pinned catalog.
- Explicit criterion and date saves include the last acknowledged revision.
  Only the separate confirmation command advances the workflow.
- Controlled inputs survive API errors and conflicts. A conflict blocks further
  saves and offers the saved version in a separate tab so text can be compared
  and copied without overwriting the newer record. No localStorage persistence.
- Confirmed arrangements are read-only; observation/rating/result editing comes
  in the remaining P4 tasks. Navigating `?step=` never mutates the assessment.

Dashboard, deadlines and HR monitoring still
contain labelled demo data until P7. Legacy flow components remain as the visual
reference for the remaining P4 screens; the UUID route no longer mounts them.
Do not enter real employee information into the legacy local workspace.
There is no automatic migration of demo data.
Live Auth/API/SSR HTTP checks passed; browser verification remains outstanding.
See `docs/backend-progress.md` at the repo root.

Help describes the current MANAGER/HR/ADMIN capabilities and labels unavailable
features explicitly. Empty states use the verified user's roles and current
assignments to offer a next step. A profile visible via HR/ADMIN does not offer
assessment creation unless that account also has MANAGER and that assignment.
Role visibility is presentation only; the API independently authorizes mutations.

API types in `src/lib/api/schema.d.ts` are generated from FastAPI OpenAPI:

```sh
npm run api:types -- http://localhost:8000/openapi.json
npm run format
```

Review and commit generated types whenever an integrated endpoint changes.

## Commands

| Command                | Purpose                                                             |
| ---------------------- | ------------------------------------------------------------------- |
| `npm run dev`          | Start Next.js development mode                                      |
| `npm run build`        | Create the production build                                         |
| `npm start`            | Serve an existing production build                                  |
| `npm run format`       | Format supported files with Oxfmt, including Tailwind class sorting |
| `npm run format:check` | Check formatting without changing files                             |
| `npm run lint`         | Run Oxlint; warnings also fail the command                          |
| `npm run lint:fix`     | Apply safe Oxlint fixes                                             |
| `npm run doctor`       | Run an advisory React Doctor scan                                   |
| `npm run typecheck`    | Generate route types and run strict TypeScript checks               |
| `npm test`             | Run unit tests with Vitest                                          |
| `npm run test:watch`   | Run Vitest in watch mode                                            |
| `npm run check`        | Check formatting, lint, types, and unit tests                       |
| `npm run precommit`    | Format files and run all checks before committing                   |

Run `npm run precommit` before each frontend commit. Run `npm run build` before
finishing an implementation phase. The script is explicit; it does not modify
the root repository's hook configuration.

Run `npm run doctor` periodically and review its findings in context: diagnostics
can include false positives. It is advisory, runs independently of the precommit
checks, and skips the remote score and dependency supply-chain services.

## Code organization

- `src/app/`: thin App Router pages, server layouts, and metadata.
- `src/components/ui/`: shared, accessible presentation components.
- `src/components/layout/`: workspace shell and navigation.
- `src/features/assessments/model/`: typed state, pure calculations, and step guards.
- `src/features/assessments/data/`: the reference competency catalog and demo people.
- `src/features/assessments/components/`: setup, observation, conversation, scoring,
  document, completion, and first-assessment screens.
- `src/features/workspace/`: React state coordination and validated local storage.
- Other `src/features/` folders contain the dashboard, employees, deadlines, help,
  HR, search, and deterministic assistant.
- Tests are colocated with the logic they verify as `*.test.ts` or `*.test.tsx`.

Assessment calculations have no React, Next.js, or browser dependency. Route
parameters are checked before rendering, and saved browser data is validated
before restoration. UI components render user text through React, without raw HTML.

## Styling

`src/styles/tokens.css` defines semantic roles, light/dark values, typography,
control/card radii, shadows, and layout dimensions. `@theme inline` maps runtime
CSS variables to Tailwind v4 utilities. `src/app/globals.css` imports Tailwind and
the tokens, and contains base styles, shared field/table rules, reduced-motion
handling, and print styles.

Preserve the source's system font fallback and SVG geometry. Avoid arbitrary
colors in components; add a semantic token when an additional color role is needed.

## Demo state

- Editable processes are isolated per employee and stored under
  `kompas-workspace-v1` in the current browser.
- The demo retains one current process per employee. Starting a replacement
  prompts before removing existing progress, including unfinished setup.
- Browser storage failures are shown to the user; current in-memory editing
  remains available.
- Reset is available in Help and requires confirmation.
- Assistant replies are deterministic demo content. The transcript lasts for
  the current app session; no model or external API is called.
- Print/PDF uses the browser print dialog and the selected document part.

Git lives at the project root. Stage only `frontend/` paths for frontend work.
