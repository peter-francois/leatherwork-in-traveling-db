# Contributing to Leather Work In Traveling DB

Thanks for your interest in contributing! This document explains how to set up your environment and the workflow we follow.

## Project overview

This is a Django e-commerce platform for handmade leather and macramé products. It uses:

- Django 5.2 LTS, SQLite
- Cloudinary for image storage
- Stripe for payments
- pytest-django for testing

## Getting started

### Prerequisites

- Python 3.10 or 3.13
- Git

### Setup

1. Fork the repository and clone your fork
2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements/dev.txt
   ```

3. Copy the example environment file and fill in the required values:

   ```bash
   cp .env.example .env
   ```

4. Apply migrations:

   ```bash
   python manage.py migrate
   ```

5. Load demo catalog data (products and categories, with publicly hosted images — no Cloudinary credentials required to view them):

   ```bash
   python manage.py loaddata fixtures/catalog_demo.json
   ```

6. Run the development server:

   ```bash
   python manage.py runserver
   ```

### About Cloudinary and Stripe credentials

You don't need real Cloudinary or Stripe credentials to develop most features. Demo product images are served from public Cloudinary URLs already stored in the fixture data. If you're working on a feature that requires uploading new images or testing payments, create your own free Cloudinary account and Stripe test account, and add your credentials to your local `.env`.

## Branching strategy

We use two long-lived branches:

- `main` — production, always stable, protected
- `dev` — integration branch, all contributions target this branch

Create your working branch from `dev`, using the format:

```
type/short-description
```

Examples:
```
feat/wishlist
fix/pagination-bug
docs/contributing-guide
```

We follow the same `type` prefixes as our commit convention (see below).

## Commit convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): short description
```

Common types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `ci`.

Example:
```
fix(cart): prevent duplicate items when adding the same product twice
```

Write commit messages and code comments in English. French is used only for `verbose_name`, translatable strings, and other user-facing content (see Code conventions below).

## Code conventions

- Code identifiers (variables, functions, classes, fields) are named in English
- User-facing strings use Django's translation system (`{% trans %}` / `gettext`)
- `verbose_name` on model fields is written in French
- Business logic lives in `services.py`; generic helpers live in `utils.py`
- Choice fields use `TextChoices` defined in a dedicated `choices.py`
- Reusable template partials live in the `components/` folder of the app that owns the data they display (e.g. a product card lives in `catalog/components/`, even if it's reused in the cart page)

## Linting and formatting
 
We use [Ruff](https://docs.astral.sh/ruff/) for both linting and formatting Python code. It's already in `requirements/dev.txt`, so it's installed once you've followed the setup above.
 
### Pre-commit hook (recommended)
 
This repo ships a [pre-commit](https://pre-commit.com/) config that runs Ruff automatically on every commit. Set it up once after cloning:
 
```bash
pip install pre-commit
pre-commit install
```
 
From then on, `git commit` will automatically lint and format staged Python files. If a hook modifies a file, the commit is aborted so you can review the changes and re-stage them. This is expected, just run `git add` and commit again.
 
### Manual run
 
You can also run the checks manually at any time:
 
```bash
ruff check . --fix    # auto-fix lint issues where possible
ruff format .          # apply consistent formatting
```
 
Then check what's left manually:
 
```bash
ruff check .
```
 
CI runs `ruff check .` and `ruff format --check .` on every PR — both must pass for the PR to be mergeable. The pre-commit hook catches most issues before you even push, saving you a round-trip through CI.

## Frontend
 
The frontend is currently transitioning toward HTMX for dynamic interactions. This is a work in progress — see [ROADMAP.md](ROADMAP.md) for the current state and which pages follow which pattern. If you're touching cart or catalog templates/JS, check the roadmap or ask a maintainer before picking an approach.
 
A couple of conventions are already stable regardless of the migration:
 
- One JavaScript file per app, no bundler

## Tests

Run the test suite with:

```bash
pytest -v
```

Tests are organized per app, with shared helpers where applicable. Please add or update tests for any behavior change.

## Submitting a pull request

Before opening your pull request, make sure your branch is up to date with `dev`. This catches conflicts early, while they're still yours to resolve, instead of surfacing them later during review.
 
```bash
git checkout dev
git pull
git checkout your-branch-name
git merge dev
```
 
If this produces merge conflicts, resolve them locally, commit the resolution, and push before opening the PR.

1. Push your branch and open a pull request against `dev`
2. Make sure CI passes (tests run automatically on every PR)
3. Once approved, a maintainer will merge it

Direct PRs are welcome — opening an issue first is not required, but feel free to open one if you'd like to discuss an idea before investing time in it.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## Questions?

If anything in this guide is unclear, feel free to open an issue asking for clarification — improving this document is itself a welcome contribution.****