#!/usr/bin/env python3
"""
Seed rich Ahmedabad data covering last 60 days.
This compensates for NewsAPI free tier 30-day limit.
"""
import sys
import os
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import News, Source, Incident, IncidentNews
from app.extensions import db


def seed_rich_data():
    """Seed 60 days of rich Ahmedabad data."""
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print(" 🌱 SEEDING 60 DAYS RICH AHMEDABAD DATA")
        print("=" * 70)
        print()
        
        # Create diverse sources (10 sources)
        sources_data = [
            {'name': 'Times of India Ahmedabad', 'category': 'neutral'},
            {'name': 'Indian Express Ahmedabad', 'category': 'neutral'},
            {'name': 'Ahmedabad Mirror', 'category': 'neutral'},
            {'name': 'DNA Ahmedabad', 'category': 'neutral'},
            {'name': 'Sandesh News', 'category': 'neutral'},
            {'name': 'Gujarat Samachar', 'category': 'neutral'},
            {'name': 'NDTV Ahmedabad', 'category': 'neutral'},
            {'name': 'Ahmedabad Citizen Reporter', 'category': 'public'},
            {'name': 'Ahmedabad Public News', 'category': 'public'},
            {'name': 'Gujarat Government Portal', 'category': 'political'},
        ]
        
        sources = []
        for s_data in sources_data:
            source = Source.query.filter_by(source_name=s_data['name']).first()
            if not source:
                source = Source(
                    source_name=s_data['name'],
                    category=s_data['category']
                )
                db.session.add(source)
                db.session.flush()
            sources.append(source)
        
        print(f"✅ Created/Found {len(sources)} sources")
        print()
        
        # 30 diverse incidents covering 60 days
        incidents_data = [
            # Week 1 (Recent - High coverage)
            {'title': 'Major traffic jam on SG Highway during evening rush hour', 'location': 'SG Highway, Ahmedabad', 'type': 'Traffic', 'sources': 7, 'days': 2},
            {'title': 'Fire incident at commercial building in Vastrapur market', 'location': 'Vastrapur, Ahmedabad', 'type': 'Fire', 'sources': 8, 'days': 3},
            {'title': 'Heavy rainfall causes waterlogging in Maninagar area', 'location': 'Maninagar, Ahmedabad', 'type': 'Weather', 'sources': 6, 'days': 5},
            {'title': 'New metro station inaugurated at Thaltej circle', 'location': 'Thaltej, Ahmedabad', 'type': 'Infrastructure', 'sources': 9, 'days': 6},
            
            # Week 2
            {'title': 'Chain snatching cases reported in Navrangpura police station area', 'location': 'Navrangpura, Ahmedabad', 'type': 'Crime', 'sources': 5, 'days': 8},
            {'title': 'Riverfront Cultural Festival attracts thousands of visitors', 'location': 'Sabarmati Riverfront, Ahmedabad', 'type': 'Event', 'sources': 7, 'days': 10},
            {'title': 'Road accident at Kankaria Circle injures three people', 'location': 'Kankaria, Ahmedabad', 'type': 'Accident', 'sources': 6, 'days': 12},
            {'title': 'BRTS corridor expansion project announced by AMC', 'location': 'Ahmedabad, Gujarat', 'type': 'Infrastructure', 'sources': 8, 'days': 14},
            
            # Week 3
            {'title': 'IIT Gandhinagar inaugurates new AI research center', 'location': 'Gandhinagar, Gujarat', 'type': 'Education', 'sources': 6, 'days': 16},
            {'title': 'Startup funding scheme launched by Gujarat government', 'location': 'Gandhinagar, Gujarat', 'type': 'Business', 'sources': 7, 'days': 18},
            {'title': 'Air quality index crosses danger mark in Ahmedabad', 'location': 'Ahmedabad, Gujarat', 'type': 'Weather', 'sources': 8, 'days': 20},
            {'title': 'Science City launches interactive space exhibition', 'location': 'Science City, Ahmedabad', 'type': 'Event', 'sources': 5, 'days': 21},
            
            # Week 4 (1 month ago)
            {'title': 'Multiple vehicle collision on Sarkhej-Gandhinagar Highway', 'location': 'SG Highway, Ahmedabad', 'type': 'Accident', 'sources': 9, 'days': 25},
            {'title': 'Municipal Corporation elections dates announced', 'location': 'Ahmedabad, Gujarat', 'type': 'Politics', 'sources': 10, 'days': 27},
            {'title': 'Hospital fire drill conducted at Civil Hospital', 'location': 'Ahmedabad, Gujarat', 'type': 'Health', 'sources': 4, 'days': 29},
            
            # Month 2 (31-45 days ago)
            {'title': 'Navratri celebrations begin at GMDC Ground with traditional Garba', 'location': 'Ahmedabad, Gujarat', 'type': 'Event', 'sources': 8, 'days': 32},
            {'title': 'Monsoon preparedness meeting held by AMC officials', 'location': 'Ahmedabad, Gujarat', 'type': 'Politics', 'sources': 5, 'days': 35},
            {'title': 'Traffic police launch helmet awareness campaign', 'location': 'Ahmedabad, Gujarat', 'type': 'Traffic', 'sources': 6, 'days': 37},
            {'title': 'Fire at textile market in Kalupur area contained', 'location': 'Kalupur, Ahmedabad', 'type': 'Fire', 'sources': 7, 'days': 39},
            {'title': 'New flyover construction begins at Paldi junction', 'location': 'Paldi, Ahmedabad', 'type': 'Infrastructure', 'sources': 6, 'days': 42},
            
            # Month 2 continued (46-60 days ago)
            {'title': 'Robbery attempt foiled at jewelry shop in Bodakdev', 'location': 'Bodakdev, Ahmedabad', 'type': 'Crime', 'sources': 8, 'days': 45},
            {'title': 'Educational fair organized at IIM Ahmedabad campus', 'location': 'Ahmedabad, Gujarat', 'type': 'Education', 'sources': 5, 'days': 48},
            {'title': 'Cyclone warning issued for Gujarat coast regions', 'location': 'Gujarat', 'type': 'Weather', 'sources': 9, 'days': 50},
            {'title': 'Kite festival preparations begin across Ahmedabad', 'location': 'Ahmedabad, Gujarat', 'type': 'Event', 'sources': 7, 'days': 52},
            {'title': 'Bus accident on Ashram Road causes traffic chaos', 'location': 'Ashram Road, Ahmedabad', 'type': 'Accident', 'sources': 6, 'days': 54},
            {'title': 'IT park development announced in Bopal area', 'location': 'Bopal, Ahmedabad', 'type': 'Business', 'sources': 7, 'days': 56},
            {'title': 'Health camps organized in rural Ahmedabad areas', 'location': 'Ahmedabad District, Gujarat', 'type': 'Health', 'sources': 4, 'days': 58},
            {'title': 'Traffic signal upgrades completed at major junctions', 'location': 'Ahmedabad, Gujarat', 'type': 'Infrastructure', 'sources': 5, 'days': 59},
        ]
        
        total_news = 0
        total_incidents = 0
        
        for inc_data in incidents_data:
            # Create incident
            reported_date = datetime.utcnow().date() - timedelta(days=inc_data['days'])
            
            # Check if exists
            existing = Incident.query.filter_by(title=inc_data['title']).first()
            if existing:
                print(f"  ↩️  Exists: {inc_data['title'][:40]}...")
                continue
            
            incident = Incident(
                title=inc_data['title'],
                description=f"Detailed report about {inc_data['title'].lower()}",
                location=inc_data['location'],
                incident_type=inc_data['type'],
                reported_date=reported_date
            )
            
            db.session.add(incident)
            db.session.flush()
            total_incidents += 1
            
            # Create multiple news from different sources
            num_sources = inc_data['sources']
            selected_sources = random.sample(sources, min(num_sources, len(sources)))
            
            for i, source in enumerate(selected_sources):
                # Vary titles
                if i == 0:
                    title = inc_data['title']
                elif i == 1:
                    title = f"Breaking: {inc_data['title']}"
                elif i == 2:
                    title = f"{inc_data['title']} - Latest Updates"
                else:
                    title = f"{inc_data['title']} ({source.source_name})"
                
                # Create content
                content = f"Detailed coverage of {inc_data['title'].lower()}. "
                if source.category == 'public':
                    content += "Eyewitness reports and citizen journalism perspective. "
                elif source.category == 'political':
                    content += "Official statement and government response. "
                else:
                    content += "Professional journalism and factual reporting. "
                
                content += f"Reported by {source.source_name} on {reported_date.strftime('%d %B %Y')}."
                
                # Create news
                news = News(
                    source_id=source.source_id,
                    title=title[:500],
                    summary=f"Report about {inc_data['title'].lower()} in {inc_data['location']}",
                    content=content[:2000],
                    location=inc_data['location'],
                    incident_type=inc_data['type'],
                    published_date=reported_date + timedelta(hours=i*2),
                    image_url=None
                )
                
                db.session.add(news)
                db.session.flush()
                
                # Link to incident
                incident_news = IncidentNews(
                    incident_id=incident.incident_id,
                    news_id=news.news_id
                )
                
                db.session.add(incident_news)
                total_news += 1
            
            print(f"  ✅ {inc_data['title'][:40]}... ({num_sources} sources, {inc_data['days']} days ago)")
        
        db.session.commit()
        
        print()
        print("=" * 70)
        print(f" 🎉 SEED COMPLETE: 60 DAYS DATA")
        print(f"    Incidents: {total_incidents}")
        print(f"    News Articles: {total_news}")
        print(f"    Time Range: Last 60 days")
        print("=" * 70)


if __name__ == '__main__':
    seed_rich_data()