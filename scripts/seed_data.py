#!/usr/bin/env python3
"""
Database seeding script.
Populates the database with sample data for testing.
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models import User, Source, News, Incident, IncidentNews, UserHistory, AnalysisCache


def seed_data():
    """Seed the database with sample data."""
    app = create_app()
    
    with app.app_context():
        print("Seeding database...")
        
        # Clear existing data
        print("Clearing existing data...")
        db.session.query(AnalysisCache).delete()
        db.session.query(UserHistory).delete()
        db.session.query(IncidentNews).delete()
        db.session.query(News).delete()
        db.session.query(Incident).delete()
        db.session.query(Source).delete()
        db.session.query(User).delete()
        db.session.commit()
        
        # Create users
        print("Creating users...")
        user1 = User(username='demo_user', email='demo@veritas.com')
        db.session.add(user1)
        db.session.commit()
        
        # Create sources
        print("Creating sources...")
        sources = [
            Source(source_name='Ahmedabad Times', category='neutral'),
            Source(source_name='Gujarat Samachar', category='neutral'),
            Source(source_name='City Voice', category='public'),
            Source(source_name='Citizen Reporter', category='public'),
            Source(source_name='Gujarat Government Press', category='political'),
            Source(source_name='Municipal Corporation Bulletin', category='political'),
        ]
        for source in sources:
            db.session.add(source)
        db.session.commit()
        
        # Create incidents
        print("Creating incidents...")
        incidents = [
            Incident(
                incident_type='Traffic Accident',
                location='Ashram Road',
                first_reported=datetime.now() - timedelta(days=5),
                last_reported=datetime.now() - timedelta(days=4)
            ),
            Incident(
                incident_type='Water Supply Issue',
                location='Satellite Area',
                first_reported=datetime.now() - timedelta(days=10),
                last_reported=datetime.now() - timedelta(days=8)
            ),
            Incident(
                incident_type='Road Construction',
                location='SG Highway',
                first_reported=datetime.now() - timedelta(days=15),
                last_reported=datetime.now() - timedelta(days=14)
            ),
        ]
        for incident in incidents:
            db.session.add(incident)
        db.session.commit()
        
        # Create news articles
        print("Creating news articles...")
        news_data = [
            # Incident 1: Traffic Accident
            {
                'source_id': 1,
                'title': 'Major Traffic Accident on Ashram Road Causes Delays',
                'summary': 'A multi-vehicle collision on Ashram Road has resulted in significant traffic congestion during evening hours.',
                'content': 'A serious traffic accident involving three vehicles occurred on Ashram Road near the ISRO crossroads yesterday evening. The incident took place around 6:30 PM during peak traffic hours, causing major delays for commuters. Preliminary reports suggest that poor visibility due to heavy rain may have contributed to the accident. Emergency services responded promptly, and injured individuals were transported to nearby hospitals. Traffic police diverted vehicles through alternative routes to manage the congestion.',
                'location': 'Ashram Road',
                'incident_type': 'Traffic Accident',
                'published_date': datetime.now() - timedelta(days=5),
                'incident': incidents[0]
            },
            {
                'source_id': 3,
                'title': 'Residents Demand Better Road Safety After Ashram Road Accident',
                'summary': 'Local residents express concerns about road safety following recent accident on Ashram Road.',
                'content': 'Following yesterday\'s accident on Ashram Road, local residents have come forward demanding improved road safety measures. Community members point to inadequate street lighting and poorly maintained road surfaces as contributing factors. "This is not the first accident at this location," said one resident. Several community groups are planning to submit a petition to the traffic authorities requesting immediate action.',
                'location': 'Ashram Road',
                'incident_type': 'Traffic Accident',
                'published_date': datetime.now() - timedelta(days=4),
                'incident': incidents[0]
            },
            {
                'source_id': 5,
                'title': 'Traffic Department Announces Safety Audit of Ashram Road',
                'summary': 'Government announces comprehensive safety review following recent accident.',
                'content': 'The State Traffic Department has announced a comprehensive safety audit of Ashram Road following the recent accident. A senior official stated that the department takes road safety seriously and will conduct a thorough review of the area. The audit will examine road conditions, signage, lighting, and traffic flow patterns. Based on the findings, appropriate measures will be implemented to prevent future incidents.',
                'location': 'Ashram Road',
                'incident_type': 'Traffic Accident',
                'published_date': datetime.now() - timedelta(days=4),
                'incident': incidents[0]
            },
            # Incident 2: Water Supply Issue
            {
                'source_id': 2,
                'title': 'Water Supply Disruption Affects Satellite Area',
                'summary': 'Residents of Satellite area face water shortage due to pipeline maintenance.',
                'content': 'Residents in the Satellite area have been experiencing water supply disruptions for the past two days due to emergency pipeline maintenance work. The Ahmedabad Municipal Corporation (AMC) stated that a major pipeline leak was detected, requiring immediate repair. Water tankers have been deployed to affected areas to provide temporary relief. Officials expect normal supply to resume within 48 hours.',
                'location': 'Satellite Area',
                'incident_type': 'Water Supply Issue',
                'published_date': datetime.now() - timedelta(days=10),
                'incident': incidents[1]
            },
            {
                'source_id': 4,
                'title': 'Satellite Residents Struggle with Extended Water Crisis',
                'summary': 'Citizens report severe hardship as water shortage continues beyond expected timeframe.',
                'content': 'What was initially announced as a 48-hour water supply disruption has extended beyond the promised timeline, causing significant hardship for Satellite area residents. Families are forced to wait in long queues for water tankers, which arrive irregularly. "We were not prepared for such a long disruption," complained several residents. Many are purchasing water at inflated prices from private suppliers. Community organizations are calling for better communication and faster resolution.',
                'location': 'Satellite Area',
                'incident_type': 'Water Supply Issue',
                'published_date': datetime.now() - timedelta(days=9),
                'incident': incidents[1]
            },
            {
                'source_id': 6,
                'title': 'AMC Restores Water Supply to Satellite Area After Pipeline Repair',
                'summary': 'Municipal corporation completes repair work, normalizes water distribution.',
                'content': 'The Ahmedabad Municipal Corporation has successfully completed the pipeline repair work in the Satellite area, restoring normal water supply to affected residents. An AMC spokesperson thanked residents for their patience and cooperation during the emergency maintenance period. The corporation has assured that the repaired pipeline will be more reliable and reduce the likelihood of future disruptions. Regular monitoring will be conducted to ensure continued stability.',
                'location': 'Satellite Area',
                'incident_type': 'Water Supply Issue',
                'published_date': datetime.now() - timedelta(days=8),
                'incident': incidents[1]
            },
            # Incident 3: Road Construction
            {
                'source_id': 1,
                'title': 'SG Highway Section Closed for Major Road Construction',
                'summary': 'Authorities announce temporary closure for infrastructure improvement work.',
                'content': 'A major section of SG Highway will be closed for the next two months to facilitate extensive road construction and improvement work. The project includes road widening, drainage improvements, and installation of modern street lighting. Commuters are advised to use alternative routes during this period. The construction is part of a larger city infrastructure development initiative.',
                'location': 'SG Highway',
                'incident_type': 'Road Construction',
                'published_date': datetime.now() - timedelta(days=15),
                'incident': incidents[2]
            },
            {
                'source_id': 2,
                'title': 'SG Highway Construction Progressing on Schedule',
                'summary': 'Road improvement project reaches first milestone within planned timeframe.',
                'content': 'The ongoing road construction project on SG Highway has completed its first phase successfully, according to project officials. Despite initial concerns about delays, the work has progressed as per schedule. The improved section now features better drainage systems and smoother road surfaces. Authorities expect the entire project to be completed within the announced two-month timeline.',
                'location': 'SG Highway',
                'incident_type': 'Road Construction',
                'published_date': datetime.now() - timedelta(days=14),
                'incident': incidents[2]
            },
            # Additional standalone news articles
            {
                'source_id': 3,
                'title': 'New Public Library Opens in Vastrapur',
                'summary': 'Community celebrates opening of modern library facility with digital resources.',
                'content': 'A new state-of-the-art public library was inaugurated in Vastrapur today, offering residents access to thousands of books, digital resources, and study spaces. The library features modern amenities including computer labs, reading rooms, and a dedicated children\'s section. Community members welcomed the facility as a valuable addition to the neighborhood.',
                'location': 'Vastrapur',
                'incident_type': 'Community Development',
                'published_date': datetime.now() - timedelta(days=2),
                'incident': None
            },
            {
                'source_id': 1,
                'title': 'Ahmedabad Weather: Heavy Rain Expected This Week',
                'summary': 'Meteorological department issues advisory for heavy rainfall across the city.',
                'content': 'The meteorological department has issued an advisory warning of heavy to very heavy rainfall expected across Ahmedabad over the next three days. Residents are advised to avoid unnecessary travel and take precautions against waterlogging. The civic authorities have activated emergency response teams to handle any flood-like situations.',
                'location': 'Ahmedabad',
                'incident_type': 'Weather Alert',
                'published_date': datetime.now() - timedelta(days=1),
                'incident': None
            },
        ]
        
        news_objects = []
        for news_item in news_data:
            incident = news_item.pop('incident')
            news = News(**news_item)
            db.session.add(news)
            db.session.flush()  # Get news_id
            
            # Link to incident if exists
            if incident:
                incident_news = IncidentNews(incident_id=incident.incident_id, news_id=news.news_id)
                db.session.add(incident_news)
            
            news_objects.append(news)
        
        db.session.commit()
        
        # Create some user history
        print("Creating user history...")
        for i, news in enumerate(news_objects[:5]):
            history = UserHistory(
                user_id=user1.user_id,
                news_id=news.news_id,
                viewed_at=datetime.now() - timedelta(days=i)
            )
            db.session.add(history)
        db.session.commit()
        
        print("\nSeeding completed successfully!")
        print(f"Created {len(sources)} sources")
        print(f"Created {len(incidents)} incidents")
        print(f"Created {len(news_objects)} news articles")
        print(f"Created 1 user with viewing history")


if __name__ == '__main__':
    seed_data()
