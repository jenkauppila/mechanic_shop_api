# 🧰 Mechanic Shop API

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-black?logo=flask)](https://flask.palletsprojects.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-red?logo=python)](https://www.sqlalchemy.org/)
[![Swagger](https://img.shields.io/badge/Swagger-UI-green?logo=swagger)](https://swagger.io/tools/swagger-ui/)
[![Postman](https://img.shields.io/badge/Tested%20with-Postman-orange?logo=postman)](https://www.postman.com/)
[![Render](https://img.shields.io/badge/Deploy%20on-Render-blueviolet?logo=render)](https://render.com/)

#

**A comprehensive RESTful API for managing a mechanic shop's operations, including customers, mechanics, service tickets, and inventory management.**

---

## Try It Live

No setup needed. The API is deployed and open to try in your browser.

**Interactive docs:** [mechanic-shop-api-1-ezx9.onrender.com/api/docs](https://mechanic-shop-api-1-ezx9.onrender.com/api/docs)

1. Open the link above, pick any endpoint, click **Try it out**, then **Execute** to see the live response.
2. To try routes marked with a lock:
   1. Register with `POST /customers/` (use made-up details).
   2. Log in with `POST /customers/login` and copy the `auth_token` from the response.
   3. Click **Authorize** at the top of the page, paste the token (just the text starting with `eyJ`, no quote marks), then click **Authorize** and **Close**. Typing `Bearer ` before the token is optional.
   4. Protected routes now work as that customer. Tokens expire after an hour, so log in again if you start getting `401` errors.
3. Prefer Postman? Import [`Mechanic Shop.postman_collection.json`](Mechanic%20Shop.postman_collection.json) and replace `http://127.0.0.1:5000` with `https://mechanic-shop-api-1-ezx9.onrender.com`. The vehicle create, update and delete requests in the collection need a login token, so add one under each request's **Authorization** tab (type **Bearer Token**) or they will return `401`.

**Good to know:**

- The first request may take 30 to 60 seconds while the free-tier server wakes up.
- This is a public demo, so **please use fake names, emails and phone numbers**. Customer details are visible to other visitors.
- Rate limits apply, and all data resets to sample data every night.

---

## Author

**Jen Kauppila**  
_Software Developer | Backend Specialization_

- GitHub: [@jenkauppila](https://github.com/jenkauppila)
- LinkedIn: [linkedin.com/in/jenkauppila](https://www.linkedin.com/in/jenkauppila)
- Website: [Hello World Studio](https://helloworldstud.io)

---

## Table of Contents

1. [Try It Live](#try-it-live)
2. [Author](#author)
3. [Introduction](#introduction)
4. [Tech Stack](#-tech-stack)
5. [Features](#features)
6. [Project Structure](#project-structure)
7. [Prerequisites](#prerequisites)
8. [Installation](#installation)
9. [Usage](#usage)
10. [API Documentation](#api-documentation)
11. [Testing](#testing)
12. [Deployment](#deployment)
13. [CI/CD Pipeline](#cicd-pipeline)
14. [Resolved Issues](#resolved-issues)
15. [Demo Data](#demo-data)
16. [Abuse Protection](#abuse-protection)
17. [Project Background](#project-background)
18. [Acknowledgments](#acknowledgments)
19. [Roadmap](#roadmap)

---

## Introduction

The Mechanic Shop API is a Flask-based REST API for managing customers, vehicles, service tickets, mechanics, and parts inventory. It includes token authentication for customer routes, interactive API documentation, an automated test suite, and a live public demo with sample data that refreshes every night. It is a hardened public demo, not a production system, and its known limitations are documented in [docs/BUG_REPORT.md](docs/BUG_REPORT.md).

Planned next: stock control, meaning tracking parts on hand, reserved for tickets, available, and used, and flagging low stock. See [ROADMAP.md](ROADMAP.md).

### Project Philosophy

As someone with ADHD, I pivoted from the built-in [unittest](https://docs.python.org/3/library/unittest.html) to [pytest](https://docs.pytest.org/en/stable/) during development to leverage its visual, color-coded feedback system. This choice significantly improved my ability to identify patterns and debug tests effectively while maintaining full compatibility with unittest concepts and meeting all learning objectives.

---

## 📦 Tech Stack

| Feature         | Technology / Tool                                                  |
| --------------- | ------------------------------------------------------------------ |
| Language        | Python 3.9+ (CI pinned to 3.12)                                    |
| Framework       | Flask 3.1.1                                                        |
| ORM             | Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.0.41                          |
| Database        | PostgreSQL via Supabase (Production), SQLite (Dev/Test)            |
| Adapter         | pg8000 1.31.2                                                      |
| Auth & Security | JWT (python-jose), Werkzeug, Flask-Limiter                         |
| Documentation   | Swagger UI (flask-swagger-ui)                                      |
| Testing         | Pytest, pytest-html, Postman                                       |
| Deployment      | Gunicorn, Render                                                   |
| CI/CD           | GitHub Actions                                                     |

---

## Features

### 🔐 **Authentication & Security**

- JWT token-based authentication for customers
- Secure password hashing with Werkzeug
- Token-protected routes for sensitive operations
- Rate limiting to prevent API abuse

### 👥 **Customer Management**

- Customer registration and login
- Profile management (view, update, delete)
- Secure token generation for session management
- Customer-specific service ticket access

### 🔧 **Mechanic Operations**

- Mechanic profile management
- Advanced queries: mechanics ranked by ticket completion
- Search functionality for finding mechanics
- Many-to-many relationships with service tickets

### 🚗 **Vehicle Management**

- Vehicles are a dedicated resource linked to a customer (make, model, year, VIN)
- Unique VIN enforcement
- CRUD operations for vehicles
- Service tickets reference a vehicle via `vehicle_id`

### 🎫 **Service Ticket System**

- Complete CRUD operations for service tickets
- Tickets are tied to a specific `Vehicle` record (not just a raw VIN string)
- Dynamic mechanic assignment/removal
- Inventory items (with quantity) can be added to or removed from a ticket
- Deletion is blocked while any mechanics or inventory items are still assigned to the ticket
- Customer-specific ticket retrieval with authentication

### 📦 **Inventory Management**

- Parts inventory with pricing
- Many-to-many relationship with service tickets, tracked via an association model that records **quantity used per ticket**
- CRUD operations for inventory items
- Inventory assignment to service tickets

### ⚡ **Performance Features**

- Pagination for large datasets
- Optimized database queries with SQLAlchemy 2.0
- Connection pooling for database efficiency

### 📊 **Advanced Queries**

- Mechanics ranked by service ticket completion
- Customer service history
- Inventory usage tracking
- Comprehensive filtering and search capabilities

---

## Project Structure

```
mechanic_shop_api/
├── .github/
│   └── workflows/
│       ├── keep-alive.yml             # Scheduled ping to /health, keeps Supabase from auto-pausing
│       ├── main.yaml                  # CI/CD: run tests, deploy to Render on push
│       └── reseed.yml                 # Nightly reset of the live database to the demo data
├── app/
│   ├── blueprints/                    # One package per resource: __init__.py, routes.py, schemas.py
│   │   ├── customers/                 # Customer management endpoints
│   │   ├── inventory/                 # Inventory management endpoints
│   │   ├── mechanics/                 # Mechanic management endpoints
│   │   ├── service_tickets/           # Service ticket operations
│   │   └── vehicles/                  # Vehicle management endpoints
│   ├── static/
│   │   └── swagger.yaml               # API documentation (hand-written)
│   ├── utils/
│   │   └── util.py                    # JWT token creation and token_required decorator
│   ├── __init__.py                    # Flask app factory, / and /health routes
│   ├── extensions.py                  # Marshmallow and rate limiter setup
│   └── models.py                      # Database models
├── docs/
│   └── BUG_REPORT.md                  # Known bugs, their status and GitHub issues
├── tests/                             # pytest suite, one test file per resource plus test_security.py
├── .env.example                       # Template for local environment variables
├── .gitignore
├── CLAUDE.md                          # Working rules for Claude Code in this repo
├── config.py                          # Development, testing and production configurations
├── flask_app.py                       # Production entry point
├── LICENSE
├── Mechanic Shop.postman_collection.json
├── pytest.ini                         # Test configuration
├── README.md                          # Project documentation
├── requirements.txt                   # Python dependencies
├── ROADMAP.md                         # Planned work: stock control and related issues
├── run.py                             # Local development entry point
└── seed.py                            # Demo data seeding script (see Demo Data)
```

---

## Prerequisites

- **Python 3.9+** (Tested with Python 3.12)
- **pip** (Python package manager)
- **Git** (for cloning the repository)
- **PostgreSQL** (for production deployment)

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/jenkauppila/mechanic_shop_api.git
cd mechanic_shop_api
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Environment Configuration

Copy the template at the repo root and fill in your own values:

```bash
cp .env.example .env
```

`.env.example` lists every variable the app reads (`SECRET_KEY`, `DATABASE_URL`, and the optional `PORT`) with placeholder values and a one-line comment for each. `.env` is gitignored, so your real values stay local.

### 5. Database Setup

```bash
# Initialize the database
python -c "from app import create_app; from app.models import db; app = create_app('DevelopmentConfig'); app.app_context().push(); db.create_all()"
```

---

## Usage

### Development Server

```bash
python run.py
```

The API will be available at `http://localhost:5000`

### Production Server

```bash
gunicorn flask_app:app
```

---

## API Documentation

[Navigate to interactive Swagger documentation](https://mechanic-shop-api-1-ezx9.onrender.com/api/docs)

The API is fully documented using **Swagger/OpenAPI 2.0** specification. Each endpoint includes:

- **Path & Method**: GET, POST, PUT, DELETE operations
- **Tags**: Organized by resource (Customers, Mechanics, Service Tickets, Inventory)
- **Summary & Description**: Clear endpoint documentation
- **Parameters**: Required and optional parameters with validation
- **Security**: Token authentication requirements
- **Response Examples**: Sample responses with status codes

### Key Endpoints:

| Resource        | Method | Endpoint                     | Description                                                         |
| --------------- | ------ | ---------------------------- | ------------------------------------------------------------------- |
| Customers       | POST   | `/customers`                 | Register new customer                                               |
| Customers       | POST   | `/customers/login`           | Customer authentication                                             |
| Service Tickets | GET    | `/service_tickets/my-tickets` | Get the logged-in customer's service tickets (Auth)                |
| Vehicles        | POST   | `/vehicles`                  | Register a vehicle on your own account (Auth)                       |
| Vehicles        | PUT    | `/vehicles/<id>`             | Update one of your own vehicles (Auth)                              |
| Vehicles        | DELETE | `/vehicles/<id>`             | Delete one of your own vehicles (Auth)                              |
| Vehicles        | GET    | `/vehicles`                  | List all vehicles                                                   |
| Mechanics       | GET    | `/mechanics`                 | List all mechanics                                                  |
| Mechanics       | GET    | `/mechanics/usage`           | Mechanics ranked by tickets completed                               |
| Service Tickets | GET    | `/service_tickets`           | List all service tickets                                            |
| Service Tickets | POST   | `/service_tickets`           | Create a ticket for a customer's vehicle                            |
| Service Tickets | PUT    | `/service_tickets/<id>/edit` | Add/remove mechanics and inventory (with quantity) on a ticket      |
| Service Tickets | DELETE | `/service_tickets/<id>`      | Delete a ticket (blocked if mechanics/inventory are still assigned) |
| Inventory       | GET    | `/inventory`                 | List inventory items                                                |
| Inventory       | POST   | `/inventory`                 | Add a new inventory item                                            |

---

## Testing

The project includes comprehensive testing using **pytest** with 80 test cases covering:

#### Test Coverage:

- ✅ **Customer Operations**: Registration, login, CRUD operations
- ✅ **Mechanic Management**: Creation, updates, search functionality
- ✅ **Service Tickets**: Create, edit and delete (open routes, no login required), plus token-protected `my-tickets` lookup
- ✅ **Inventory Management**: CRUD operations and ticket integration
- ✅ **Authentication**: Token generation and validation
- ✅ **Error Handling**: Invalid inputs and edge cases
- ✅ **Advanced Queries**: Pagination, search, and ranking

---

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with HTML report
pytest tests/ --html=report.html

# Run specific test file
pytest tests/test_customers.py -v

# Run with coverage
pytest tests/ --cov=app
```

### Test Configuration

The project uses `TestingConfig` with in-memory SQLite database for isolated, fast testing:

```python
class TestingConfig:
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TESTING = True
    DEBUG = True
```

---

## Deployment

### Production Deployment on Render

The API is deployed on **Render** with the following configuration:

#### 1. Database Setup

- PostgreSQL database hosted on **Supabase**
- Connects via Supabase's transaction pooler (port 6543) for compatibility with Render's serverless-style connections
- `DATABASE_URL` set manually as a Render environment variable, pointing at the Supabase connection string

#### 2. Environment Variables

```env
DATABASE_URL=postgresql://...pooler.supabase.com:6543/postgres  # Supabase transaction pooler connection string
SECRET_KEY=production-secret-key
```

`SECRET_KEY` is required in production. It signs the login tokens, so if it is not set the app refuses to start rather than fall back to the default development key, which would let anyone forge tokens (see `create_app` in `app/__init__.py`).

#### 3. Production Configuration

The `ProductionConfig` class handles:

- PostgreSQL URL transformation for pg8000 compatibility
- Runtime database URI resolution
- Production security settings (debug off, proxy-aware client IPs for rate limiting)

#### 4. Web Service Configuration

```yaml
# render.yaml (conceptual)
services:
  - type: web
    name: mechanic-shop-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn flask_app:app
    envVars:
      - key: SECRET_KEY
        value: your-production-secret
```

**Live API**: [https://mechanic-shop-api-1-ezx9.onrender.com](https://mechanic-shop-api-1-ezx9.onrender.com)  
**API Documentation**: [https://mechanic-shop-api-1-ezx9.onrender.com/api/docs](https://mechanic-shop-api-1-ezx9.onrender.com/api/docs)

#### 5. Keep-Alive Workflow

Both free-tier services this project runs on will idle down if nothing touches them: Render spins the web service down after 15 minutes of inactivity, and Supabase pauses the database after 7 days of it. [`keep-alive.yml`](.github/workflows/keep-alive.yml) handles the Supabase side. It is a scheduled GitHub Action that runs every Monday and Thursday and calls the app's `/health` endpoint. That endpoint runs a real `SELECT 1` against the database (see `app/__init__.py`), so each call counts as database activity and keeps Supabase from pausing. It does not stop Render from spinning down: a ping twice a week cannot beat a 15 minute idle timer, so the first request after a quiet spell still waits for Render to wake up. It can also be triggered manually from the Actions tab (`workflow_dispatch`) if you want to wake things up on demand instead of waiting for the schedule.

---

## CI/CD Pipeline

### GitHub Actions Workflow

The project includes a comprehensive [CI/CD pipeline](.github/workflows/main.yaml) with:

#### 1. **Test Job**

- Python 3.12 environment setup
- Dependency installation from requirements.txt
- Pytest execution with verbose output
- Test failure prevention of deployment

#### 2. **Deploy Job** (depends on test success)

- Automatic deployment to Render
- Secure API key management via GitHub Secrets
- Production environment activation

#### 3. **Pipeline Features**

- **Trigger**: Automatic on push to `main` branch
- **Testing**: All 80 tests must pass before deployment
- **Security**: Encrypted secrets for deployment credentials
- **Reliability**: Deployment only occurs after successful testing

#### 4. **GitHub Secrets Configuration**

```
SERVICE_ID: srv-xxxxxxxxxxxxxxxxxxxxx (Render Service ID)
RENDER_API_KEY: rnd_xxxxxxxxxxxxxxxx (Render API Key)
```

---

### Workflow Execution

```yaml
name: Flask CI
on:
  push:
    branches: [main, master]
jobs:
  test: # Run comprehensive test suite
  deploy: # Deploy to Render (only if tests pass)
    needs: test
```

---

## Resolved Issues

Six issues filed against earlier versions of the API were tracked and closed on GitHub. Each one changed the schema, validation, or behavior described above:

| Issue                                                                                      | What it added                                                                                                                                                                                       |
| ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| No Vehicle model exists                                                                    | Added a dedicated `Vehicle` model linked to `Customer`; service tickets now reference a vehicle via `vehicle_id` instead of a raw VIN string                                                        |
| Inventory association table has no quantity field                                          | Added a `quantity` column to the `service_inventory` association object so ticket line items track how many of each part were used                                                                  |
| Write test to check that deleting a service ticket does not release mechanics or inventory | Made ticket deletion consistently blocked (400 error) while mechanics **or** inventory items are still assigned, instead of silently releasing them                                                 |
| Phone number format is not validated                                                       | Added regex-based phone validation to the customer and mechanic schemas (valid 10-digit US format)                                                                                                  |
| Passwords are stored and compared in plaintext                                             | Added password hashing and verification via Werkzeug (`generate_password_hash` / `check_password_hash`)                                                                                             |
| Local dev config uses MySQL, production uses Postgres                                      | Standardized `DevelopmentConfig` and `TestingConfig` on SQLite so local development and tests are fast and dependency-free, while `ProductionConfig` resolves `DATABASE_URL` to Postgres at runtime |

---

## Demo Data

[`seed.py`](seed.py) populates the database with realistic demo data so the live app has something to show besides an empty database: customers, vehicles, mechanics, inventory items, and service tickets (with mechanic assignments and inventory usage).

### Safe to re-run

The script checks row counts before doing anything:

- If the tables it seeds are empty, it seeds directly.
- If any of them already have data, it prints the current counts and requires you to type `reset` at an interactive prompt before wiping and reseeding. Anything else cancels with no changes made.
- With `python seed.py --reset`, the prompt is skipped and the tables are wiped and reseeded automatically. This is what the scheduled reseed workflow uses.

It only touches the tables it owns — `customers`, `vehicles`, `mechanics`, `inventory_items`, `service_tickets`, `service_inventory`, and the `service_mechanics` association table — never schema, migrations, or any other database.

### Requires `DATABASE_URL`

`seed.py` builds the app with `ProductionConfig`, the same config `flask_app.py` uses in production, which resolves `DATABASE_URL` via `config.py`'s `get_database_uri()`. If `DATABASE_URL` isn't set, `ProductionConfig` silently falls back to a local SQLite file — to avoid accidentally seeding the wrong database, the script refuses to run unless `DATABASE_URL` is set and points at something other than SQLite.

`seed.py` loads `.env` automatically via `python-dotenv`, so if your Supabase connection string is already in `.env`, just run:

```bash
python seed.py
```

`seed.py` does not need a real `SECRET_KEY`. It never issues login tokens, so if `SECRET_KEY` is not set it generates a random throwaway key for that run, just enough to pass the production startup check. That is why the reseed workflow only needs the `DATABASE_URL` secret.

The rest of the app (`flask_app.py`, `run.py`) does _not_ load `.env` automatically — for those, export `DATABASE_URL` into your shell first:

```bash
export DATABASE_URL="postgresql://USER:PASSWORD@HOST:6543/postgres"
```

### Model limitations reflected in the seed data

- `Mechanic` has no password field in the current model, so seeded mechanics have no password, matching how the app itself creates them.
- `ServiceTicket` has no status field, so there's no open/completed status to vary — variation instead comes from `service_date` and `service_desc`.

### Scheduled reseed

[`reseed.yml`](.github/workflows/reseed.yml) runs `python seed.py --reset` against the production database every night (and on demand from the Actions tab), so anything added, changed, or deleted through the public API goes back to the sample data. It needs a repository secret named `DATABASE_URL` containing the same Supabase connection string Render uses.

---

## Abuse Protection

The live API is open to the public, so it is protected in layers:

- **Default rate limit** on every route: 200 requests per day and 60 per hour per client IP. The health check, Swagger UI, and static files are exempt.
- **Stricter limits on sensitive routes**: login (5 per minute, 30 per hour) to slow password guessing, registration (5 per hour, 20 per day) to limit scripted account creation, and caps on creating, updating, and deleting records.
- **Authentication and ownership**: vehicle create, update, and delete require a login token, and a customer can only touch their own vehicles. Customer update and delete are also token-protected.
- **No secrets in responses**: password hashes are accepted on input but never returned.
- **Per-client limits behind Render's proxy**: in production the app reads the client IP from the proxy header, so one visitor cannot use up everyone's limit.
- **Nightly reseed** (see above) as a backstop for anything the limits do not stop.

Limits are held in memory, which is correct for the single free-tier instance this runs on. Running more than one instance or worker would need a shared store such as Redis. This project does not currently set one up.

### Known limitations

Some write routes are rate limited but need no login, so anyone can call them:

- **Service tickets**: create, edit, and delete ([issue #8](https://github.com/jenkauppila/mechanic_shop_api/issues/8))
- **Inventory**: update and delete ([issue #9](https://github.com/jenkauppila/mechanic_shop_api/issues/9))
- **Mechanics**: create, update, and delete ([issue #12](https://github.com/jenkauppila/mechanic_shop_api/issues/12)). This needs a staff or admin role, which the app does not have yet.

The rate limits and the nightly reseed contain the damage in the meantime. See [docs/BUG_REPORT.md](docs/BUG_REPORT.md) for steps to reproduce and the other open bugs.

## Project Background

This project began as my final capstone for Coding Temple's Software Development Backend Specialization. It has since continued to develop through independent work on deployment, security hardening, and feature planning. The original development phases were:

1. **Foundation & Documentation**: Core API development with Flask-Swagger documentation
2. **Advanced Features**: Rate limiting, token authentication and advanced queries
3. **Resource Expansion**: Inventory management with many-to-many relationships
4. **Deployment & CI/CD**: Production deployment on Render with automated testing pipeline

## Acknowledgments

This project began as a capstone and was developed independently. Special thanks to:

- **Coding Temple Staff** - Technical Support & Code Reviews
- **Pytest Community** - For creating an accessible testing framework that supports neurodiverse learning styles

### Learning Journey

This project represents the culmination of intensive backend development study, showcasing:

- **RESTful API Design Principles**
- **Test-Driven Development (TDD)**
- **Production Deployment Strategies**
- **CI/CD Pipeline Implementation**
- **Database Design & Optimization**

### Accessibility Considerations

Special recognition for choosing **pytest over unittest** to accommodate ADHD learning needs:

- Visual, color-coded test feedback
- Enhanced readability and debugging capabilities
- HTML report generation for pattern recognition
- Maintained full compatibility with unittest principles

### Technical Growth

From initial Flask routes to production deployment with automated testing - this project demonstrates:

- ✅ **Professional Development Practices**
- ✅ **Comprehensive Testing Strategies**
- ✅ **Security Implementation**
- ✅ **Performance Optimization**
- ✅ **Documentation Excellence**
- ✅ **Deployment Automation**

---

**🔗 Repository**: [https://github.com/jenkauppila/mechanic_shop_api](https://github.com/jenkauppila/mechanic_shop_api)  
**🌐 Live API**: [https://mechanic-shop-api-1-ezx9.onrender.com](https://mechanic-shop-api-1-ezx9.onrender.com)  
**📚 Documentation**: [https://mechanic-shop-api-1-ezx9.onrender.com/api/docs](https://mechanic-shop-api-1-ezx9.onrender.com/api/docs)

---

## Roadmap

Planned work is tracked in [ROADMAP.md](ROADMAP.md) and the open GitHub issues.

  ***

_Built with ❤️ and ☕ by Jen Kauppila_
