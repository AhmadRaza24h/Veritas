"""
Basic tests for Veritas application.
"""
import os
import sys
import unittest
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models import User, Source, News, Incident, IncidentNews


class VeritasTestCase(unittest.TestCase):
    """Test case for Veritas application."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Override environment variable for testing
        os.environ['TEST_DATABASE_URL'] = 'sqlite:///:memory:'
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            self._create_test_data()
    
    def tearDown(self):
        """Clean up after tests."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def _create_test_data(self):
        """Create test data."""
        # Create a source
        source = Source(source_name='Test Source', category='neutral')
        db.session.add(source)
        db.session.commit()
        
        # Create news
        news = News(
            source_id=source.source_id,
            title='Test News Article',
            summary='Test summary',
            content='Test content',
            location='Test Location',
            incident_type='Test Type',
            published_date=datetime.now().date()
        )
        db.session.add(news)
        db.session.commit()
        
        # Create incident
        incident = Incident(
            incident_type='Test Type',
            location='Test Location',
            first_reported=datetime.now().date(),
            last_reported=datetime.now().date()
        )
        db.session.add(incident)
        db.session.commit()
        
        # Link news to incident
        incident_news = IncidentNews(
            incident_id=incident.incident_id,
            news_id=news.news_id
        )
        db.session.add(incident_news)
        db.session.commit()
    
    def test_home_page(self):
        """Test home page loads."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Veritas', response.data)
    
    def test_news_list(self):
        """Test news listing page."""
        response = self.client.get('/news/')
        self.assertEqual(response.status_code, 200)
    
    def test_news_detail(self):
        """Test news detail page."""
        response = self.client.get('/news/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test News Article', response.data)
    
    def test_analysis_page(self):
        """Test analysis page."""
        response = self.client.get('/analysis/1')
        self.assertEqual(response.status_code, 200)
    
    def test_api_news(self):
        """Test API news endpoint."""
        response = self.client.get('/api/news')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
    
    def test_api_analysis(self):
        """Test API analysis endpoint."""
        response = self.client.get('/api/analysis/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
    
    def test_api_recommendations(self):
        """Test API recommendations endpoint."""
        response = self.client.get('/api/recommendations')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
    
    def test_404_error(self):
        """Test 404 error handler."""
        response = self.client.get('/nonexistent')
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'404', response.data)


if __name__ == '__main__':
    unittest.main()
