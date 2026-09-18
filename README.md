# LR Desk — LR Inquiry & Employee Attendance

Django + Supabase (PostgreSQL) + plain HTML/CSS, ready to deploy on Vercel.

## Fixed in this version

Two real bugs were found and reproduced (not guessed at):

1. **Every page 500'd once `DEBUG` was off**, because `STORAGES["staticfiles"]`
   used a manifest-based backend (`CompressedManifestStaticFilesStorage`).
   That backend raises a hard `ValueError` from any `{% static %}` tag whose
   file isn't listed in a `staticfiles.json` manifest — and that manifest is
   only produced by `collectstatic`, which this project's Vercel build never
   ran. Fixed by switching to plain `StaticFilesStorage` and setting
   `WHITENOISE_USE_FINDERS = True`, so WhiteNoise serves `static/css/app.css`
   straight from the committed source folder — no build step, no manifest,
   nothing that can go missing. Verified: CSS now returns 200 with real
   content even with zero `collectstatic` step and no `staticfiles_build/`
   directory present at all.
2. **`vercel.json` and `build_files.sh` simplified to match** — the static
   build entry and `/static/` route are gone, since WhiteNoise now handles
   static files at request time via `includeFiles: "static/**"`.

**The "crashes immediately after submitting the login form" symptom is not a
code bug** — it was reproduced directly and traced to one specific cause:
the production database has never had `python manage.py migrate` run
against it, so tables like `auth_user` don't exist yet. Django gets as far
as rendering the login page (no query needed), then the POST hits
`authenticate()`, which queries a table that isn't there, and crashes with
`OperationalError: no such table: auth_user` (Postgres: `relation "auth_user"
does not exist`). This is a very common miss with Supabase + Vercel: the
database you migrate locally against SQLite is not the same database your
deployed app talks to.

### Do this before you redeploy

```bash
# with DATABASE_URL pointed at your Supabase pooler URI
export DATABASE_URL="postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres"
python manage.py migrate
python manage.py createsuperuser
```

If you already ran `seed_demo` against SQLite, run it again with
`DATABASE_URL` set so the same `admin` account and sample rows exist in
Supabase too. Confirm the tables exist by checking the Supabase dashboard's
Table Editor before trying to log in on the live site.

If login still crashes after migrating, the fastest way to find out why is
Vercel's **Runtime Logs** (not the build log) for that specific request —
Project → Deployments → the deployment → Functions/Logs. Paste that
traceback rather than the build log; the build log can't show a login-time
error because the crash happens after the build has already succeeded.

## What is inside

| Module | Where | What it does |
|---|---|---|
| Login | `/` | The only page reachable when signed out. Every other URL bounces back here. |
| Attendance | `/attendance/` | Daily sheet. Mark present; choosing absent, half day or leave opens a reason box that must be filled before the sheet saves. |
| Day register | `/attendance/register/` | Read-only view of any single day with reasons. |
| Employees | `/attendance/employees/` | Add and edit staff. |
| LR inquiry board | `/lr/` | Day-wise dashboard, add inquiries by hand, and a green WhatsApp button per row that opens `wa.me` with the contact's number and a ready message. |
| Saved contacts | `/lr/contacts/` | Every contact person typed once is stored and offered as a choice next time; picking the name fills the number, party and transport automatically. |
| Monthly report | `/reports/attendance/` | Month grid per employee with P/A/H/L/W counts, payable days, all recorded reasons, print view and an Excel download (two sheets: the grid and the absence reasons). |
| Report builder | `/report-builder/` | Upload a raw billing export and get back only the bills whose LR number is still marked **OK**. |

### How the report builder cleans a file

1. Reads every sheet of the `.xlsx` / `.xlsm` / `.csv` you upload.
2. Text to columns — if the whole line sits in column A it is split on the delimiter that fits (tab, `|`, `~`, `;`, `,` or runs of spaces).
3. Finds the header row anywhere in the first 25 rows and matches headings against a list of common spellings (`Party`, `Customer Name`, `Invoice No`, `GR No`, `Qty`, and so on).
4. Drops the junk: blank rows, totals, sub totals, page footers, print headers, and header rows repeated mid-report.
5. Drops every column except **Transport Name / Party Name / Bill No / LR No / LR Date / Cases**, in that order.
6. Keeps only the rows whose LR number cell reads `OK`, `ok`, `O.K.` — the bills whose LR number has not arrived. Rows that already carry a real LR number are removed. Optionally an empty LR cell can count as missing too.

The screen shows how many rows were read, removed and kept before you download, so you can sanity check the result. The download is a formatted `.xlsx` with filters and frozen headers.

---

## Run it locally

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # fill in DATABASE_URL when you have Supabase
python manage.py migrate
python manage.py seed_demo         # creates admin / admin12345 plus sample rows
python manage.py runserver
```

Open http://127.0.0.1:8000 and sign in. **Change the seeded password immediately**, or skip `seed_demo` and run `python manage.py createsuperuser` instead.

Without `DATABASE_URL` the project falls back to a local SQLite file so you can try it before wiring up Supabase.

---

## Connect Supabase

1. Create a project at supabase.com.
2. Project Settings → Database → Connection string → **URI**. Pick the **Session pooler** string (port 5432 / 6543) — the direct connection does not suit serverless.
3. Put it in `.env` as `DATABASE_URL`, replacing `[YOUR-PASSWORD]` with the database password.
4. Run the migrations against it:

```bash
python manage.py migrate
python manage.py createsuperuser
```

Tables are created by Django, so nothing needs to be built by hand in the Supabase table editor. You can still browse the data there.

---

## Deploy to Vercel

1. Push this folder to a GitHub repository.
2. In Vercel, **Add New → Project** and import that repository. Leave the framework preset as *Other*; `vercel.json` handles the rest.
3. Add these environment variables (Production and Preview):

| Key | Value |
|---|---|
| `DJANGO_SECRET_KEY` | a long random string |
| `DEBUG` | `False` |
| `DATABASE_URL` | the Supabase session pooler URI |
| `SITE_URL` | `https://your-project.vercel.app` |
| `TIME_ZONE` | `Asia/Kolkata` |
| `WHATSAPP_COUNTRY_CODE` | `91` |

4. Deploy. Run `python manage.py migrate` locally against the same `DATABASE_URL` whenever models change — Vercel's filesystem is read only, so migrations are not run during the build.

### Things to know about the serverless setup

- `whitenoise` serves the CSS; `build_files.sh` runs `collectstatic` into `staticfiles_build/static`.
- `lrsystem/wsgi.py` exposes `app`, which is what the Vercel Python runtime looks for.
- Uploaded Excel files are held in memory and never written to disk, because the disk is read only. The processed result is passed back to the download button in the page, so nothing is stored between requests.
- `conn_max_age` is 0 so each request opens and closes its own database connection, which is what a pooled Supabase connection expects.

---

## Project layout

```
lrsystem/          settings, urls, wsgi
accounts/          login gate middleware, dashboard, seed_demo command
attendance/        Employee + Attendance models, daily sheet
lrinquiry/         Contact + Inquiry models, board, WhatsApp links
reports/           monthly attendance report and Excel export
reportbuilder/     upload form, cleaning engine (processor.py), download
templates/         all HTML
static/css/app.css single stylesheet
sample-data/       a deliberately messy file for testing the report builder
```

## Status codes used in attendance

`P` present · `A` absent · `H` half day · `L` paid leave · `W` week off.
A reason is required for `A`, `H` and `L`.
