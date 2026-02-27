# CLAUDE.md — Ground Truth Generator

You are building a ground truth TOML file for a codebase. This file will be used to evaluate how accurately an AI analysis pipeline detects properties of the codebase. **Accuracy is critical** — every claim in the TOML must be verifiable from the actual source code.

## Your task

Given a repo folder path, explore the codebase and produce a ground truth TOML file following the schema below. The output file should be written to `benchmarks/ground_truth/<repo-name>.toml`.

## Golden rule: verify against code, not docs

**Do NOT trust README files, docs, or comments as ground truth.** They are often outdated, aspirational, or wrong. Every field you fill in must be confirmed by inspecting actual source code:

- **framework**: Check `package.json` dependencies, `requirements.txt`, `Gemfile`, `go.mod`, etc. — not the README badge.
- **language**: Look at the actual file extensions and dominant language in `src/`, `app/`, `lib/`. A project's README may say "TypeScript" but the code may be JavaScript.
- **database**: Look for database client imports, connection strings in config files, ORM model definitions, migration files. Do not rely on "Built with PostgreSQL" in docs.
- **auth**: Find actual auth middleware, session management, login route handlers. Identify the specific library or service (e.g., "NextAuth", "Supabase Auth", "Passport.js"), not just "OAuth".
- **deployment**: Check for `vercel.json`, `Dockerfile`, `fly.toml`, `render.yaml`, `railway.json`, `serverless.yml`, AWS CDK/SAM templates. A Vercel badge in the README is not proof.
- **package_manager**: Check for `package-lock.json` (npm), `yarn.lock` (yarn), `pnpm-lock.yaml` (pnpm), `bun.lockb` (bun), `uv.lock` (uv), `poetry.lock` (poetry), `Pipfile.lock` (pipenv).
- **services**: Only list services that have actual SDK imports, API client usage, or webhook handlers in the code. A "Stripe" badge means nothing if there's no Stripe code.

## How to explore

1. **Start broad**: List the top-level directory structure. Check for `package.json`, `requirements.txt`, `pyproject.toml`, `go.mod`, or equivalent.
2. **Identify the stack**: Read dependency files to determine framework, language, database drivers, auth libraries, and third-party services.
3. **Scan for growth features**: Search for files related to billing/payments, authentication, team/invitation management, analytics/tracking, onboarding flows, email/notifications, referral systems, and freemium/paywall logic.
4. **Verify each feature**: For every feature you plan to include, find at least one concrete file that implements it. Read enough of the file to confirm the feature is real and functional — not a TODO, stub, or dead code.
5. **Check file paths**: Every path in `file_patterns` and `notable_files` must exist in the repo. Verify with a glob or directory listing.

## What to include as expected features

Only include features that relate to **product-led growth (PLG)** — things an analysis tool should detect when evaluating a product's growth potential:

- **Billing/payments**: Stripe, Paddle, LemonSqueezy integration; subscription management; paywall logic; pricing tiers
- **Authentication**: Login/signup flows; OAuth providers; magic links; SSO
- **Team/collaboration**: Invitation systems; role-based access; workspace management; member management
- **Analytics/tracking**: Event tracking; usage analytics; dashboards; product metrics
- **Onboarding**: Guided flows; checklists; progressive disclosure; welcome sequences
- **Email/notifications**: Transactional email; drip campaigns; in-app notifications; push notifications
- **Referral/viral**: Referral programs; invite rewards; social sharing; viral loops
- **Monetization signals**: Usage limits; upgrade prompts; trial management; feature gating

Do **NOT** include generic technical features (routing, state management, CSS framework) — only features with growth relevance.

## Output schema

```toml
# Required: must match the codebase name used in the benchmark config
name = "repo-name"
description = "One-line description of what this project is"

[tech_stack]
# Only include fields you've verified in source code. Omit unknown fields.
framework = "Next.js"         # Primary framework
language = "TypeScript"       # Dominant language by file count
database = "PostgreSQL"       # Confirmed by driver/ORM imports
auth = "NextAuth"             # Specific auth library or service
deployment = "Vercel"         # Confirmed by config file
package_manager = "npm"       # Confirmed by lock file
services = ["Stripe", "Resend"]  # Only services with actual code usage

[industry]
# What kind of product is this?
primary = "DevTools"
# Other labels that would also be reasonable
acceptable_alternatives = ["SaaS", "Productivity"]
# Tags that describe the go-to-market (pick from: B2B, B2C, SaaS,
# Marketplace, API-first, Enterprise, Open Source, Developer Tools)
expected_tags = ["B2B", "SaaS"]

# One entry per growth feature found in the codebase.
[[expected_features]]
name = "billing"                              # Short identifier
description = "Stripe subscriptions with free/paid tiers"  # What it does
file_patterns = ["subscriptions", "stripe"]   # Substrings that match file paths
keywords = ["billing", "subscription", "stripe", "payment"]  # Match in feature names

# Repeat [[expected_features]] for each feature found.

# Key implementation files (relative to repo root).
# Every path listed here MUST exist in the repo.
notable_files = [
    "src/lib/stripe.ts",
    "src/app/api/webhooks/stripe/route.ts",
]
```

## Quality checklist

Before writing the final TOML, verify:

- [ ] Every `tech_stack` field is confirmed by an actual dependency or config file
- [ ] Every service in `services` has real imports/usage in the code (not just docs)
- [ ] Every `expected_features` entry has at least one file that implements it
- [ ] Every path in `file_patterns` matches real files in the repo
- [ ] Every path in `notable_files` exists (verify with a directory listing or glob)
- [ ] The `industry` classification is based on what the product actually does, not marketing copy
- [ ] No features are listed based on TODOs, stubs, or commented-out code
- [ ] `name` matches the folder name of the repo (this will be used in the benchmark config)

## What NOT to do

- Do not guess. If you can't verify something, leave it out.
- Do not list a service just because it appears in a `.env.example` — confirm there's code that uses it.
- Do not include features that are clearly abandoned (dead code, no imports, last touched years ago).
- Do not inflate the feature count. A simple auth check middleware is not worth listing unless there's a real login/signup flow.
- Do not include non-growth features. A REST API router, a CSS theme system, or a test harness are not growth features.
