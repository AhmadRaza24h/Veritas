-- ============================================
-- Veritas : Required Indexes
-- Purpose: Improve query performance for
-- filtering, joins, and analytics
-- ============================================

-- 1. Speed up location-based news filtering
CREATE INDEX idx_news_location
ON news(location);

-- 2. Speed up incident-type based analysis & recommendations
CREATE INDEX idx_news_incident_type
ON news(incident_type);

-- 3. Speed up fetching all reports for a given incident
CREATE INDEX idx_incident_news_incident
ON incident_news(incident_id);

-- 4. Speed up user history lookup (profile & recommendations)
CREATE INDEX idx_user_history_user
ON user_history(user_id);

-- 5. Speed up cached analysis lookup for incidents
CREATE INDEX idx_analysis_cache_incident
ON analysis_cache(incident_id);
