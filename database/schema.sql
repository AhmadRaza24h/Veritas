-- ============================================
-- Veritas : Database Schema (Final, Safe)
-- PostgreSQL
-- ============================================

-- Drop tables in correct dependency order
DROP TABLE IF EXISTS analysis_cache;
DROP TABLE IF EXISTS user_history;
DROP TABLE IF EXISTS incident_news;
DROP TABLE IF EXISTS incidents;
DROP TABLE IF EXISTS news;
DROP TABLE IF EXISTS sources;
DROP TABLE IF EXISTS users;

-- ============================================
-- 1. users (MASTER ENTITY)
-- ============================================

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 2. sources (MASTER ENTITY)
-- ============================================

CREATE TABLE sources (
    source_id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL,
    category VARCHAR(20)
        CHECK (category IN ('public', 'neutral', 'political'))
);

-- ============================================
-- 3. news (DEPENDS ON sources)
-- ============================================

CREATE TABLE news (
    news_id SERIAL PRIMARY KEY,
    source_id INT,
    title TEXT NOT NULL,
    summary TEXT,
    content TEXT,
    location VARCHAR(100),
    incident_type VARCHAR(50),
    published_date DATE,

    CONSTRAINT fk_news_source
        FOREIGN KEY (source_id)
        REFERENCES sources(source_id)
        ON DELETE SET NULL
);

-- ============================================
-- 4. incidents (MASTER ENTITY)
-- ============================================

CREATE TABLE incidents (
    incident_id SERIAL PRIMARY KEY,
    incident_type VARCHAR(50),
    location VARCHAR(100),
    first_reported DATE,
    last_reported DATE
);

-- ============================================
-- 5. incident_news (JUNCTION TABLE)
-- ============================================

CREATE TABLE incident_news (
    incident_id INT NOT NULL,
    news_id INT NOT NULL,
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_incident_news
        PRIMARY KEY (incident_id, news_id),

    CONSTRAINT fk_incident
        FOREIGN KEY (incident_id)
        REFERENCES incidents(incident_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_news
        FOREIGN KEY (news_id)
        REFERENCES news(news_id)
        ON DELETE CASCADE
);

-- ============================================
-- 6. user_history (DERIVED DATA)
-- ============================================

CREATE TABLE user_history (
    history_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    news_id INT NOT NULL,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_history_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_history_news
        FOREIGN KEY (news_id)
        REFERENCES news(news_id)
        ON DELETE CASCADE
);

-- ============================================
-- 7. analysis_cache (CACHED DATA)
-- ============================================

CREATE TABLE analysis_cache (
    analysis_id SERIAL PRIMARY KEY,
    incident_id INT NOT NULL,

    credibility_score INT
        CHECK (credibility_score BETWEEN 0 AND 100),

    public_pct INT
        CHECK (public_pct BETWEEN 0 AND 100),
    neutral_pct INT
        CHECK (neutral_pct BETWEEN 0 AND 100),
    political_pct INT
        CHECK (political_pct BETWEEN 0 AND 100),

    perspective_summary TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_analysis_incident
        FOREIGN KEY (incident_id)
        REFERENCES incidents(incident_id)
        ON DELETE CASCADE
);
