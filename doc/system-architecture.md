# System Architecture — Veritas

## Purpose of this Document

This document explains **how Veritas works internally** at a system level. It is meant for:

* Team members (technical and non-technical)
* Faculty / evaluators
* Anyone who wants to understand the project flow without reading code

This document focuses on **architecture and responsibilities**, not implementation details.

---

## Architectural Overview

Veritas follows a **layered architecture** where each layer has a clear and limited responsibility.

**High-level flow:**

User → Frontend → Flask (Controller) → Python (Logic) → Database

This separation ensures clarity, maintainability, and Case-3 compliance.

---

## Frontend Architecture

### Technologies

* **HTML** – Structure of pages
* **CSS** – Styling and layout
* **Bootstrap** – UI components and responsiveness
* **JavaScript** – User interaction and visualization

### Responsibilities

The frontend is responsible for:

* Publishing and displaying local news articles
* Showing analysis results returned by the backend
* Handling user actions (clicks, filters, navigation)

### What the Frontend Does NOT Do

* No data analysis
* No decision-making
* No direct database access

The frontend only **requests data** and **presents results**.

---

## Backend Architecture

### Flask — Controller Layer

Flask acts as the **control and routing layer**.

Responsibilities:

* Defines application routes (URLs)
* Receives requests from the frontend
* Calls Python logic functions
* Sends processed results back to the frontend

Flask does not contain business or analytical logic.

---

### Python — Core Logic Layer

Python is the **analytical engine** of Veritas.

Responsibilities include:

* Incident analysis (frequency, patterns)
* Credibility scoring using rule-based logic
* Perspective distribution analysis (Public / Neutral / Political)
* Similar incident comparison
* Basic recommendation logic

All calculations and decisions are performed in Python using data structures.

---

## Data Structures Usage

Data Structures are explicitly used to justify analytical processing.

| Purpose              | Data Structure |
| -------------------- | -------------- |
| Incident frequency   | Dictionary     |
| User viewing history | Stack          |
| Category preference  | Hash Map       |
| Monthly trends       | Array          |
| Area × Incident type | 2D Array       |

These structures improve efficiency and clarity of analysis.

---

## Database Architecture

### PostgreSQL — Persistent Storage

The database acts as the **long-term memory** of the system. It stores all data required for publishing news, analysis, comparison, and user tracking.

The database is accessed **only through the backend** (Python + Flask).

---

## Database Tables & Required Columns

### 1. `users`

Stores basic user information.

| Column     | Description            |
| ---------- | ---------------------- |
| user_id    | Unique user identifier |
| username   | User name              |
| email      | User email             |
| created_at | Account creation time  |

---

### 2. `sources`

Stores news source metadata and reporting orientation.

| Column      | Description                  |
| ----------- | ---------------------------- |
| source_id   | Unique source identifier     |
| source_name | Name of the news source      |
| category    | public / neutral / political |

---

### 3. `news`

Stores published news articles.

| Column         | Description                                     |
| -------------- | ----------------------------------------------- |
| news_id        | Unique news identifier                          |
| source_id      | Reference to source                             |
| title          | News headline                                   |
| summary        | Short description                               |
| content        | Full article text                               |
| location       | Area / city (Ahmedabad)                         |
| incident_type  | Type of incident (crime, civic, accident, etc.) |
| published_date | Date of publication                             |

---

### 4. `incidents`

Stores grouped incident-level information.

| Column         | Description                |
| -------------- | -------------------------- |
| incident_id    | Unique incident identifier |
| incident_type  | Type of incident           |
| location       | Area affected              |
| first_reported | First report date          |
| last_reported  | Latest report date         |

---

### 5. `incident_news`

Links multiple news articles to a single incident.

| Column      | Description               |
| ----------- | ------------------------- |
| incident_id | Reference to incident     |
| news_id     | Reference to news article |

---

### 6. `user_history`

Tracks which news articles a user has viewed.

| Column     | Description               |
| ---------- | ------------------------- |
| history_id | Unique history identifier |
| user_id    | Reference to user         |
| news_id    | Viewed news               |
| viewed_at  | Time of view              |

---

### 7. `analysis_cache` (Optional)

Stores precomputed analysis results for performance.

| Column              | Description                           |
| ------------------- | ------------------------------------- |
| analysis_id         | Unique analysis identifier            |
| incident_id         | Related incident                      |
| credibility_score   | Stored credibility value              |
| perspective_summary | Public/Neutral/Political distribution |
| generated_at        | Analysis timestamp                    |

---

### Database Design Notes

* Tables are normalized to avoid redundancy
* Incident-based design enables comparison
* Source category is **metadata**, not opinion
* Schema is scalable for future features

---

## Perspective Classification Model

Veritas categorizes news sources into three reporting orientations:

* **Public** – citizen-focused and people-impact reporting
* **Neutral** – factual and balanced reporting
* **Political** – government and policy-driven reporting

Important notes:

* Classification is **source-based**, not content-based
* No opinions or sentiment are evaluated
* The system only performs **distribution analysis**

---

## End-to-End System Flow

1. News is fetched and stored in the database
2. Related articles are grouped as a single incident
3. Python performs analysis using data structures
4. Flask manages request–response flow
5. Frontend displays news and analytical insights

---

## Design Principles

* Clear separation of concerns
* Analysis-focused, not opinion-based
* Simple, explainable logic
* Scalable for future extensions

---

## Final Note

The architecture of Veritas ensures that **presentation, control, logic, and storage** remain independent. This makes the system easier to understand, evaluate, and extend while maintaining clarity and academic integrity.

