-- ============================================
-- Veritas : Sample Data
-- (Fake data for development & testing)
-- ============================================

-- ============================================
-- 1. users
-- ============================================

INSERT INTO users (username, email) VALUES
('ahmad', 'ahmad@example.com'),
('rahul', 'rahul@example.com');

-- ============================================
-- 2. sources
-- ============================================

INSERT INTO sources (source_name, category) VALUES
('Ahmedabad Police', 'public'),
('Local News Network', 'neutral'),
('Political Times', 'political');

-- ============================================
-- 3. news
-- ============================================

INSERT INTO news (source_id, title, summary, content, location, incident_type, published_date) VALUES
(1,
 'Robbery reported near Maninagar',
 'A robbery incident was reported near Maninagar area.',
 'A robbery occurred late night near Maninagar where local residents reported theft.',
 'Ahmedabad',
 'crime',
 '2025-01-10'
),

(2,
 'Fire accident in Naroda industrial area',
 'Fire broke out in a factory in Naroda.',
 'A major fire accident occurred in a factory located in Naroda industrial area.',
 'Ahmedabad',
 'accident',
 '2025-01-12'
),

(3,
 'Traffic congestion increases in Satellite',
 'Heavy traffic reported during peak hours.',
 'Residents of Satellite area faced heavy traffic congestion during evening hours.',
 'Ahmedabad',
 'civic',
 '2025-01-15'
),

(2,
 'Second robbery case reported in Maninagar',
 'Another robbery reported within a week.',
 'Police confirmed a second robbery incident in Maninagar within a short time span.',
 'Ahmedabad',
 'crime',
 '2025-01-18'
);

-- ============================================
-- 4. incidents
-- ============================================

INSERT INTO incidents (incident_type, location, first_reported, last_reported) VALUES
('crime', 'Maninagar', '2025-01-10', '2025-01-18'),
('accident', 'Naroda', '2025-01-12', '2025-01-12'),
('civic', 'Satellite', '2025-01-15', '2025-01-15');

-- ============================================
-- 5. incident_news (junction table)
-- ============================================

-- Incident 1: Maninagar robbery (multiple reports)
INSERT INTO incident_news (incident_id, news_id) VALUES
(1, 1),
(1, 4);

-- Incident 2: Naroda fire
INSERT INTO incident_news (incident_id, news_id) VALUES
(2, 2);

-- Incident 3: Satellite traffic issue
INSERT INTO incident_news (incident_id, news_id) VALUES
(3, 3);

-- ============================================
-- 6. user_history
-- ============================================

INSERT INTO user_history (user_id, news_id) VALUES
(1, 1),
(1, 4),
(1, 3),
(2, 2);

-- ============================================
-- 7. analysis_cache
-- ============================================

INSERT INTO analysis_cache (
    incident_id,
    credibility_score,
    public_pct,
    neutral_pct,
    political_pct,
    perspective_summary
) VALUES
(
    1,
    85,
    60,
    30,
    10,
    'Mostly public and neutral sources with multiple confirmations'
);
