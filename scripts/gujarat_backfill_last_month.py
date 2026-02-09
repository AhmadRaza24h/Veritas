#!/usr/bin/env python3
import sys
import os
import requests
import re
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models import News, Source, Incident, IncidentNews


class GujaratBackfillIngestion:

    GUJARAT_CITIES = [
        'Ahmedabad','Surat','Vadodara','Rajkot','Bhavnagar',
        'Jamnagar','Junagadh','Gandhinagar','Anand','Nadiad',
        'Morbi','Surendranagar','Bharuch','Valsad','Vapi',
        'Navsari','Mehsana','Patan','Palanpur','Gandhidham',
        'Kheda','Botad','Amreli','Porbandar','Godhra'
    ]

    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2/everything"

    # ---------------- SOURCE CATEGORY ----------------
    def _get_source_category(self, source_obj):
        name = (source_obj.get("name") or "").lower()
        name = re.sub(r'[^a-z0-9 ]', '', name)

        if any(x in name for x in [
            'times of india','indian express','hindustan times',
            'ndtv','news18','the hindu','divya bhaskar',
            'gujarat samachar','sandesh','the wire','scroll'
        ]):
            return 'public'

        if any(x in name for x in [
            'pib','doordarshan','dd news','sansad tv','all india radio'
        ]):
            return 'political'

        return 'neutral'

    # ---------------- LOCATION ----------------
    def _extract_location(self, article):
        text = f"{article.get('title','')} {article.get('description','')} {article.get('content','')}".lower()
        text = re.sub(r'[^\w\s]', ' ', text)

        for city in self.GUJARAT_CITIES:
            if re.search(rf'\b{city.lower()}(based|\'s| district)?\b', text):
                return f"{city}, Gujarat"

        if 'gujarat' in text:
            return "Gujarat"

        return None

    # ---------------- INCIDENT ----------------
    def _extract_incident_type(self, article):
        text = f"{article.get('title','')} {article.get('description','')} {article.get('content','')}".lower()

        RULES = [
            ('Crime',['murder','arrest','robbery','rape','crime','police','fir']),
            ('Fire',['fire','blaze','explosion']),
            ('Accident',['accident','collision','crash','injured','killed']),
            ('Weather',['flood','rain','cyclone','storm']),
            ('Infrastructure',['bridge','road','metro','construction']),
            ('Business',['investment','startup','company','industry','crore','profit']),
            ('Health',['hospital','covid','health']),
            ('Education',['exam','college','school']),
            ('Politics',['election','minister','government']),
            ('Sports',['cricket','ipl','match']),
        ]

        for itype, kws in RULES:
            if any(k in text for k in kws):
                return itype

        return 'General'

    # ---------------- FETCH ----------------
    def fetch_range(self, from_date, to_date):
        query = "(Gujarat OR Ahmedabad OR Surat OR Vadodara OR Rajkot OR Gandhinagar)"
        all_articles = []

        page = 1
        while True:
            resp = requests.get(self.base_url, params={
                'q': query,
                'from': from_date,
                'to': to_date,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 100,
                'page': page,
                'apiKey': self.api_key
            }, timeout=15)

            if resp.status_code != 200:
                break

            data = resp.json().get("articles", [])
            if not data:
                break

            all_articles.extend(data)
            if len(data) < 100:
                break

            page += 1

        print(f"   🔹 {from_date} → {to_date}: {len(all_articles)} fetched")
        return all_articles

    # ---------------- SAVE ----------------
    def save_articles(self, articles):
        saved_ids = []

        for art in articles:
            url = art.get("url")
            if not url or News.query.filter_by(url=url).first():
                continue

            location = self._extract_location(art)
            if not location:
                continue

            incident_type = self._extract_incident_type(art)

            # Source
            source_obj = art.get("source", {})
            source_name = source_obj.get("name", "Unknown")
            category = self._get_source_category(source_obj)

            source = Source.query.filter_by(source_name=source_name).first()
            if not source:
                source = Source(source_name=source_name, category=category)
                db.session.add(source)
                db.session.flush()

            # Date
            try:
                pub_date = datetime.fromisoformat(
                    art["publishedAt"].replace("Z","+00:00")
                ).date()
            except:
                pub_date = datetime.now().date()

            news = News(
                source_id=source.source_id,
                title=art.get("title","")[:500],
                summary=art.get("description",""),
                content=art.get("content",""),
                location=location,
                incident_type=incident_type,
                url=url,
                image_url=art.get("urlToImage"),
                published_date=pub_date
            )

            db.session.add(news)
            db.session.flush()
            saved_ids.append(news.news_id)

        db.session.commit()
        return saved_ids

    # ---------------- INCIDENT LINK ----------------
    def create_incidents(self, news_ids):
        if not news_ids:
            return

        news_list = News.query.filter(News.news_id.in_(news_ids)).all()
        groups = {}

        for n in news_list:
            groups.setdefault((n.incident_type,n.location), []).append(n)

        for (itype,loc), items in groups.items():
            existing = Incident.query.filter(
                Incident.incident_type==itype,
                Incident.location==loc,
                Incident.last_reported >= datetime.now().date() - timedelta(days=3)
            ).first()

            if not existing:
                dates = [i.published_date for i in items]
                existing = Incident(
                    incident_type=itype,
                    location=loc,
                    first_reported=min(dates),
                    last_reported=max(dates)
                )
                db.session.add(existing)
                db.session.flush()

            for n in items:
                if not IncidentNews.query.filter_by(
                    incident_id=existing.incident_id,
                    news_id=n.news_id
                ).first():
                    db.session.add(IncidentNews(
                        incident_id=existing.incident_id,
                        news_id=n.news_id,
                        reported_at=n.published_date
                    ))

        db.session.commit()


# ===================== RUN =====================
if __name__ == "__main__":
    app = create_app()
    with app.app_context():

        API_KEY = os.getenv("NEWSAPI_KEY")  # env variable
        ingestor = GujaratBackfillIngestion(API_KEY)

        end = datetime.now().date()
        start = end - timedelta(days=30)

        cur = start
        while cur < end:
            chunk_end = min(cur + timedelta(days=7), end)
            articles = ingestor.fetch_range(cur.isoformat(), chunk_end.isoformat())
            saved = ingestor.save_articles(articles)
            ingestor.create_incidents(saved)
            cur = chunk_end

        print("\n✅ Gujarat last-month backfill completed successfully!")
