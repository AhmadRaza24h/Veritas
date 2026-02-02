#!/usr/bin/env python3
"""
Seed database with sample data for testing Veritas application.
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models import User, Source, News, Incident, IncidentNews, UserHistory


def seed_data():
    """Seed the database with sample data."""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("🌱 SEEDING DATABASE WITH SAMPLE DATA")
        print("=" * 60)
        
        # Step 1: Clear existing data (in correct order)
        print("\n📝 Step 1: Clearing existing data...")
        try:
            db.session.query(UserHistory).delete()
            db.session.query(IncidentNews).delete()
            db.session.query(Incident).delete()
            db.session.query(News).delete()
            db.session.query(Source).delete()
            db.session.query(User).delete()
            db.session.commit()
            print("   ✅ Old data cleared successfully")
        except Exception as e:
            print(f"   ⚠️  Warning: {e}")
            db.session.rollback()
        
        # Step 2: Create Users
        print("\n👤 Step 2: Creating users...")
        users = [
            User(username='demo_user', email='demo@veritas.com'),
            User(username='john_doe', email='john@example.com'),
            User(username='jane_smith', email='jane@example.com'),
        ]
        
        # Set passwords
        users[0].set_password('demo123')
        users[1].set_password('john123')
        users[2].set_password('jane123')
        
        db.session.add_all(users)
        db.session.flush()  # ⭐ IMPORTANT: Get user_id before using them
        print(f"   ✅ Created {len(users)} users")
        
        # Step 3: Create Sources
        print("\n📰 Step 3: Creating news sources...")
        sources = [
            Source(source_name='TV9 Gujarati', category='neutral'),
            Source(source_name='ABP Asmita', category='neutral'),
            Source(source_name='Public Voice', category='public'),
            Source(source_name='Citizen Reporter', category='public'),
            Source(source_name='Government Portal', category='political'),
            Source(source_name='Gujarat Samachar', category='neutral'),
        ]
        db.session.add_all(sources)
        db.session.flush()  # ⭐ IMPORTANT: Get source_id before using them
        print(f"   ✅ Created {len(sources)} sources")
        print(f"      - Neutral: 3 sources")
        print(f"      - Public: 2 sources")
        print(f"      - Political: 1 source")
        
        # Step 4: Create News Articles
        print("\n📄 Step 4: Creating news articles...")
        base_date = datetime.utcnow()
        
        news_articles = [
            # Incident 1: SG Highway Accident (Multiple sources)
            News(
                source_id=sources[0].source_id,  # ✅ Now source_id exists
                title='Major Accident on SG Highway, Ahmedabad',
                summary='A major road accident occurred on SG Highway near Gota involving multiple vehicles.',
                content='A severe road accident took place on SG Highway near Gota junction in Ahmedabad. Multiple vehicles were involved in the collision during evening rush hour. Traffic police reached the spot and cleared the area. Two people sustained minor injuries and were taken to nearby hospital.',
                location='SG Highway, Ahmedabad',
                incident_type='Accident',
                published_date=base_date - timedelta(days=1)
            ),
            News(
                source_id=sources[1].source_id,
                title='Traffic Collision Near Gota Junction Causes Chaos',
                summary='Multiple vehicles collided on SG Highway causing severe traffic disruption.',
                content='A traffic collision involving 4 vehicles occurred near Gota junction on SG Highway. Emergency services responded quickly. Traffic was diverted for 2 hours. Investigation underway.',
                location='SG Highway, Ahmedabad',
                incident_type='Accident',
                published_date=base_date - timedelta(days=1, hours=2)
            ),
            News(
                source_id=sources[2].source_id,
                title='Commuters Stranded Due to SG Highway Accident',
                summary='Citizens report difficulty reaching home due to accident.',
                content='Local residents and commuters faced severe difficulty due to the accident on SG Highway. Many reported being stuck in traffic for over an hour. Public demands better traffic management.',
                location='SG Highway, Ahmedabad',
                incident_type='Accident',
                published_date=base_date - timedelta(days=1, hours=3)
            ),
            
            # Incident 2: Vastrapur Crime (Multiple sources)
            News(
                source_id=sources[2].source_id,
                title='Robbery Reported in Vastrapur Area',
                summary='Local shop robbed late night, police investigating the case.',
                content='A local shop in Vastrapur area was robbed late night. Shop owner filed complaint with Vastrapur police station. CCTV footage being examined. Police suspect involvement of 2-3 people.',
                location='Vastrapur, Ahmedabad',
                incident_type='Crime',
                published_date=base_date - timedelta(days=2)
            ),
            News(
                source_id=sources[4].source_id,
                title='Police Arrest Suspect in Vastrapur Robbery Case',
                summary='One person arrested in connection with Vastrapur shop robbery.',
                content='Ahmedabad city police arrested one suspect in the Vastrapur robbery case. Investigation ongoing to identify other accomplices. Stolen items partially recovered.',
                location='Vastrapur, Ahmedabad',
                incident_type='Crime',
                published_date=base_date - timedelta(days=2, hours=12)
            ),
            
            # Additional diverse news
            News(
                source_id=sources[0].source_id,
                title='Heavy Rain Causes Waterlogging in Paldi Area',
                summary='Paldi area faces severe waterlogging after heavy rainfall.',
                content='Heavy rain in Ahmedabad caused severe waterlogging in Paldi area. Residents faced difficulty commuting. AMC deployed pumps to drain water. Several areas remained waterlogged for hours.',
                location='Paldi, Ahmedabad',
                incident_type='Weather',
                published_date=base_date - timedelta(days=3)
            ),
            News(
                source_id=sources[1].source_id,
                title='New Metro Route Announced for Ahmedabad',
                summary='GMRC announces extension of metro line to Maninagar area.',
                content='Gujarat Metro Rail Corporation announced new metro route extension to Maninagar area. Work expected to start next year. This will improve connectivity to eastern parts of city.',
                location='Maninagar, Ahmedabad',
                incident_type='Infrastructure',
                published_date=base_date - timedelta(days=4)
            ),
            News(
                source_id=sources[3].source_id,
                title='Street Food Festival at Law Garden Attracts Thousands',
                summary='Popular street food festival organized at Law Garden.',
                content='A street food festival was organized at Law Garden showcasing local Ahmedabad delicacies. Thousands of food lovers attended the event. Various stalls offered traditional Gujarati snacks.',
                location='Law Garden, Ahmedabad',
                incident_type='Event',
                published_date=base_date - timedelta(days=5)
            ),
            News(
                source_id=sources[2].source_id,
                title='Traffic Issues Continue on Ashram Road',
                summary='Daily commuters face traffic congestion on Ashram Road.',
                content='Traffic congestion on Ashram Road continues to trouble daily commuters. Citizens demand better traffic management and road widening. Peak hours see severe jams.',
                location='Ashram Road, Ahmedabad',
                incident_type='Traffic',
                published_date=base_date - timedelta(days=6)
            ),
            News(
                source_id=sources[5].source_id,
                title='Fire Breaks Out in Textile Market, No Casualties',
                summary='Fire incident at textile market in Kalupur area controlled quickly.',
                content='A fire broke out in a textile shop in Kalupur market area. Fire brigade reached quickly and controlled the fire. No casualties reported. Cause of fire under investigation.',
                location='Kalupur, Ahmedabad',
                incident_type='Fire',
                published_date=base_date - timedelta(days=7)
            ),
        ]
        
        db.session.add_all(news_articles)
        db.session.flush()  # ⭐ Get news_id before using them
        print(f"   ✅ Created {len(news_articles)} news articles")
        
        # Step 5: Create Incidents
        print("\n🔗 Step 5: Creating incidents (grouping related news)...")
        incidents = [
            Incident(
                incident_type='Accident',
                location='SG Highway, Ahmedabad',
                first_reported=(base_date - timedelta(days=1, hours=3)).date(),
                last_reported=(base_date - timedelta(days=1)).date()
            ),
            Incident(
                incident_type='Crime',
                location='Vastrapur, Ahmedabad',
                first_reported=(base_date - timedelta(days=2, hours=12)).date(),
                last_reported=(base_date - timedelta(days=2)).date()
            ),
        ]
        db.session.add_all(incidents)
        db.session.flush()  # ⭐ Get incident_id before using them
        print(f"   ✅ Created {len(incidents)} incidents")
        
        # Step 6: Link News to Incidents
        print("\n🔗 Step 6: Linking news articles to incidents...")
        incident_links = [
            # Incident 1: SG Highway Accident (3 news articles)
            IncidentNews(
                incident_id=incidents[0].incident_id,
                news_id=news_articles[0].news_id
            ),
            IncidentNews(
                incident_id=incidents[0].incident_id,
                news_id=news_articles[1].news_id
            ),
            IncidentNews(
                incident_id=incidents[0].incident_id,
                news_id=news_articles[2].news_id
            ),
            # Incident 2: Vastrapur Crime (2 news articles)
            IncidentNews(
                incident_id=incidents[1].incident_id,
                news_id=news_articles[3].news_id
            ),
            IncidentNews(
                incident_id=incidents[1].incident_id,
                news_id=news_articles[4].news_id
            ),
        ]
        db.session.add_all(incident_links)
        print(f"   ✅ Created {len(incident_links)} incident-news links")
        
        # Step 7: Create User History
        print("\n👁️ Step 7: Creating user viewing history...")
        history_entries = [
            UserHistory(user_id=users[0].user_id, news_id=news_articles[0].news_id),
            UserHistory(user_id=users[0].user_id, news_id=news_articles[3].news_id),
            UserHistory(user_id=users[0].user_id, news_id=news_articles[6].news_id),
            UserHistory(user_id=users[0].user_id, news_id=news_articles[0].news_id),  # Viewed twice
            UserHistory(user_id=users[1].user_id, news_id=news_articles[7].news_id),
            UserHistory(user_id=users[1].user_id, news_id=news_articles[8].news_id),
        ]
        db.session.add_all(history_entries)
        print(f"   ✅ Created {len(history_entries)} user history entries")
        
        # Commit all changes
        print("\n💾 Committing all changes to database...")
        db.session.commit()
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ DATABASE SEEDED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\n📊 Summary:")
        print(f"   • Users created:           {len(users)}")
        print(f"   • Sources created:         {len(sources)}")
        print(f"   • News articles created:   {len(news_articles)}")
        print(f"   • Incidents created:       {len(incidents)}")
        print(f"   • Incident links created:  {len(incident_links)}")
        print(f"   • History entries created: {len(history_entries)}")
        
        # Print test user credentials
        print("\n🔐 Test User Credentials:")
        print("   1. Username: demo_user  | Password: demo123")
        print("   2. Username: john_doe   | Password: john123")
        print("   3. Username: jane_smith | Password: jane123")
        
        print("\n🎉 Database is ready for testing!")
        print("=" * 60)


if __name__ == '__main__':
    try:
        seed_data()
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)