#  Leatherwork In Traveling — E-Shop for Handmade Leather & Macrame Creations

Django e-commerce project for a leather goods shop — live at [leatherworkintravelingdb.com](https://www.leatherworkintravelingdb.com/fr/)

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

## Project Structure

```
leatherwork-in-traveling-db/
├── .github/workflows/     # CI/CD (GitHub Actions)
├── core/                  # Homepage, base templates
├── catalogue/             # Product listing
├── panier/                # Cart and checkout
├── legal/                 # Legal pages
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

## Features

- Product listing with categories and filters
- Shopping cart
- Secure checkout with Stripe
- Admin dashboard
- Multilingual support (French / English)
- Responsive design

---

## Contact

Questions or feedback? Feel free to reach out.