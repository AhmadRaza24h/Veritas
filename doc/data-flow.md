# Data Flow — Veritas

## Purpose of this Document

This document explains **how data moves through Veritas**, from the moment news is collected to the moment analysis is shown to the user.

It focuses only on **data flow** (who sends what to whom), not architecture or implementation.

---

## High-Level Data Flow

```
External News Sources / APIs
        ↓
News Ingestion Layer
        ↓
PostgreSQL Database
        ↓
Python Analysis Logic
        ↓
Flask Routes (Controller)
        ↓
Frontend (HTML / CSS / JS)
        ↓
User
```

---

## 1. News Ingestion Flow

**Source:**

* News APIs
* RSS feeds
* Local Ahmedabad news portals

**Flow:**

1. External sources provide raw news data
2. News is fetched periodically by the backend
3. Each article is normalized (title, source, date, location)
4. Normalized articles are stored in the database

📌 At this stage, data is **raw and unprocessed**.

---

## 2. News Storage Flow

**Database tables involved:**

* `sources`
* `news`

**Flow:**

1. Source metadata is checked or inserted
2. News articles are stored with reference to the source
3. Duplicate articles are avoided

📌 Database acts as the **single source of truth**.

---

## 3. Incident Grouping Flow

**Purpose:** Identify multiple articles referring to the same real-world incident.

**Flow:**

1. News articles are fetched from the database
2. Articles are grouped using:

   * Location
   * Incident type
   * Time window
3. A single incident is created from multiple articles
4. Incident references are stored in incident-related tables

📌 This enables comparison and analysis.

---

## 4. Analysis Data Flow

**Triggered when:**

* User opens an analysis page
* Or analysis is precomputed

**Flow:**

1. Flask route receives an analysis request
2. Python logic retrieves related articles for the incident
3. Analysis modules process the data:

   * Incident statistics
   * Credibility score
   * Perspective distribution (Public / Neutral / Political)
   * Similar incident matching
4. Analysis results are returned to Flask

📌 All analysis happens **only in Python**.

---

## 5. Perspective Distribution Flow

**Input:**

* Articles belonging to the same incident

**Flow:**

1. Each article’s source category is read
2. Articles are counted by category:

   * Public
   * Neutral
   * Political
3. Distribution ratios are calculated
4. Results are prepared for visualization

📌 No opinion or content evaluation is performed.

---

## 6. User Interaction Flow

**Triggered by:**

* Clicking a news article
* Opening analysis or similar incidents

**Flow:**

1. User action triggers a frontend request
2. JavaScript sends request to Flask
3. Flask calls Python logic
4. Processed data is returned
5. Frontend renders results visually

---

## 7. User History & Recommendation Flow

**Flow:**

1. User views a news article
2. Viewing data is stored in `user_history`
3. Python analyzes viewing patterns
4. Preferred categories are identified
5. Recommended news is fetched from database
6. Recommendations are sent to frontend

---

## 8. End-to-End Example Flow

**Example:** User opens analysis for an Ahmedabad civic incident

1. User clicks "Analyze"
2. Frontend sends request to Flask
3. Flask fetches incident-related articles
4. Python performs analysis and perspective distribution
5. Results are returned as structured data
6. Frontend displays charts and summaries

---

## Key Data Flow Principles

* Data always flows **Frontend → Backend → Database** or **Database → Backend → Frontend**
* Frontend never accesses the database directly
* Flask never performs analysis
* Python never handles UI
* Database never contains business logic

---

## Final Note

This data flow ensures that Veritas remains **structured, scalable, and easy to reason about**, making the system suitable for academic evaluation and future expansion.
