# Veritas (dev)

### Local News Portal with Analysis of given data 

---

## Project Overiview

Veritas is  data-driven local news portal that analyzes incidents, scores credibility, compares reporting perspectives (public, neutral, political), identifies similar incidents, and provides basic user-based recommendations using backend logic and persistent storage.

---

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

## Project Status

🚧 **Under Development**

Planned next steps:

* Finalize database schema
* Integrate news APIs
* Implement analysis modules
* Build frontend pages
* Test with local Ahmedabad datasets

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
