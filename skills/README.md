<!--
Brand hierarchy:
  Skene              - the company (skene.ai)
  Skene Skills       - open-source backend skills for Supabase (skene/skills/)
  Skene CLI          - the agent that installs and operates on skills (skene/cli/)
  Skene Cloud        - triggers, telemetry, analytics (paid)
-->

<div align="center">

# Skene Skills

### Backend skills for Supabase.

Install a CRM into your Supabase project.
Or a helpdesk. Or billing. Or all of them.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Supabase](https://img.shields.io/badge/Supabase-Ready-3ECF8E?logo=supabase&logoColor=white)](https://supabase.com)
[![GitHub Stars](https://img.shields.io/github/stars/SkeneTechnologies/skene?style=flat&label=Stars)](https://github.com/SkeneTechnologies/skene)

</div>

---

```bash
skene install crm
skene install pipeline
skene install support
skene install billing

# or just
skene install all
```

Each skill adds tables, row-level security, and seed data to your Supabase project. Pick what you need. Build the UI yourself.

---

## Why Skene Skills exist

AI can build a frontend in minutes. Cursor, Claude Code, v0, Bolt -- they generate UI fast. But every project still starts with an empty Postgres instance and a blank migration file. The bottleneck moved from "how do I build this" to "what database do I build on top of."

Every founder using AI to build a SaaS product hits the same wall in the first hour. What tables do I need? How do I handle multi-tenancy? What should my RLS look like?

These are solved problems. But everyone solves them alone, from scratch, every time.

Skene Skills are the starting line. Composable backend capabilities you install and build on.

**Your AI agent gets a 2-week head start.** An agent building on a well-defined, documented schema writes better code with fewer tokens than one guessing your data model. Less prompting, more building.

**Every business app stores the same data.** CRM, helpdesk, project management, billing -- 80% of the schema is identical. That 80% should not be custom work every time.

**You own the data.** No per-seat pricing. No rate-limited APIs. No Zapier glue between tools. One Postgres database you control.

## What's a Skene Skill?

A Skene Skill is a packaged backend capability. It gives your Supabase project the ability to do something it couldn't do before.

Each skill includes:
- **Schema** -- tables and enums
- **Security** -- RLS policies and role checks
- **Queries** -- example SQL for common operations
- **Seed data** -- realistic sample data to build against
- **Manifest** -- declares dependencies on other skills

## Available Skills

| Skill | What it gives your Supabase backend | Depends on |
|-------|--------------------------------------|------------|
| `identity` | Organizations, users, teams, roles, permissions | none |
| `crm` | Contacts, companies, relationships | identity |
| `pipeline` | Deals, stages, stage history. Sales, recruiting, fundraising, anything with stages. | crm |
| `tasks` | Projects, tasks, subtasks, dependencies | identity |
| `support` | Tickets with priorities, SLAs, channels | identity |
| `comms` | Unified messages and threads. Email, SMS, chat, notes, call logs. | crm |
| `content` | Documents, folders, versioning, comments | identity |
| `billing` | Products, prices, subscriptions, invoices. Stripe-ready. | crm |
| `calendar` | Events, attendees, recurrence | identity |
| `automations` | Triggers, actions, execution logs | identity |
| `analytics` | Tags, custom fields, activity log | identity |
| `forms` | Form definitions, fields, submissions, file uploads | identity |
| `notifications` | Templates, delivery log, user preferences, push tokens | identity |
| `campaigns` | Email campaigns, segments, lists, send events, engagement tracking | crm |
| `commerce` | Orders, line items, carts, shipping, fulfillment | billing |
| `knowledge` | Articles, categories, publish status | content |
| `approvals` | Approval chains, requests, decisions, delegation | identity |
| `integrations` | Connected apps, OAuth tokens, webhooks, sync logs | identity |
| `compliance` | Consent records, deletion requests, retention policies | identity |

**19 skills. ~72 tables. All with RLS. All multi-tenant.**

## What you can build

```
CRM            = identity + crm + pipeline + comms + analytics
Project tool   = identity + tasks + content + analytics
Helpdesk       = identity + crm + support + comms + knowledge + analytics
Billing app    = identity + crm + billing + commerce + analytics
Marketing      = identity + crm + campaigns + forms + analytics
Internal wiki  = identity + content + knowledge
Full business  = skene install all
```

Every business app is just a combination of skills.

## How it works

```
1. Pick your skills
2. Run skene install <skill>
3. Tables, RLS, and seed data land in your Supabase project
4. Build the UI with whatever framework you want
```

Don't want the CLI? Run the migration.sql files directly:

```bash
psql $DATABASE_URL -f identity/migration.sql
psql $DATABASE_URL -f crm/migration.sql
psql $DATABASE_URL -f pipeline/migration.sql
```

Or use the install script:

```bash
# Clone the repo
git clone https://github.com/SkeneTechnologies/skene.git
cd skene/skills

# Set your database URL
export DATABASE_URL="postgresql://postgres:password@localhost:54322/postgres"

# Install specific skills (dependencies resolve automatically)
./scripts/install.sh crm

# Install everything with seed data
./scripts/install.sh --seed all

# Reset and reinstall
./scripts/reset.sh --seed
```

## Schema design

Every table follows the same rules. No exceptions.

| Rule | What it means |
|------|---------------|
| `org_id` on every table | Multi-tenant by default. Every query is scoped to an organization. |
| RLS on every table | Row-level security enforces tenant isolation at the database layer. |
| `id uuid DEFAULT gen_random_uuid()` | No serial IDs leaking row counts. |
| `created_at` and `updated_at` | Timestamps on every table with an automatic `set_updated_at()` trigger. |
| `metadata jsonb DEFAULT '{}'` | Extensibility without migrations. Store app-specific fields, embeddings, whatever you need. |
| PostgreSQL enums | Status fields use enums, not unconstrained strings. |
| Integer cents for money | No floating point. `value` and `amount` store cents. |
| `entity_type` + `entity_id` | Polymorphic references for comments, tags, activities. Attach anything to anything. |
| `COMMENT ON` every table | Schema is self-documenting. AI agents can read it. |

## AI-ready by default

Every table has comments. Every relationship is explicit. Every naming convention is consistent. Any AI coding tool pointed at your Supabase project can reason about your data model without explanation.

Your prompts go from "I have a contacts table with these columns..." to "add a feature that shows recent activity for a contact." The schema is the context. The agent already knows.

## Demo

```bash
# 1. Install skills into your Supabase project
skene install --seed crm pipeline billing

# 2. Start building
#    Your AI agent now has 12 tables with realistic data to work with.
#    Point it at a SKILL.md and it has full context: columns, types,
#    enums, RLS rules, and working SQL examples.

# 3. Connect Skene Cloud (optional)
#    Skene Cloud reads your installed skills and visualizes the full
#    system: entity relationships, data flow, growth metrics.
#    See https://skene.ai for details.
```

## Built by Skene

Skene Skills is part of [Skene](https://skene.ai) -- growth agents for Supabase. Skene reads your codebase and deploys onboarding, activation, and retention flows directly into your backend. Skene Skills is the data foundation those agents operate on.

Use skills standalone. Or pair them with the Skene CLI for growth infrastructure out of the box.

## Build your own skill

Anyone can create a Skene Skill. Follow the manifest format, write a SKILL.md, include a migration and seed data, submit a PR.

See [docs/build-a-skill.md](docs/build-a-skill.md) for the full guide.

## FAQ

<details>
<summary><b>Do I need the Skene CLI?</b></summary>
<br>
No. Run the migration.sql files manually with psql. The CLI just makes it one command.
</details>

<details>
<summary><b>Can I install just one skill?</b></summary>
<br>
Yes. Only <code>identity</code> is required as a base. Everything else is optional.
</details>

<details>
<summary><b>Can I modify a skill after installing?</b></summary>
<br>
Yes. It is just SQL in your Supabase project. No ORM, no code generation, no lock-in.
</details>

<details>
<summary><b>How is this different from a Supabase template?</b></summary>
<br>
Templates give you a full app. Skills give you composable backend building blocks. Install what you need, skip what you don't, build the UI yourself.
</details>

<details>
<summary><b>Does this work without Supabase?</b></summary>
<br>
The SQL is standard PostgreSQL. RLS policies and <code>auth.uid()</code> are Supabase-specific. You can replace <code>auth.uid()</code> with your own auth layer.
</details>

<details>
<summary><b>What about the shared channel_type enum?</b></summary>
<br>
Both <code>support</code> and <code>comms</code> use a <code>CREATE TYPE IF NOT EXISTS</code> guard. Install them in any order.
</details>

## Contributing

PRs welcome. See [docs/build-a-skill.md](docs/build-a-skill.md) for the skill format.

---

<div align="center">

Built by [Skene](https://skene.ai) -- [MIT License](LICENSE)

</div>
