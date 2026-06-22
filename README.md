#  Leatherwork In Traveling — E-Shop for Handmade Leather & Macrame Creations

Django e-commerce project for a leather goods shop — live at [leatherworkintravelingdb.com](https://www.leatherworkintravelingdb.com/fr/)

---

## About this project
 
This is a production e-commerce platform built and maintained for a real, independent craftsperson who designs and sells leather and macramé pieces (bags, accessories, decorative items). The store handles the full customer journey: browsing a filtered catalog, managing a cart, and checking out securely via Stripe — with a bilingual (French/English) storefront targeting both local and international buyers.
 
The project also serves as an open codebase for developers who want to:
 
- See a complete, real-world Django e-commerce implementation (catalog, cart, checkout, legal pages, i18n)
- Contribute to an actively used production project
- Learn from or discuss architectural decisions as they evolve (see [ROADMAP.md](ROADMAP.md) for ongoing work, like the migration to HTMX)
If you're a contributor, see [CONTRIBUTING.md](CONTRIBUTING.md) to get set up . No real Cloudinary or Stripe credentials are needed to start developing, demo data is provided.
 
---

## Features

- Product listing with categories and filters
- Shopping cart
- Secure checkout with Stripe
- Admin dashboard
- Multilingual support (French / English)
- Responsive design

---

## Technologies

- **Backend:** Django 5.1 (Python)
- **Frontend:** HTML, CSS, JavaScript
- **Database:** SQLite (dev) / MySQL (prod)
- **Storage:** Cloudinary
- **Payments:** Stripe
- **Deployment:** PythonAnywhere

---

## Prerequisites

Make sure you have:

- Python 3.10+
- pip

---

## Configuration

### 1. Environment variables

A `.env.example` file is provided as a configuration template.

```bash
cp .env.example .env
```

Then fill in the values for your environment.

Key variables:

```
SECRET_KEY=your-secret-key
DJANGO_ENV=development
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 2. Requirements

The project uses separate requirement files:

| File | Purpose |
|---|---|
| `requirements/base.txt` | Core dependencies |
| `requirements/dev.txt` | Base + development tools (pytest, etc.) |
| `requirements/lock.txt` | Exact versions snapshot |

---

## Quick Start

1. Clone the repository
   ```bash
   git clone https://github.com/peter-francois/leatherwork-in-traveling-db.git
   cd leatherwork-in-traveling-db
   ```

2. Create and activate a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements/dev.txt
   ```

4. Copy and fill the environment file
   ```bash
   cp .env.example .env
   ```

5. Apply migrations
   ```bash
   python manage.py migrate
   ```

6. Create a superuser
   ```bash
   python manage.py createsuperuser
   ```

7. Run the development server
   ```bash
   python manage.py runserver
   ```

App available at http://127.0.0.1:8000/

See CONTRIBUTING.md for the complete development environment setup.

---

## Tests

The project uses [pytest](https://pytest.org) with [pytest-django](https://pytest-django.readthedocs.io) and [pytest-sugar](https://github.com/Teemu/pytest-sugar).

### Running tests

```bash
# All tests
pytest -v

# Specific app
pytest core/tests.py -v

# Specific class
pytest core/tests.py::IndexViewTest -v

# Specific test
pytest core/tests.py::IndexViewTest::test_returns_200 -v
```

### Test structure

Each app has its own `tests.py` file:

```
core/tests.py          ← homepage, robots.txt, sitemaps
catalogue/tests.py     ← products, filters, pagination
panier/tests.py        ← cart, checkout, payment
legal/tests.py         ← cgv, cookies, legal mentions
```

---

## CI/CD

The project uses GitHub Actions for continuous integration and deployment.

### Flow
```
Push on main
     ↓
CI — tests on Python 3.10 and 3.13
     ↓ (only if all tests pass)
CD — automatic deployment to PythonAnywhere
```

### CI — What it does

- Runs on every push and pull request to `main`
- Tests on Python 3.10 (production) and 3.13 (local dev)
- Uses a minimal environment

### CD — What it does

Connects to PythonAnywhere via SSH and runs `scripts/deploy.sh`:

1. `git pull` — fetch latest code
2. `pip install` — update dependencies
3. `python manage.py migrate` — apply migrations
4. `python manage.py collectstatic` — compile static files
5. App reload

### Required GitHub Secrets

| Secret | Description |
|---|---|
| `SECRET_KEY` | Django secret key (dedicated CI key, not production) |
| `PYTHONANYWHERE_USERNAME` | PythonAnywhere username |
| `PYTHONANYWHERE_SSH_KEY` | Private SSH key for deployment |

---

## Project Structure

```
leatherwork-in-traveling-db/
├── .github/workflows/     # CI/CD (GitHub Actions)
├── core/                  # Homepage, base templates
├── catalogue/             # Product listing
├── panier/                # Cart and checkout
├── legal/                 # Legal pages
├── scripts/               # Deploy script
├── page_vente/            # Landing page
├── leatherwork/           # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── lock.txt
├── locale/                # Translation files
├── manage.py
├── pytest.ini
├── .env.example
└── README.md
```

---

## Contact

Questions or feedback? Feel free to reach out.