# Veritas - News Analytics Platform

### Production-Ready Flask Application with PostgreSQL

A data-driven local news portal that analyzes incidents, scores credibility, compares reporting perspectives (public, neutral, political), identifies similar incidents, and provides personalized recommendations using backend logic and persistent storage.

---

## Tech Stack

- **Backend**: Flask 3.0.0, Python 3.x
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Frontend**: Bootstrap 5, Chart.js
- **Migrations**: Flask-Migrate
- **Architecture**: Blueprint pattern, Factory pattern, Service layer

---

## Quick Start

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/AhmadRaza24h/Veritas.git
cd Veritas
```

2. **Create and activate virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env file with your database credentials
```

5. **Initialize the database**
```bash
# Create database in PostgreSQL
createdb veritas_dev

# Initialize tables
python scripts/init_db.py

# Seed with sample data (optional)
python scripts/seed_data.py
```

6. **Run the application**
```bash
python run.py
```

The application will be available at `http://localhost:5000`

---

## Project Overview

## Problem Statement

Local news readers often consume information from a **single source**, or consume news without analytical context,, which can lead to:

* Partial understanding of incidents
* Over-reliance on one reporting style
* Difficulty in judging credibility

**Veritas** addresses this by aggregating and analyzing multiple reports of the same incident and presenting structured insights instead of opinions.

---

## Core Features

### 1. Incident Analysis

* Groups news reports related to the same incident
* Analyzes frequency based on area, time, and incident type
* Identifies commonly affected groups

### 2. Credibility Scoring

* Assigns a rule-based credibility score to an incident
* Factors include:

  * Number of independent sources
  * Clarity of location and details
  * Completeness of information

### 3. Perspective Distribution Analysis

Each news source is categorized using **predefined source metadata** into:

* **Public** – citizen-focused, people-impact reporting
* **Neutral** – fact-based, balanced reporting
* **Political** – government and policy-driven reporting

For every incident, Veritas shows how coverage is distributed across these three perspectives.

> The system does not judge opinions or analyze article sentiment. It only counts predefined source categories.

---

### 4. Similar Incident Comparison

* Compares the current incident with past incidents
* Uses factors such as location, type, and time period
* Helps users identify recurring patterns

---

### 5. Recommended for You

* Tracks user viewing history
* Identifies frequently viewed categories
* Recommends recent news based on user interest

---

## System Flow (High-Level)

1. News articles are fetched using APIs and stored in the database
2. Related articles are grouped into a single incident
3. Backend logic performs:

   * Incident analysis
   * Credibility scoring
   * Perspective distribution
   * Similar incident matching
4. Results are sent to the frontend
5. Users view analysis through clean visual components

---

## Technology Stack & Responsibilities

| Technology      | Responsibility                     |
| --------------- | ---------------------------------- |
| HTML            | Page structure                     |
| CSS             | Styling & readability              |
| Bootstrap       | UI components                      |
| JavaScript      | Interaction & charts (no analysis) |
| Python          | All analysis and decision logic    |
| Flask           | Routing and control layer          |
| Data Structures | Efficient processing and counting  |
| PostgreSQL      | Persistent data storage            |

---

## Academic & Design Notes

* The project is **analysis-focused**, not opinion-based
* Reporting categories are **source-based**, not content-based
* No machine learning or sentiment analysis is used
 
---

## Project Structure

```
Veritas/
├── app/
│   ├── __init__.py           # App factory
│   ├── config.py             # Configuration classes
│   ├── extensions.py         # Flask extensions
│   ├── models/               # Database models
│   │   ├── user.py
│   │   ├── source.py
│   │   ├── news.py
│   │   ├── incident.py
│   │   ├── incident_news.py
│   │   ├── user_history.py
│   │   └── analysis_cache.py
│   ├── routes/               # Blueprint routes
│   │   ├── main.py           # Home page
│   │   ├── news.py           # News routes
│   │   ├── analysis.py       # Analysis routes
│   │   └── api.py            # API endpoints
│   ├── services/             # Business logic
│   │   ├── news_service.py
│   │   └── analysis_service.py
│   ├── utils/                # Analysis utilities
│   │   ├── credibility.py
│   │   ├── perspective.py
│   │   ├── similarity.py
│   │   └── recommendations.py
│   ├── templates/            # Jinja2 templates
│   │   ├── base/
│   │   ├── pages/
│   │   ├── news/
│   │   ├── analysis/
│   │   └── errors/
│   └── static/               # Static assets
│       ├── css/
│       ├── js/
│       └── images/
├── database/                 # SQL schemas
├── scripts/                  # Utility scripts
│   ├── init_db.py
│   └── seed_data.py
├── tests/                    # Test files
├── run.py                    # Application entry point
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
└── README.md
```

---

## API Endpoints

### Web Routes
- `GET /` - Home page with latest news and recommendations
- `GET /news` - News listing (paginated)
- `GET /news/<id>` - News detail page
- `GET /analysis/<id>` - Incident analysis page

### API Routes (JSON)
- `GET /api/news` - News list (JSON)
- `GET /api/analysis/<id>` - Analysis data (JSON)
- `GET /api/recommendations` - User recommendations (JSON)

---

## Database Schema

The application uses 7 main tables:

1. **users** - User accounts
2. **sources** - News sources (with category: public/neutral/political)
3. **news** - News articles
4. **incidents** - Grouped incidents
5. **incident_news** - Many-to-many relationship
6. **user_history** - User viewing history
7. **analysis_cache** - Cached analysis results

See `database/schema.sql` for detailed schema.

---

## Analysis Features

### 1. Credibility Scoring
- **Source diversity** (40%): More independent sources = higher score
- **Location clarity** (30%): Clear location information
- **Completeness** (30%): Complete article information

### 2. Perspective Distribution
- **Public**: Citizen-focused reporting
- **Neutral**: Fact-based, balanced reporting
- **Political**: Government and policy-driven reporting

### 3. Similar Incidents
- Matches by location, category, and date (±30 days)

### 4. Personalized Recommendations
- Based on user viewing history
- Tracks category and location preferences

---

## Development

### Running in Development Mode
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python run.py
```

### Database Migrations
```bash
# Initialize migrations (first time only)
flask db init

# Create a migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade
```

### Project Status

✅ **Production Ready**

Features implemented:
* ✅ Complete database schema with relationships
* ✅ All analysis modules (credibility, perspective, similarity, recommendations)
* ✅ Responsive Bootstrap 5 UI
* ✅ Chart.js visualizations
* ✅ RESTful API endpoints
* ✅ Error handling (404, 500)
* ✅ Sample data seeding script

---

## Contributing

This project is currently under development and contributions are welcome from team members.

### How to Contribute

* Discuss the change with the team before starting
* Pick one responsibility area:

  * News content & data collection
  * Analysis logic (incident, credibility, perspective)
  * Frontend UI & layout
  * Database & data organization
* Keep changes **small, clear, and well-explained**

### Contribution Guidelines

* Do not add political opinions or subjective judgments
* Follow the project terminology: **Public / Neutral / Political**
* Keep explanations simple so all team members can understand
* Test changes with sample local (Ahmedabad) data

### Communication

* Use clear commit messages
* Update documentation if behavior or flow changes
* Ask before introducing new features

---

## Final Note

Veritas is built to help users **see the full picture**, not to influence viewpoints. By structuring and comparing information logically, the system empowers readers to make their own judgments.

*Truth becomes clearer when seen from more than one angle.*
