# Development Plan — Veritas Technical Responsibilities

> This document lists the technical responsibilities for each language/technology, required libraries, APIs to integrate, tools to learn, and a step-by-step development plan to help you start and finish the project.

---

## Goal of this doc

Give every team member (including non-coders) a clear, actionable checklist: what to learn, what to implement, and in which order.

---

## High-level responsibilities by technology

### Frontend (HTML / CSS / Bootstrap / JavaScript)

**Primary role:** Presentation, navigation, and visualisation.

**What to learn / libraries:**

* HTML5 semantics and accessibility basics
* CSS basics + layout (Flexbox / Grid)
* Bootstrap 5 (components, grid, forms)
* Vanilla JavaScript (ES6+) — modules, Fetch API, async/await
* Charting library: Chart.js (simple) or Recharts/D3 (advanced)
* Small helper libraries (optional): dayjs (date handling in browser)

**Responsibility list:**

* Implement responsive views (Home, News detail, Analysis, Profile)
* Build components using Bootstrap (cards, modals, accordions)
* Use Fetch API to call Flask endpoints (JSON)
* Render charts (perspective distribution, credibility) using Chart.js
* Client-side filters (date, area, category) — UI only
* Minimal client validation for forms

---

### Backend (Flask + Python)

**Primary role:** Controller + orchestrator (routes via Flask), call analysis code, talk to DB, return JSON/HTML.

**What to learn / libraries:**

* Python 3.10+ basics (typing, modules)
* Flask (routing, request/response, blueprints)
* Flask-RESTful or Flask API patterns (optional)
* SQLAlchemy (ORM) or `psycopg2-binary` for raw queries
* Flask-Migrate / Alembic for DB migrations
* `requests` for HTTP calls to external APIs
* `python-dotenv` for environment variables
* `python-dateutil` for robust date parsing
* `pytest` for backend tests
* `black`, `flake8`, `isort` for code quality

**Responsibility list:**

* Implement Flask routes listed in system-architechture
* Normalize incoming articles and write to DB (news table)
* Provide API endpoints for frontend (home, news detail, analysis, similar)
* Implement analysis modules as pure Python functions (incident analysis, credibility scoring, perspective distribution, similarity matching)
* Use a configuration file for `SOURCE_CATEGORY` mapping
* Add caching for expensive computations (simple in-memory dict for dev; Redis optional)

---

### Data Structures & Algorithms (Python)

**Primary role:** Efficient and explainable processing.

**What to learn / topics:**

* Python collections: dict, list, set, deque, defaultdict
* Stack / queue behavior using list or deque
* Hash maps (dict) for frequency counting
* 2D arrays (list of lists) or nested dicts for area × incident
* Simple clustering heuristics (key-based clustering)

**Responsibility list:**

* Use dicts for counting and grouping incidents
* Use list stack for user viewed history
* Use nested dicts / 2D array for area × incident type statistics
* Keep algorithms simple and explainable for viva

---

### Database (PostgreSQL)

**Primary role:** Persistent storage for articles, sources, incidents, history.

**What to learn / tools:**

* Basic SQL: CREATE, INSERT, SELECT, JOIN, GROUP BY
* Index basics for performance (on date, source_id, location)
* How to use pgAdmin or psql command line
* Simple migrations using Flask-Migrate or Alembic

**Responsibility list:**

* Create tables: users, sources, news, incidents, incident_news, user_history, analysis_cache
* Add indexes on frequently queried fields (published_date, source_id, location)
* Setup DB connection pooling if needed

---

### News ingestion & APIs

**Primary role:** Collect multiple articles for the same incident.

**APIs / feeds to integrate:**

* NewsAPI.org — global aggregator (free tier has limits)
* GNews or similar aggregators (optional)
* RSS feeds from local news portals (preferred for Ahmedabad local sources)
* Press Information Bureau (PIB) and official government press releases (scrape/RSS)
* Local portals' public endpoints (if any)

**What to learn / libraries:**

* How to call REST APIs using `requests`
* How to parse RSS feeds (feedparser)
* How to scrape (BeautifulSoup) if necessary — but follow robots.txt and legal rules

**Responsibility list:**

* Build a simple ingestion module to fetch articles by keyword + date range
* Normalize source codes and store in `sources` table
* Avoid duplicates (use URL or title+date hash)
* Periodic batch job (cron or scheduled Flask/worker) to cluster new articles

---

### Optional / Advanced (future)

* Redis for caching analysis results
* Celery (or RQ) for background jobs (ingestion, clustering)
* Docker + docker-compose for local dev environment
* CI: GitHub Actions for tests and linting
* Basic deployment on a VPS or platform like Render/Heroku

---

## Minimal tooling & dev environment

* Git (version control) + GitHub
* Python virtualenv or venv / or poetry
* PostgreSQL local dev or Docker image
* Editor: VS Code (with Python extensions)
* Browser dev tools for frontend debugging

---

## Recommended learning path (for team members)

1. Git basics (clone, branch, commit, PR)
2. Basic HTML/CSS + Bootstrap components
3. Vanilla JS + Fetch API and Chart.js usage
4. Python + Flask basic app (simple route → JSON)
5. PostgreSQL basics and connecting from Flask
6. Implement simple ingestion (fetch + store) flow
7. Build one analysis module (perspective distribution)

---

## Step-by-step development plan (practical)

**Week 0 — Setup**

* Create GitHub repo `veritas`
* Setup `doc/` folder and add README, system architecture
* Create `src/` skeleton and basic Flask app
* Setup virtualenv and requirements file
* Create PostgreSQL DB and basic tables (sources, news)

**Week 1 — Ingestion & DB**

* Implement `sources` table and load initial source_map
* Build ingestion module: NewsAPI + RSS parser
* Normalize and insert sample Ahmedabad articles

**Week 2 — Clustering & Perspective**

* Implement simple clustering (location + date + event_type)
* Implement perspective_distribution using source_map
* Build `/analysis/<id>` route returning JSON

**Week 3 — Frontend & Display**

* Build home page and news detail pages (Bootstrap)
* Fetch and display analysis JSON using Fetch API
* Add charts for perspective and credibility

**Week 4 — Similar Incidents & Credibility**

* Implement simple similar-incident matching
* Implement credibility_score function (rule-based)
* Integrate into analysis page

**Week 5 — Polish & Testing**

* Add user_history and recommendations
* Add tests for backend functions (pytest)
* Prepare sample dataset and demo flow

**Week 6 — Finalize & Document**

* Final README, project report, and demo script
* Prepare viva Q&A and slides

---

## Suggested folder structure

```
veritas/
├── doc/
│   ├── README.md
│   └── development-plan.md
├── src/
│   ├── app.py  # Flask entry
│   ├── config.py
│   ├── models/  # DB models
│   ├── services/  # ingestion, analysis
│   ├── routes/  # flask blueprints
│   └── static/  # css, js
├── tests/
├── requirements.txt
└── README.md
```

---

## Coding & documentation best practices

* Keep functions short and single-purpose
* Write docstrings for Python functions
* Use clear commit messages (feature: add ingestion)
* Keep `config/source_map.json` editable and documented
* Add a small `CONTRIBUTING.md` describing how to run locally

---

## Quick starter checklist (do this now)

* [ ] Create GitHub repo and push skeleton
* [ ] Setup Python virtualenv and initial requirements
* [ ] Create local PostgreSQL and create `sources` + `news` tables
* [ ] Add `config/source_map.json` with a few sample sources
* [ ] Implement a simple /health route in Flask
* [ ] Fetch and insert 5 sample Ahmedabad articles


---

*End of development plan.*
