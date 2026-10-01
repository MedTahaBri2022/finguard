# FinGuard

A multi-tenant platform that analyses a company's transaction exports and
reports where money may be leaking: abnormal amounts, duplicate payments,
unusual failure rates and data-quality problems, each with the evidence that
led to it, a risk score and a PDF report.

**FastAPI · SQLAlchemy · Alembic · PostgreSQL · pandas · scikit-learn · Next.js 16 · React 19 · TypeScript · Tailwind CSS · Docker**

[![CI](https://github.com/MedTahaBri2022/finguard/actions/workflows/ci.yml/badge.svg)](https://github.com/MedTahaBri2022/finguard/actions/workflows/ci.yml)

## What it does

1. A client user uploads a CSV or Excel export of transactions.
2. The file is cleaned and its columns are mapped to a canonical schema
   (`montant` becomes `amount`, `statut` becomes `status`, and so on), whatever
   the naming used by the source system. Amounts are normalized to a base
   currency.
3. The detection engine looks for:
   - **amount anomalies**, using robust statistics (median and MAD) on the
     whole batch and on its business contexts (category, counterparty,
     transaction type), an Isolation Forest as supporting evidence, and the
     client's own history when a baseline exists;
   - **probable duplicates** (same reference, nearly identical amount and
     context);
   - **abnormal failure rates** and **currency or data-quality issues**.
4. Each finding carries a severity, a confidence, an amount at risk and the
   list of signals behind it, so an analyst can see *why* it was raised.
5. A global risk score (0 to 100) is computed without counting the same
   transaction twice, alerts are created, and the analysis is stored in the
   client's history. A PDF report can be downloaded.
6. Optionally, an LLM (Groq API) writes a plain-language summary. The analysis
   itself never depends on it: if the call fails, the result is returned
   without the summary.

On the sample dataset of this repository (10,050 synthetic transactions), a
local run flags 679 findings (629 amount anomalies, 50 duplicates), a risk
score of 58 / 100 and about 15.6 M MAD at risk, in roughly 34 seconds.

## Architecture

```
frontend/   Next.js (App Router)
  app/(client)   dashboard, analysis, history, alerts, reports, settings
  app/admin      clients and users administration
  app/login

backend/    FastAPI
  app/routes     auth, analysis, history, alerts, reports, clients, admin_users
  app/services   schema_mapper, data_cleaner, currency/fx, baseline_service,
                 leak_detector, risk_engine, ai_service, auth_service
  app/models     User, ClientProfile, ClientBaseline, Analysis, Finding,
                 Alert, Transaction
  alembic/       database migrations
  tests/         pytest suite
```

- **Multi-tenant.** Every analysis, finding and alert belongs to a client
  profile; a user only sees the data of their own client.
- **Three roles**: `platform_admin` (manages clients and their users),
  `client_admin`, `client_member`.
- **Security**: passwords hashed with Argon2, JWT access tokens signed with a
  key of at least 32 characters, password policy on creation, protected routes
  answer `401` without a valid token.
- **Client baselines**: once a client has enough history, new files are
  compared with that client's own normal behaviour, not only with the batch.

## Run it

Requirements: Docker.

```bash
cp .env.example .env        # then set POSTGRES_PASSWORD, JWT_SECRET_KEY, GROQ_API_KEY
docker compose up -d --build
```

| Service | URL |
| --- | --- |
| Web interface | http://localhost:3000 |
| API documentation | http://localhost:8000/docs |
| PostgreSQL | `localhost:5433` |

Migrations are applied when the backend starts. Create the first
administrator:

```bash
docker compose exec backend python create_user.py     # role: platform_admin
```

Then, from the admin area (or the API): create a client, create a user for
that client, sign in as that user and upload `data/business_transactions.csv`.

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

20 tests on the parts that carry the logic: detection on a clean batch, on an
extreme amount and on a duplicate; bounds of the risk score; mapping of French
column names; password policy, hashing and token tampering; and through the
HTTP API, health, protected routes, login, and the refusal of an upload by a
user who has no client.

CI runs these tests and builds both Docker images.

## API overview

| Method | Path | Access |
| --- | --- | --- |
| POST | `/api/v1/auth/login` | public |
| GET | `/api/v1/auth/me` | signed in |
| POST | `/api/v1/analysis/analyze` | client user (file upload) |
| GET | `/api/v1/history`, `/api/v1/history/{id}` | client user |
| GET | `/api/v1/alerts/`, `/api/v1/alerts/unread` | client user |
| PATCH | `/api/v1/alerts/{id}/read`, `/api/v1/alerts/read-all` | client user |
| GET | `/api/v1/reports/{analysis_id}/pdf` | client user |
| GET, POST, PATCH | `/api/v1/clients` | platform admin |
| GET, POST, PATCH | `/api/v1/admin/clients/{id}/users` | platform admin |

## Limits

- The dataset in `data/` is synthetic (`backend/generate_dataset.py`); the
  detection thresholds have not been validated against real, labelled fraud or
  leak cases, so precision and recall are not measured.
- An analysis runs inside the HTTP request (about 34 s for 10,000 rows); a
  background job would be the next step for larger files.
- Tests cover the core logic and authentication, not every route or the
  front end.
- A Groq API key is required for the API to start, even though the AI summary
  is optional at run time.
- Currency conversion relies on an external rates service.

## License

MIT
