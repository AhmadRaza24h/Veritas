# Veritas – News Analytics Platform

### Production-Ready Flask Application with PostgreSQL

Veritas is a structured news analytics platform that groups multiple reports of the same real-world event, evaluates cross-source credibility, analyzes reporting perspectives, and presents comparative insights using backend logic and persistent storage.

---

## 🚀 Tech Stack

- **Backend:** Flask 3.x, Python 3.x  
- **Database:** PostgreSQL with SQLAlchemy ORM  
- **Frontend:** Bootstrap 5, Chart.js  
- **Migrations:** Flask-Migrate  
- **Architecture:** Blueprint Pattern, Factory Pattern, Service Layer  

---

# ⚡ Quick Start

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip

---

## 1️⃣ Clone Repository

```bash
git clone https://github.com/AhmadRaza24h/Veritas.git
cd Veritas
```

---

## 2️⃣ Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your PostgreSQL credentials.

---

## 5️⃣ Initialize Database

```bash
createdb veritas_dev
python scripts/init_db.py
python scripts/seed_data.py
```

---

## 6️⃣ Run Application

```bash
python run.py
```

Open in browser:

```
http://localhost:5000
```

---

# 📌 Problem Statement

News readers often consume information from:

- A single source  
- Or multiple sources without structured comparison  

This can result in:

- Over-reliance on one reporting style  
- Limited cross-verification  
- Difficulty assessing credibility  

Veritas addresses this by grouping similar articles into a single real-world event and analyzing coverage across independent sources.

---

# 🧠 Core Features

---

## 1️⃣ Event-Based Grouping

Articles covering the same real-world story are grouped using backend similarity logic.

Each event group:

- Represents one real-world occurrence  
- Contains multiple articles from different sources  
- Enables structured cross-source validation  

Grouping is managed using the `group_id` field in the `news` table.

---

## 2️⃣ Cross-Source Credibility Scoring

Credibility is calculated per event group (0–100).

### Scoring Components

- **Cross-Source Confirmation (50%)**  
  Number of independent sources covering the same event.

- **Source Reliability Tier (30%)**  
  Based on predefined source classification:
  - Neutral  
  - Public  
  - Political  

- **Time Convergence (20%)**  
  Measures how closely in time different sources reported the same story.

> The system evaluates structural credibility, not factual truth.

---

## 3️⃣ Perspective Distribution Analysis

Each source is categorized as:

- **Public** – Citizen-focused reporting  
- **Neutral** – Fact-based, balanced reporting  
- **Political** – Government or policy-focused reporting  

For each event group, Veritas calculates percentage distribution across these three source categories.

This allows readers to understand diversity of coverage.

---

## 4️⃣ Timeline & Geographic Insights

For each event group, the system provides:

- Reporting timeline visualization  
- Geographic distribution (when applicable)  
- Coverage density insights  

---

## 5️⃣ Personalized Recommendations

The system:

- Tracks user viewing history  
- Identifies frequently viewed categories  
- Recommends recent relevant event groups  

All recommendation logic is backend-driven and persistent.

---

# 🔄 System Flow

1. News articles are fetched from APIs  
2. Similar articles are grouped into a single event (`group_id`)  
3. Articles are stored with:
   - `source_id`
   - `group_id`
   - category (classification reference)  
4. Backend performs:
   - Credibility scoring  
   - Perspective distribution  
   - Timeline analysis  
5. Results are cached  
6. Data is rendered using structured UI components  

---

# 🌐 Routes

## Web Routes

- `GET /` – Home page  
- `GET /news/<id>` – News detail page  
- `GET /analysis/event/<group_id>` – Event analysis page  

## API Routes

- `GET /api/news`  
- `GET /api/analysis/event/<group_id>`  
- `GET /api/recommendations`  

---

# 🗄 Database Schema

Main Tables:

1. **users** – User accounts  
2. **sources** – News sources (public / neutral / political)  
3. **news** – News articles (includes `group_id`)  
4. **incidents** – Category reference table  
5. **incident_news** – Relationship mapping  
6. **user_history** – Viewing history  
7. **analysis_cache** – Cached event analysis results  

See `database/schema.sql` for detailed schema.

---

# 🧩 Analysis Modules

Located in:

```
app/utils/
```

- `credibility.py`
- `perspective.py`
- `similarity.py`
- `recommendations.py`

---

# 📂 Project Structure

```
Veritas/
├── app/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── utils/
│   ├── templates/
│   └── static/
├── scripts/
├── database/
├── tests/
├── run.py
└── README.md
```

---

# 🛠 Development

## Development Mode

```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python run.py
```

---

## Database Migrations

```bash
flask db migrate -m "Describe change"
flask db upgrade
```

---

# 🎓 Academic & Design Notes

- Analysis-focused, not opinion-based  
- Source categories are metadata-based  
- Fully deterministic backend logic  
- No machine learning or sentiment analysis  

---

# 📌 Final Note

Veritas helps readers understand:

- Who is reporting a story  
- How many independent sources confirm it  
- What type of sources are covering it  
- Whether coverage is balanced or concentrated  

By structuring multi-source reporting into coherent event groups, Veritas empowers readers to evaluate news through data-driven insight rather than isolated narratives.

> Truth becomes clearer when seen from more than one angle.