-- ============================================
-- Veritas : Required Triggers
-- Purpose: Maintain data consistency automatically
-- ============================================

-- ============================================
-- Trigger 1:
-- Update incidents.last_reported when new news is linked
-- ============================================

CREATE OR REPLACE FUNCTION update_last_reported()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE incidents
    SET last_reported = CURRENT_DATE
    WHERE incident_id = NEW.incident_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_last_reported
AFTER INSERT ON incident_news
FOR EACH ROW
EXECUTE FUNCTION update_last_reported();

-- ============================================
-- Trigger 2:
-- Ensure only one analysis_cache per incident
-- ============================================

CREATE OR REPLACE FUNCTION prevent_duplicate_analysis()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM analysis_cache
        WHERE incident_id = NEW.incident_id
    ) THEN
        RAISE EXCEPTION
        'Analysis already exists for this incident';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_prevent_duplicate_analysis
BEFORE INSERT ON analysis_cache
FOR EACH ROW
EXECUTE FUNCTION prevent_duplicate_analysis();

-- ============================================
-- Trigger 3:
-- Auto-set first_reported if it is NULL
-- ============================================

CREATE OR REPLACE FUNCTION set_first_reported()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.first_reported IS NULL THEN
        NEW.first_reported := CURRENT_DATE;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_set_first_reported
BEFORE INSERT ON incidents
FOR EACH ROW
EXECUTE FUNCTION set_first_reported();
