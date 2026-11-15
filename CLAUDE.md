# CLAUDE.md

Django 5.2 e-commerce site for handmade leather and macramé products (SQLite, Cloudinary for images, Stripe for payments, `django-modeltranslation` for FR/EN content).

Human-facing docs: `CONTRIBUTING.md` (setup, workflow, linting), `ROADMAP.md` (frontend/HTMX migration status). Read the roadmap before choosing a frontend pattern for cart or catalog pages.

## Hard rules

- Never modify `scripts/deploy.sh`.
- Never deploy, and never run anything that targets production.
- Never read `.env`. Use `.env.example` to learn which variables exist.
- Never put secrets in code: read them from environment variables (see `leatherwork/settings.py`).

## Architecture

Project package: `leatherwork/` (settings, root URLs, custom middleware). Single settings module, configured by environment variables; `DJANGO_ENV=test` switches off Cloudinary.

| App | Responsibility |
|---|---|
| `core` | Home and shared pages, sitemaps, site-wide templates and static files |
| `legal` | Legal documents (terms, cookies, legal mentions, privacy policy) |
| `catalog` | Products and categories, translated fields (`translation.py`), product components |
| `cart` | Cart, checkout, Stripe payment, emails, cleanup management commands |

Each app may expose a JSON API in its `api/` package. Reusable template partials live in `<app>/templates/<app>/components/` of the app that owns the data (a product card stays in `catalog/` even when the cart uses it). One JS file per app, no bundler.

## Conventions

- Identifiers (models, fields, functions) in English; `verbose_name` in French; user-facing strings go through `gettext` / `{% trans %}`.
- Choice fields use `TextChoices` defined in the app's `choices.py`, never inline tuples.
- Business logic goes in services, not in views or models: `services.py`, or a `services/` package split by domain when it grows (see `cart/services/`). Generic, domain-free helpers go in `utils.py`.
- Data migrations are written as `RunPython` operations in their own migration file (see `catalog/migrations/0008_copy_name_and_description.py`).
- Commits follow Conventional Commits with a scope: `fix(cart): …`.
- Branch from `develop` and open PRs against `develop` (`main` is production). `CONTRIBUTING.md` still says `dev`: the real branch is `develop`.

## Tests

- `pytest-django`, configured in `pytest.ini`. Tests sit next to each app: a `tests.py`, or a `tests/` package for larger apps (`cart/tests/`).
- Build test data with factory functions in a `helpers.py` (e.g. `make_product()` in `cart/tests/helpers.py`) rather than fixtures or repeated `objects.create()` calls.
- Every behavior change comes with a test.

## Commands

The project uses a plain `venv` + pip with `requirements/` (`base.txt`, `dev.txt`, `lock.txt`), not uv.

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements/dev.txt
cp .env.example .env                       # then fill in values (the human does this)
python manage.py migrate
python manage.py loaddata fixtures/catalog_demo.json
python manage.py runserver                 # dev server
```

Tests (no `.env` needed if these variables are set, as in CI):

```bash
SECRET_KEY=test-key DJANGO_ENV=test DATABASE_URL=sqlite:///db.sqlite3 ALLOWED_HOSTS=localhost pytest -v
```

Lint and format, the same checks CI runs on every PR:

```bash
ruff check . --fix && ruff format .
djlint . --reformat
djlint . --lint        # no autofix: fix reported issues by hand
```

Pre-commit runs Ruff and djLint on staged files (`pre-commit install` once).
