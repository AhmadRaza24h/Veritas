"""
NewsAPI Ingestion Service for Global World News
With improved similarity detection, incident classification, and location extraction
"""
import requests
import re
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging

from app.models import News, Source, Incident, IncidentNews
from app.extensions import db

logger = logging.getLogger(__name__)


class NewsAPIIngestion:
    """NewsAPI Ingestion Service with enhanced classification and grouping"""

    # Major countries and regions
    COUNTRIES = {
        'United States': ['USA', 'United States', 'America', 'US'],
        'United Kingdom': ['UK', 'United Kingdom', 'Britain', 'Great Britain'],
        'India': ['India'],
        'China': ['China', 'Chinese'],
        'Russia': ['Russia', 'Russian Federation'],
        'France': ['France', 'French'],
        'Germany': ['Germany', 'German'],
        'Japan': ['Japan', 'Japanese'],
        'Australia': ['Australia', 'Australian'],
        'Canada': ['Canada', 'Canadian'],
        'Brazil': ['Brazil', 'Brazilian'],
        'Mexico': ['Mexico', 'Mexican'],
        'Italy': ['Italy', 'Italian'],
        'Spain': ['Spain', 'Spanish'],
        'South Africa': ['South Africa'],
        'Argentina': ['Argentina'],
        'South Korea': ['South Korea', 'Korea'],
        'Indonesia': ['Indonesia'],
        'Turkey': ['Turkey', 'Turkish'],
        'Saudi Arabia': ['Saudi Arabia', 'Saudi'],
        'Iran': ['Iran', 'Iranian'],
        'Iraq': ['Iraq', 'Iraqi'],
        'Israel': ['Israel', 'Israeli'],
        'Palestine': ['Palestine', 'Palestinian'],
        'Egypt': ['Egypt', 'Egyptian'],
        'Nigeria': ['Nigeria'],
        'Pakistan': ['Pakistan'],
        'Bangladesh': ['Bangladesh'],
        'Vietnam': ['Vietnam', 'Vietnamese'],
        'Thailand': ['Thailand'],
        'Philippines': ['Philippines', 'Filipino'],
        'Malaysia': ['Malaysia'],
        'Singapore': ['Singapore'],
        'New Zealand': ['New Zealand'],
        'Ukraine': ['Ukraine', 'Ukrainian'],
        'Poland': ['Poland', 'Polish'],
        'Netherlands': ['Netherlands', 'Dutch'],
        'Belgium': ['Belgium'],
        'Sweden': ['Sweden', 'Swedish'],
        'Norway': ['Norway', 'Norwegian'],
        'Denmark': ['Denmark', 'Danish'],
        'Finland': ['Finland', 'Finnish'],
        'Switzerland': ['Switzerland', 'Swiss'],
        'Austria': ['Austria', 'Austrian'],
        'Greece': ['Greece', 'Greek'],
        'Portugal': ['Portugal', 'Portuguese'],
        'Ireland': ['Ireland', 'Irish'],
        'Czech Republic': ['Czech Republic', 'Czech']
    }

    # US States for better USA location detection
    US_STATES = {
        'California': ['California', 'CA'],
        'Texas': ['Texas', 'TX'],
        'New York': ['New York', 'NY'],
        'Florida': ['Florida', 'FL'],
        'Illinois': ['Illinois', 'IL'],
        'Pennsylvania': ['Pennsylvania', 'PA'],
        'Ohio': ['Ohio', 'OH'],
        'Georgia': ['Georgia', 'GA'],
        'North Carolina': ['North Carolina', 'NC'],
        'Michigan': ['Michigan', 'MI'],
        'Washington': ['Washington State', 'WA'],
        'Arizona': ['Arizona', 'AZ'],
        'Massachusetts': ['Massachusetts', 'MA'],
        'Virginia': ['Virginia', 'VA'],
        'Colorado': ['Colorado', 'CO']
    }

    # Indian States for better India location detection
    INDIAN_STATES = {
        'Gujarat': ['Gujarat'],
        'Maharashtra': ['Maharashtra', 'Mumbai', 'Pune'],
        'Delhi': ['Delhi', 'New Delhi'],
        'Karnataka': ['Karnataka', 'Bangalore', 'Bengaluru'],
        'Tamil Nadu': ['Tamil Nadu', 'Chennai'],
        'Uttar Pradesh': ['Uttar Pradesh', 'UP'],
        'West Bengal': ['West Bengal', 'Kolkata'],
        'Rajasthan': ['Rajasthan', 'Jaipur'],
        'Madhya Pradesh': ['Madhya Pradesh', 'MP'],
        'Kerala': ['Kerala'],
        'Punjab': ['Punjab'],
        'Haryana': ['Haryana'],
        'Bihar': ['Bihar'],
        'Andhra Pradesh': ['Andhra Pradesh', 'Hyderabad'],
        'Telangana': ['Telangana']
    }

    # Source categorization mapping
    SOURCE_CATEGORY_MAP = {
        # Public (mass readership)
        "the times of india": "public", "timesofindia.indiatimes.com": "public",
        "the indian express": "public", "indianexpress.com": "public",
        "hindustan times": "public", "hindustantimes.com": "public",
        "the hindu": "public", "thehindu.com": "public",
        "ndtv": "public", "ndtv.com": "public",
        "news18": "public", "news18.com": "public",
        "india today": "public", "indiatoday.in": "public",
        "theprint": "public", "theprint.in": "public",
        "scroll": "public", "scroll.in": "public",
        "the wire": "public", "thewire.in": "public",
        "the quint": "public", "thequint.com": "public",
        "cnn": "public", "cnn.com": "public",
        "bbc": "public", "bbc.com": "public", "bbc.co.uk": "public",
        "aljazeera": "public", "aljazeera.com": "public",
        "guardian": "public", "theguardian.com": "public",
        "new york times": "public", "nytimes.com": "public",
        "washington post": "public", "washingtonpost.com": "public",
        
        # Neutral (wire agencies, business)
        "reuters": "neutral", "reuters.com": "neutral",
        "bloomberg": "neutral", "bloomberg.com": "neutral",
        "associated press": "neutral", "ap.org": "neutral",
        "afp": "neutral", "agence france-presse": "neutral",
        "livemint": "neutral", "livemint.com": "neutral",
        "business standard": "neutral", "business-standard.com": "neutral",
        "moneycontrol": "neutral", "moneycontrol.com": "neutral",
        "economictimes": "neutral", "economictimes.indiatimes.com": "neutral",
        
        # Political / Official
        "pib": "political", "pib.gov.in": "political",
        "dd news": "political", "doordarshan": "political",
        "newsonair": "political", "all india radio": "political"
    }

    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://newsapi.org/v2/everything'
        
        # Initialize similarity model
        self.similarity_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.similarity_threshold = 0.52
        logger.info("✅ Loaded similarity detection model (threshold: 0.52)")
        
        self.stats = {
            'fetched': 0, 'filtered': 0, 'inserted': 0, 'duplicates': 0,
            'incidents_created': 0, 'incidents_updated': 0,
            'by_category': {},
            'by_incident': {}
        }

    def _normalize(self, s: str) -> str:
        """Lowercase and remove non-alphanumeric for safe matching."""
        if not s:
            return ''
        s = s.lower()
        s = re.sub(r'[^a-z0-9 ]+', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    def _get_source_category(self, source_obj):
        """Categorize source using SOURCE_CATEGORY_MAP."""
        raw_id = (source_obj.get('id') or '') or ''
        raw_name = (source_obj.get('name') or '') or ''
        nid = self._normalize(raw_id)
        nname = self._normalize(raw_name)

        if nid and nid in self.SOURCE_CATEGORY_MAP:
            return self.SOURCE_CATEGORY_MAP[nid]

        if nname and nname in self.SOURCE_CATEGORY_MAP:
            return self.SOURCE_CATEGORY_MAP[nname]

        for key, category in self.SOURCE_CATEGORY_MAP.items():
            if key in nname or key in nid:
                return category

        if 'gov' in nname or 'gov' in nid or 'press' in nname:
            return 'political'

        return 'neutral'

    def fetch_global_news(self, days=30, page_size=100, max_pages=2):
        """Fetch global world news from NewsAPI"""
        to_date = datetime.utcnow().date()
        from_date = to_date - timedelta(days=days)

        all_articles = []

        print(f"\n🔍 Fetching global world news from NewsAPI...")
        print(f"   Period: {days} days | Pages: {max_pages}")

        for page in range(1, max_pages + 1):
            try:
                response = requests.get(self.base_url, params={
                    'q': 'world OR international OR global',
                    'from': from_date.isoformat(),
                    'to': to_date.isoformat(),
                    'sortBy': 'publishedAt',
                    'language': 'en',
                    'apiKey': self.api_key,
                    'pageSize': page_size,
                    'page': page
                }, timeout=15)

                if response.status_code == 200:
                    articles = response.json().get('articles', [])
                    all_articles.extend(articles)
                    print(f"   ✅ Page {page}: {len(articles)} articles")
                    if len(articles) < page_size:
                        break
                else:
                    print(f"   ⚠️  Error {response.status_code} - {response.text[:200]}")
                    break
            except Exception as e:
                print(f"   ❌ {e}")
                break

        self.stats['fetched'] = len(all_articles)
        print(f"✅ Total fetched: {len(all_articles)}")
        return all_articles

    def _is_valid_article(self, article):
        """Quality check"""
        title = article.get('title', '') or ''
        desc = article.get('description', '') or ''

        if not title or not desc or len(title) < 10:
            return False

        combined = f"{title} {desc} {article.get('content', '')}".lower()
        if any(x in combined for x in ['[removed]', '[deleted]', 'subscribe to']):
            return False

        return True

    def _tokenize(self, text):
        """Convert text into a set of lowercase word tokens."""
        text = (text or '').lower()
        text = re.sub(r'[^a-z0-9 ]+', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return set(text.split())

    def _classify_incident(self, article):
        """Improved incident classification"""
        text = f"{article.get('title','')} {article.get('description','')} {article.get('content','')}".lower()

        RULES = [
            ('Crime', [
                'murder','killed','killing','rape','robbery','theft','fraud',
                'arrest','assault','crime','criminal','shooting','gunfire',
                'police','custody','investigation','suspect','charged','court',
                'kidnap','kidnapping','violence','stab','stabbing'
            ]),
            ('Politics', [
                'election','elections','minister','government','parliament',
                'policy','president','senate','vote','voting','bill','law',
                'cabinet','congress','political','campaign'
            ]),
            ('International', [
                'war','conflict','diplomacy','summit','sanctions','global',
                'international','military','border','ceasefire','foreign',
                'tensions','alliance'
            ]),
            ('Business', [
                'company','market','economy','economic','investment','revenue',
                'stocks','trade','business','profit','loss','shares','ipo',
                'corporate','industry','finance','bank','banking'
            ]),
            ('Technology', [
                'ai','artificial intelligence','software','startup','cyber',
                'tech','technology','app','digital','data','hacking',
                'cyberattack','innovation','device'
            ]),
            ('Health', [
                'hospital','virus','vaccine','disease','covid','health',
                'medical','infection','doctor','treatment','surgery'
            ]),
            ('Weather', [
                'flood','flooding','cyclone','storm','heatwave','earthquake',
                'wildfire','hurricane','rain','snow','temperature',
                'climate','weather','monsoon'
            ]),
            ('Sports', [
                'match','tournament','cricket','football','league',
                'championship','sports','final','semi final','goal',
                'victory','defeat','olympics','world cup'
            ])
        ]

        for label, keywords in RULES:
            if any(keyword in text for keyword in keywords):
                return label

        return 'General'

    def _extract_location(self, article):
        """
        Extract location: Priority = State > Country > Global
        Returns format: "State, Country" or "Country"
        """
        text = f"{article.get('title', '')} {article.get('description', '')}"
        
        detected_country = None
        detected_state = None
        
        # Step 1: Check US States first
        for state_name, variants in self.US_STATES.items():
            for variant in variants:
                if re.search(rf'\b{re.escape(variant)}\b', text, re.IGNORECASE):
                    detected_state = state_name
                    detected_country = 'United States'
                    return f"{detected_state}, {detected_country}"
        
        # Step 2: Check Indian States
        for state_name, variants in self.INDIAN_STATES.items():
            for variant in variants:
                if re.search(rf'\b{re.escape(variant)}\b', text, re.IGNORECASE):
                    detected_state = state_name
                    detected_country = 'India'
                    return f"{detected_state}, {detected_country}"
        
        # Step 3: Check Countries (if no state found)
        for country_name, variants in self.COUNTRIES.items():
            for variant in variants:
                if re.search(rf'\b{re.escape(variant)}\b', text, re.IGNORECASE):
                    return country_name
        
        # Fallback
        return 'Global'

    def _process_and_save(self, articles):
        """Process articles and save to database"""
        print(f"\n💾 Processing and saving {len(articles)} articles...")

        days_ago = datetime.utcnow() - timedelta(days=5)
        recent_news = News.query.filter(
            News.published_date >= days_ago.date()
        ).all()

        recent_news_embeddings = {}

        if recent_news:
            print(f"   📊 Pre-calculating embeddings for {len(recent_news)} recent articles...")
            texts = [f"{n.title} {n.summary or ''}" for n in recent_news]
            embeddings = self.similarity_model.encode(texts)

            for i, n in enumerate(recent_news):
                recent_news_embeddings[n.news_id] = (
                    embeddings[i],
                    n.group_id or n.news_id
                )
        
        print(f"   🚀 Batch encoding new articles...")
        valid_articles = [a for a in articles if self._is_valid_article(a)]
        new_texts = [
            f"{a.get('title','')} {a.get('description','')}"
            for a in valid_articles
        ]
        
        new_embeddings = self.similarity_model.encode(new_texts) if new_texts else []

        saved_news_ids = []

        for idx, article in enumerate(valid_articles):
            try:
                new_embedding = new_embeddings[idx]

                url = (article.get('url') or '').strip()
                if not url:
                    continue

                if News.query.filter_by(url=url).first():
                    self.stats['duplicates'] += 1
                    continue

                # Extract location (State, Country format)
                location = self._extract_location(article)

                incident_type = self._classify_incident(article)
                self.stats['by_incident'][incident_type] = self.stats['by_incident'].get(incident_type, 0) + 1

                source_obj = article.get('source', {}) or {}
                source_name = source_obj.get('name') or 'Unknown'
                category = self._get_source_category(source_obj)

                source = Source.query.filter_by(source_name=source_name).first()
                if not source:
                    source = Source(source_name=source_name, category=category)
                    db.session.add(source)
                    db.session.flush()
                else:
                    if source.category != category:
                        source.category = category
                        db.session.flush()

                self.stats['by_category'][category] = self.stats['by_category'].get(category, 0) + 1

                published_at = article.get('publishedAt')
                try:
                    pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00')).date()
                except Exception:
                    pub_date = datetime.now().date()

                max_similarity = 0.0
                matched_group_id = None

                for existing_embedding, group_id in recent_news_embeddings.values():
                    similarity = cosine_similarity(
                        new_embedding.reshape(1, -1),
                        existing_embedding.reshape(1, -1)
                    )[0][0]

                    if similarity > max_similarity:
                        max_similarity = similarity
                        matched_group_id = group_id

                news = News(
                    source_id=source.source_id,
                    title=(article.get('title') or '')[:500],
                    summary=article.get('description'),
                    content=article.get('content'),
                    location=location,
                    incident_type=incident_type,
                    url=url,
                    image_url=article.get('urlToImage'),
                    published_date=pub_date
                )

                db.session.add(news)
                db.session.flush()

                if max_similarity >= self.similarity_threshold:
                    news.group_id = matched_group_id
                    print(f"  🔗 Group {matched_group_id} (sim: {max_similarity:.2f}) | {incident_type} | {location}")
                else:
                    news.group_id = news.news_id
                    print(f"  ✨ New story {news.news_id} | {incident_type} | {location}")

                db.session.flush()
                
                recent_news_embeddings[news.news_id] = (
                    new_embedding,
                    news.group_id
                )

                saved_news_ids.append(news.news_id)
                self.stats['inserted'] += 1

            except Exception as e:
                print(f"   ❌ Error: {str(e)[:200]}")
                db.session.rollback()
                continue

        try:
            db.session.commit()
            print(f"✅ Saved {self.stats['inserted']} articles!")
        except Exception as e:
            print(f"❌ Commit error: {e}")
            db.session.rollback()
            return []

        return saved_news_ids

    def _create_incidents(self, news_ids):
        """Create incidents from saved news"""
        if not news_ids:
            print("\n⚠️  No news IDs to create incidents")
            return

        print(f"\n🔗 Creating incidents from {len(news_ids)} news articles...")
        
        try:
            news_list = News.query.filter(News.news_id.in_(news_ids)).all()
            print(f"   📰 Retrieved {len(news_list)} news records")

            # Group by (incident_type, location) for better grouping
            groups = {}
            for news in news_list:
                key = (news.incident_type, news.location)
                groups.setdefault(key, []).append(news)

            print(f"   📊 Grouped into {len(groups)} incident groups:")
            for (itype, loc), articles in groups.items():
                print(f"      - {itype} at {loc}: {len(articles)} articles")

            for (itype, loc), articles in groups.items():
                try:
                    dates = [a.published_date for a in articles if a.published_date]
                    if not dates:
                        continue
                    
                    min_date = min(dates)
                    max_date = max(dates)
                    
                    # Check existing incident (7-day window, same type and location)
                    existing = Incident.query.filter(
                        Incident.incident_type == itype,
                        Incident.location == loc,
                        Incident.first_reported >= (min_date - timedelta(days=7)),
                        Incident.last_reported <= (max_date + timedelta(days=7))
                    ).first()

                    if existing:
                        for news in articles:
                            link = IncidentNews.query.filter_by(
                                incident_id=existing.incident_id,
                                news_id=news.news_id
                            ).first()
                            
                            if not link:
                                db.session.add(IncidentNews(
                                    incident_id=existing.incident_id,
                                    news_id=news.news_id,
                                    reported_at=news.published_date or datetime.now()
                                ))

                        if min_date < existing.first_reported:
                            existing.first_reported = min_date
                        if max_date > existing.last_reported:
                            existing.last_reported = max_date

                        self.stats['incidents_updated'] += 1
                        print(f"   ✅ Updated: {itype} at {loc} ({len(articles)} articles)")
                    else:
                        incident = Incident(
                            incident_type=itype,
                            location=loc,
                            first_reported=min_date,
                            last_reported=max_date
                        )
                        db.session.add(incident)
                        db.session.flush()

                        for news in articles:
                            db.session.add(IncidentNews(
                                incident_id=incident.incident_id,
                                news_id=news.news_id,
                                reported_at=news.published_date or datetime.now()
                            ))

                        self.stats['incidents_created'] += 1
                        print(f"   ✅ Created: {itype} at {loc} ({len(articles)} articles)")
                
                except Exception as e:
                    print(f"   ❌ Error creating incident for {itype} at {loc}: {e}")
                    continue

            db.session.commit()
            print(f"\n   📊 Total: {self.stats['incidents_created']} new, {self.stats['incidents_updated']} updated")
            
            incident_count = Incident.query.count()
            link_count = IncidentNews.query.count()
            print(f"   ✅ Verification: {incident_count} incidents, {link_count} links in database")

        except Exception as e:
            print(f"   ❌ Critical error in _create_incidents: {e}")
            db.session.rollback()

    def run_ingestion(self, days=30, page_size=100, max_pages=2):
        """Run complete pipeline"""
        articles = self.fetch_global_news(days, page_size, max_pages)
        if not articles:
            return self.stats

        saved_ids = self._process_and_save(articles)
        
        if saved_ids:
            self._create_incidents(saved_ids)
        
        return self.stats

    def print_stats(self):
        """Print detailed statistics"""
        print("\n" + "=" * 70)
        print("📊 FINAL STATISTICS")
        print("=" * 70)
        print(f"   Fetched:       {self.stats['fetched']}")
        print(f"   Saved:         {self.stats['inserted']}")
        print(f"   Duplicates:    {self.stats['duplicates']}")
        print(f"   Incidents:     {self.stats['incidents_created']} new, {self.stats['incidents_updated']} updated")

        print(f"\n📰 Sources Distribution:")
        total = sum(self.stats['by_category'].values())
        if total > 0:
            for cat in ['public', 'neutral', 'political']:
                count = self.stats['by_category'].get(cat, 0)
                pct = (count / total * 100) if total > 0 else 0
                icon = {'public': '🟢', 'neutral': '🔵', 'political': '🟡'}.get(cat, '🔵')
                print(f"   {icon} {cat.upper():10s} {count:3d} ({pct:5.1f}%)")

        print(f"\n📋 By Incident Type:")
        for itype, count in sorted(self.stats['by_incident'].items(), key=lambda x: x[1], reverse=True):
            print(f"   {itype:15s} {count}")
        print("=" * 70)