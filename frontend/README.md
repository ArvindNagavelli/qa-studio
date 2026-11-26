# QA Studio frontend

Next.js 16 (App Router, Turbopack, `src/` dir) + React 19 + TypeScript + Tailwind CSS 4 +
shadcn/ui. Requires Node 22 (see `.nvmrc`). Works on Windows, macOS and Linux.

## Setup

```bash
cd frontend
npm ci                          # installs exactly what package-lock.json pins
cp .env.example .env.local      # then fill in values
npm run dev                     # http://localhost:3000
```

## Scripts

| Command                | Purpose                                               |
| ---------------------- | ----------------------------------------------------- |
| `npm run dev`          | Dev server                                            |
| `npm run build`        | Production build                                      |
| `npm run lint`         | ESLint (flat config: Next core-web-vitals + Prettier) |
| `npm run typecheck`    | Generate Next route types, then `tsc --noEmit`        |
| `npm run format:check` | Prettier check (`format` writes)                      |

## Libraries

- Data fetching: `@tanstack/react-query`
- Forms and validation: `react-hook-form`, `zod`, `@hookform/resolvers`
- Charts: `recharts`
- Google sign-in: `@react-oauth/google`
- UI: shadcn/ui (initialised only; add components with `npx shadcn@latest add <name>`)

## Dependency policy

All versions are pinned exactly (`.npmrc` sets `save-exact`), and `npm audit` must report
0 vulnerabilities. ESLint stays on 9.x until `eslint-config-next`'s plugins
(`eslint-plugin-react`, `jsx-a11y`, `import`) declare ESLint 10 support.

## End-to-end tests

`@playwright/test` is installed, but browsers are **not** downloaded into the repo.
To run e2e tests locally, run `npx playwright install chromium` once (it installs into
the user cache, outside the repo).

## Environment

`NEXT_PUBLIC_*` variables are compiled into the browser bundle, so they must never hold
secrets. The Google client **ID** is public by design; the client **secret** lives only
in the backend.

Fonts are loaded with `next/font/local` from `src/app/fonts/`, so builds work offline.
