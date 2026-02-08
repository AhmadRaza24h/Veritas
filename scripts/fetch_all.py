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
    """
    Backfill NewsAPI ingestion for last 30 days (Gujarat-wide)
    Aligned with main ingestion logic (token-based, safe)
    """

    GUJARAT_CITIES = [
        'Ahmedabad','Surat','Vadodara','Rajkot','Bhavnagar',
        'Jamnagar','Junagadh','Gandhinagar','Anand','Nadiad',
        'Morbi','Surendranagar','Bharuch','Valsad','Vapi',
        'Navsari','Mehsana','Patan','Palanpur','Gandhidham',
        'Kheda','Botad','Amreli','Porbandar','Godhra'
    ]

    SOURCE_CATEGORY_MAP = {
        # Public
        "the times of india": "public",
        "timesofindia.indiatimes.com": "public",
        "the indian express": "public",
        "indianexpress.com": "public",
        "hindustan times": "public",
        "the hindu": "public",
        "ndtv": "public",
        "news18": "public",
        "indiatoday": "public",
        "theprint": "public",
        "newslaundry": "public",
        "scroll": "public",
        "the wire": "public",
        "the quint": "public",
        "rediff": "public",
        "divya bhaskar": "public",
        "gujarat samachar": "public",
        "sandesh": "public",
        "ahmedabad mirror": "public",
        "altnews": "public",
        "caravan": "public",
        "google news": "public",
        "yahoo": "public",

        # Neutral
        "reuters": "neutral",
        "bloomberg": "neutral",
        "businessline": "neutral",
        "livemint": "neutral",
        "business standard": "neutral",
        "moneycontrol": "neutral",
        "economictimes": "neutral",
        "bbc": "neutral",
        "cnbc": "neutral",
        "cna": "neutral",

        # Political
        "pib": "political",
        "press information bureau": "political",
        "dd news": "political",
        "doordarshan": "political",
        "newsonair": "political",
        "all india radio": "political",
        "sansad tv": "political",
    }

    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2/everything"

    # ---------- NORMALIZATION ----------
    def _normalize(self, s):
        s = (s or '').lower()
        s = re.sub(r'[^a-z0-9 ]+', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    def _get_source_category(self, source_obj):
        sid = self._normalize(source_obj.get('id'))
        sname = self._normalize(source_obj.get('name'))

        if sid in self.SOURCE_CATEGORY_MAP:
            return self.SOURCE_CATEGORY_MAP[sid]

        if sname in self.SOURCE_CATEGORY_MAP:
            return self.SOURCE_CATEGORY_MAP[sname]

        for k, v in self.SOURCE_CATEGORY_MAP.items():
            if k in sname or k in sid:
                return v

        if 'gov' in sname or 'press' in sname:
            return 'political'

        return 'neutral'

    # ---------- TOKENIZER ----------
    def _tokenize(self, text):
        text = (text or '').lower()
        text = re.sub(r'[^a-z0-9 ]+', ' ', text)
        return set(text.split())

    # ---------- LOCATION ----------
    def _extract_location(self, article):
        text = f"{article.get('title','')} {article.get('description','')} {article.get('content','')}".lower()
        text = re.sub(r'[^\w\s]', ' ', text)

        for city in self.GUJARAT_CITIES:
            if re.search(rf'\b{city.lower()}\b', text):
                return f"{city}, Gujarat"

        if 'gujarat' in text:
            return "Gujarat"

        return None

    # ---------- INCIDENT ----------
    def _extract_incident_type(self, article):
        tokens = self._tokenize(
            f"{article.get('title')} {article.get('description')} {article.get('content')}"
        )

        RULES = [
            ('Education', {'education','college','university','iim','iit','nit','exam','placement'}),
            ('Business', {'business','company','industry','investment','startup','profit','market'}),
            ('Health', {'health','hospital','doctor','covid','medical'}),
            ('Infrastructure', {'road','bridge','metro','highway','construction'}),
            ('Weather', {'rain','flood','cyclone','storm','heatwave'}),
            ('Politics', {'election','minister','government','policy','cabinet'}),
            ('Sports', {'cricket','ipl','match','tournament'}),
            ('Crime', {'murder','arrest','rape','robbery','theft','police','fir','assault'}),
        ]

        for label, kws in RULES:
            for kw in kws:
                if kw in tokens:
                    return label

        return 'General'

    # ---------- FETCH ----------
    def fetch_range(self, from_date, to_date):
        query = "(Gujarat OR Ahmedabad OR Surat OR Vadodara OR Rajkot OR Gandhinagar)"
        page = 1
        articles = []

        while True:
            r = requests.get(self.base_url, params={
                'q': query,
                'from': from_date,
                'to': to_date,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 100,
                'page': page,
                'apiKey': self.api_key
            }, timeout=15)

            if r.status_code != 200:
                break

            data = r.json().get('articles', [])
            if not data:
                break

            articles.extend(data)
            if len(data) < 100:
                break

            page += 1

        print(f"🔹 {from_date} → {to_date}: {len(articles)} fetched")
        return articles

    # ---------- SAVE ----------
    def save_articles(self, articles):
        saved_ids = []

        for art in articles:
            url = art.get('url')
            if not url or News.query.filter_by(url=url).first():
                continue

            location = self._extract_location(art)
            if not location:
                continue

            incident_type = self._extract_incident_type(art)

            source_obj = art.get('source', {})
            source_name = source_obj.get('name', 'Unknown')
            category = self._get_source_category(source_obj)

            source = Source.query.filter_by(source_name=source_name).first()
            if not source:
                source = Source(source_name=source_name, category=category)
                db.session.add(source)
                db.session.flush()

            try:
                pub_date = datetime.fromisoformat(
                    art['publishedAt'].replace('Z', '+00:00')
                ).date()
            except:
                pub_date = datetime.now().date()

            news = News(
                source_id=source.source_id,
                title=art.get('title','')[:500],
                summary=art.get('description',''),
                content=art.get('content',''),
                location=location,
                incident_type=incident_type,
                url=url,
                image_url=art.get('urlToImage'),
                published_date=pub_date
            )

            db.session.add(news)
            db.session.flush()
            saved_ids.append(news.news_id)

        db.session.commit()
        return saved_ids

    # ---------- INCIDENT LINK ----------
    def create_incidents(self, news_ids):
        if not news_ids:
            return

        news_list = News.query.filter(News.news_id.in_(news_ids)).all()
        groups = {}

        for n in news_list:
            groups.setdefault((n.incident_type, n.location), []).append(n)

        for (itype, loc), items in groups.items():
            dates = [i.published_date for i in items]

            incident = Incident.query.filter_by(
                incident_type=itype,
                location=loc
            ).first()

            if not incident:
                incident = Incident(
                    incident_type=itype,
                    location=loc,
                    first_reported=min(dates),
                    last_reported=max(dates)
                )
                db.session.add(incident)
                db.session.flush()

            for n in items:
                if not IncidentNews.query.filter_by(
                    incident_id=incident.incident_id,
                    news_id=n.news_id
                ).first():
                    db.session.add(IncidentNews(
                        incident_id=incident.incident_id,
                        news_id=n.news_id,
                        reported_at=n.published_date
                    ))

        db.session.commit()


# ===================== RUN =====================
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        API_KEY = os.getenv("NEWSAPI_KEY")
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
