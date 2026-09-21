# CivicShield

**Turn a confusing moment into a concrete next step.** CivicShield is an NYC-focused assistance navigator built with Python, FastAPI and transparent screening rules. It connects a structured intake to seven curated programs, explains why each appears, and helps users prepare a practical action plan.

Personal portfolio project · NYC assistance navigator · Manual workflow needs no API key

**Your plan:** Use the homepage intake, then track program progress and download your complete plan. Call reminders are another homepage tab.

**Call reminders:** The guide includes unemployment issue preparation and an 8 a.m. New York calendar alert. Download the calendar file, open it and save the event in your calendar; check that alerts are enabled. This works without an AI model or paid API. The app does not place calls or create a phone Clock alarm.

## Run locally

Use Python 3.11 or newer. Run these commands from this project folder:

```sh
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or on macOS/Linux:

```sh
source .venv/bin/activate
```

Then:

```sh
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If PowerShell activation is blocked, use `.\.venv\Scripts\python.exe` in place of `python` without changing your execution policy.

Open [the app](http://127.0.0.1:8000), [interactive API docs](http://127.0.0.1:8000/docs), or [health check](http://127.0.0.1:8000/api/health). SQLite is initialized and seeded on startup. No database service, frontend build or `.env` is required.

## Two-minute demo

1. Click **Try a demo**, then **Find my next steps**. The fictional Brooklyn resident recently lost work and needs help with food, housing and bills.
2. See a food resource, initial matches for implemented checks, and agency-review results for complex benefits. Open **What to prepare & what we checked** to inspect limitations.
3. Change annual income to `23475.01` for a one-person household: the seeded Fair Fares income check fails. Clear annual income: the result becomes **Needs agency review** rather than treating unknown as zero. These examples assume source verification remains within its 90-day window.
4. Optionally configure Groq and try **Describe your situation**. Review its suggestions before applying them to the form.
5. Browse all seven official sources in **Program library**. Print the action plan through the browser.

Sample API request (macOS/Linux or `curl.exe` on Windows):

```sh
curl -X POST http://127.0.0.1:8000/api/screen -H "Content-Type: application/json" --data-binary @data/demo-profile.json
```

## What works

- Responsive frontend served by FastAPI, with intake, program library, printable results, and optional AI-assisted intake.
- Pydantic validation, nullable unknown answers and decimal money handling.
- Deterministic rule results with reasons, missing fields, source metadata and rule versions.
- Seven programs: SNAP, Cash Assistance, One Shot Deal, Homebase, Community Food Connection, Fair Fares NYC and NY Unemployment Insurance.
- SQLAlchemy program model using SQLite; PostgreSQL-compatible column types.
- Source-grounded explanation templates and a retrieval boundary ready for a later AI adapter.
- Reviewable AI suggestions for borough and support categories only.
- Automated API, rule boundary, source freshness, AI validation and privacy tests; GitHub Actions workflow.

## Architecture

```mermaid
flowchart TD
    UI[HTML / CSS / JavaScript] --> API[FastAPI endpoints]
    API --> Profile[Pydantic Situation model]
    Profile --> Rules[Deterministic Python rules]
    DB[(SQLite / PostgreSQL program catalog)] --> Rules
    Rules --> Decision[Frozen Decision]
    Decision --> Explanation[Source-grounded explanation]
    DB --> Retrieval[Curated context retrieval]
    Retrieval --> Explanation
    Explanation --> UI
    UI --> AI[Optional Groq intake extraction]
    AI --> Review[User reviews suggestions]
    Review --> UI
```

```text
app/
  main.py          HTTP routes, lifespan and response privacy headers
  schemas.py       Validated intake input
  database.py      SQLAlchemy model and idempotent catalog seed
  rules.py         Pure screening functions and frozen Decision
  explanations.py Retrieval/context seam and deterministic templates
  intake_ai.py     Restricted AI suggestions and provider boundary
static/            Plain frontend: no Node installation needed
data/              Curated programs and fictional demo inputs
tests/             Boundary and integration tests
docs/              Learning guide, source policy, validation notes
```

The database stores **only the program catalog**. Intakes and cases are held in memory, not persisted by the app. No analytics, browser storage or remote fonts are used. Normal server access logs include request paths, not request bodies. Browser print/export creates a local copy at the user's direction.

## Screening semantics

| Status | Meaning |
|---|---|
| `preliminary_match` | Only the implemented initial checks match; the agency still decides. |
| `needs_review` | Missing facts, complex criteria or source freshness prevent screening. |
| `criteria_not_met` | A specific implemented check failed; this is not a government denial. |
| `resource` | A resource referral, not an eligibility decision. |
| `not_requested` | Outside the needs selected; still available in the library. |
| `out_of_scope` | Outside this MVP's NYC coverage, not outside program eligibility. |

**Scope matters:** Fair Fares checks residence, age and the cited annual income table. Homebase checks residence and self-reported housing risk. Unemployment checks initial work-history/separation/availability indicators, not wage qualification. SNAP, Cash Assistance and One Shot Deal deliberately require agency review: the MVP does not pretend to implement their full rules. Monthly income is collected for structured intake but is not currently used in those incomplete financial rules. Annual income is supplied separately and never inferred from current monthly income. No benefit dollar amount is calculated.

The source's `last_updated` is distinct from our `verified_at`. Records reviewed more than 90 days ago (or in the future) return `needs_review` for selected programs. This is a project freshness policy, not a government rule. Updating source dates requires an actual review; do not simply reset the date. See [source policy](docs/SOURCES.md).

## AI / RAG boundary

Program cards use deterministic templates. `app/cases.py` builds tasks from a user-confirmed profile. Only optional intake suggestions call Groq. The model can suggest borough and support categories, never eligibility, income or household size. The user explicitly applies suggestions before screening. `retrieve_context()` selects a curated program record by ID; it is not vector search. No interview or automated caller is included.

## Database configuration

Optionally copy `.env.example` to `.env`. For PostgreSQL, create an empty database, install `psycopg[binary]`, and set `DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/civicshield` in `.env`. Restart the app. The same model and seed routine create the catalog. Keep credentials out of Git.

PostgreSQL DDL compilation is tested; a live PostgreSQL service has not been integration-tested in this MVP. `create_all()` supports the initial schema only. Add Alembic migrations before evolving a deployed database. Startup upserts the seven seed IDs and overwrites edits to those catalog rows; change the reviewed JSON seed to make persistent catalog updates.

## Tests

```sh
python -m pytest -q
```

Tests use a separate temporary SQLite database. Rule tests freeze their evaluation date so future source expiration does not break boundary tests. The CI workflow runs Python 3.11 and 3.12. See [validation notes](docs/VALIDATION.md).

## Learn Python while building

Start with [the short learning path](docs/LEARNING.md). Read one function, change one case and run one test. The order follows this app: models → functions → dataclasses → lists/dictionaries → database sessions → HTTP endpoints.

## Next iterations and limits

1. Review requirements with a benefits navigator; expand validated financial rules with effective-date tables and regression fixtures.
2. Evaluate the new natural-language intake with the configured Groq model and real-world test scenarios; improve extraction and factual grounding.
3. Evaluate extraction accuracy across varied descriptions and ambiguous situations.
4. Add migrations and PostgreSQL integration tests. Before public use, add HTTPS, request-size limits, rate limiting, operational privacy controls and accessibility audits.

This personal portfolio project provides preliminary guidance; it is not a complete benefits eligibility service. No public deployment or GitHub repository has been created.

## Phone experience

Food cards link directly to the NYC Food Help Finder, where users enter their ZIP code. Relevant programs link to ACCESS HRA and both official mobile app stores. The supplied FF-14 (E), dated February 10, 2025, is served unchanged as a suggested-document checklist; the actual application specifies which documents are needed.

Use Add to Home Screen for an app icon. Real phone use requires hosting at an HTTPS address reachable from the phone; the development localhost address points to the device opening it. No deployment has been performed. Calendar alerts depend on saving the event and device notification settings. No private case data is cached by a service worker.

## Homepage workflow update

The separate goal-builder page is removed; `/guide` redirects to the homepage call-reminder tab. Screen once on the homepage, add program progress and notes, then download the whole plan as a readable HTML file (print it to PDF from a browser if needed). Downloads contain personal answers and notes; keep them private.

## Render deployment

A Free web-service configuration is included in `render.yaml`. See [deployment instructions](docs/RENDER.md) for GitHub setup, commands and free-plan limits. Deployment is not yet live.


## Current workflow: optional AI intake

Understand a notice and its PDF parsing endpoints have been removed. Describe your situation on the homepage uses Groq to suggest only borough and support categories. Review the preview, choose Use these suggestions, then complete the manual form and submit to the deterministic screening engine. No AI eligibility decisions, interviews or translation.

Set `GROQ_API_KEY` privately in `.env` or Render Environment and `GROQ_MODEL=openai/gpt-oss-120b`. Restart after changes. A consent checkbox precedes each request. Descriptions are sent to Groq, not stored by this app. Avoid private identifiers. Unknown values remain unknown; AI never supplies income or household size. Twenty attempts/hour and one concurrent request are enforced per server process; these are not durable billing limits.
