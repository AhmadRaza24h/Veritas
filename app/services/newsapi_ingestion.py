"""
NewsAPI Ingestion Service for Gujarat State-Level News
Custom source categorization mapping (copy-paste ready)
"""
import requests
import re
from datetime import datetime, timedelta
from sqlalchemy import and_
from app.models import News, Source, Incident, IncidentNews
from app.extensions import db


class NewsAPIIngestion:
    """NewsAPI Ingestion Service for Gujarat State"""

    GUJARAT_CITIES = [
        'Ahmedabad', 'Surat', 'Vadodara', 'Rajkot', 'Bhavnagar',
        'Jamnagar', 'Junagadh', 'Gandhinagar', 'Anand', 'Nadiad',
        'Morbi', 'Surendranagar', 'Bharuch', 'Valsad', 'Vapi',
        'Navsari', 'Mehsana', 'Patan', 'Palanpur', 'Gandhidham',
        'Kheda', 'Botad', 'Amreli', 'Porbandar', 'Godhra'
    ]

    # === Exact + partial mapping to categories ===
    # Use normalized lowercase keys. Add / tweak as needed.
    SOURCE_CATEGORY_MAP = {
        # Public (mass readership, local reporting)
        "the times of india": "public",
        "timesofindia.indiatimes.com": "public",
        "the-times-of-india": "public",
        "the indian express": "public",
        "indianexpress.com": "public",
        "hindustan times": "public",
        "hindustantimes.com": "public",
        "the hindu": "public",
        "thehindu.com": "public",
        "ndtv": "public",
        "ndtv.com": "public",
        "news18": "public",
        "news18.com": "public",
        "india today": "public",
        "indiatoday.in": "public",
        "theprint": "public",
        "theprint.in": "public",
        "newslaundry": "public",
        "newslaundry.com": "public",
        "scroll": "public",
        "scroll.in": "public",
        "the wire": "public",
        "thewire.in": "public",
        "the quint": "public",
        "thequint.com": "public",
        "rediff": "public",
        "rediff.com": "public",
        "ahmedabad mirror": "public",
        "divya bhaskar": "public",
        "gujarat samachar": "public",
        "sandesh": "public",
        "statetimes": "public",
        "statetimes.in": "public",
        "yahoo": "public",
        "yahoo news": "public",
        "yahoo entertainment": "public",
        "google news": "public",
        "altnews": "public",
        "altnews.in": "public",
        "caravan": "public",
        "sarkarinaukriblog.com": "public",
        "gossiplankanews.com": "public",

        # Neutral (wire agencies, business, research, international)
        "reuters": "neutral",
        "reuters.com": "neutral",
        "bloomberg": "neutral",
        "bloomberg.com": "neutral",
        "businessline": "neutral",
        "thehindubusinessline": "neutral",
        "businessline.com": "neutral",
        "livemint": "neutral",
        "livemint.com": "neutral",
        "business standard": "neutral",
        "business-standard.com": "neutral",
        "moneycontrol": "neutral",
        "moneycontrol.com": "neutral",
        "economictimes": "neutral",
        "economictimes.com": "neutral",
        "economictimes.indiatimes.com": "neutral",
        "bbc": "neutral",
        "bbc news": "neutral",
        "bbc.co.uk": "neutral",
        "cna": "neutral",
        "channel newsasia": "neutral",
        "cnbc": "neutral",
        "cnbc-tv18": "neutral",
        "globalsecurity": "neutral",
        "globalsecurity.org": "neutral",
        "nature": "neutral",
        "nature.com": "neutral",
        "globenewswire": "neutral",
        "globenewswire.com": "neutral",
        "oilprice": "neutral",
        "oilprice.com": "neutral",
        "insurance journal": "neutral",
        "insurancejournal.com": "neutral",

        # Political / Official
        "pib": "political",
        "pib.gov.in": "political",
        "dd news": "political",
        "doordarshan": "political",
        "ddindia.gov.in": "political",
        "newsonair": "political",
        "newsonair.com": "political",
        "all india radio": "political",
        "air": "political",
        "sansad tv": "political",
        "government": "political",
        "press information bureau": "political"
    }

    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://newsapi.org/v2/everything'
        self.stats = {
            'fetched': 0, 'filtered': 0, 'inserted': 0, 'duplicates': 0,
            'incidents_created': 0, 'incidents_updated': 0,
            'by_category': {'public': 0, 'neutral': 0, 'political': 0},
            'by_incident': {}
        }

    def _normalize(self, s: str) -> str:
        """Lowercase and remove non-alphanumeric (keep spaces) for safe matching."""
        if not s:
            return ''
        s = s.lower()
        s = re.sub(r'[^a-z0-9 ]+', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    def _get_source_category(self, source_obj):
        """
        Categorize source using SOURCE_CATEGORY_MAP with:
        1) exact id match
        2) exact name match
        3) partial substring match
        default: 'neutral'
        """
        raw_id = (source_obj.get('id') or '') or ''
        raw_name = (source_obj.get('name') or '') or ''
        nid = self._normalize(raw_id)
        nname = self._normalize(raw_name)

        # 1) exact id
        if nid and nid in self.SOURCE_CATEGORY_MAP:
            return self.SOURCE_CATEGORY_MAP[nid]

        # 2) exact name
        if nname and nname in self.SOURCE_CATEGORY_MAP:
            return self.SOURCE_CATEGORY_MAP[nname]

        # 3) partial match (key contained in name or id)
        for key, category in self.SOURCE_CATEGORY_MAP.items():
            if key in nname or key in nid:
                return category

        # fallback
        if 'gov' in nname or 'gov' in nid or 'press' in nname:
            return 'political'

        return 'neutral'

    def fetch_gujarat_news(self, days=7, page_size=100, max_pages=2):
        """Fetch Gujarat news from NewsAPI"""
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        query = '(Gujarat OR Ahmedabad OR Surat OR Vadodara OR Rajkot OR Gandhinagar)'

        all_articles = []

        print(f"\n🔍 Fetching Gujarat news from NewsAPI...")
        print(f"   Period: {days} days | Pages: {max_pages}")

        for page in range(1, max_pages + 1):
            try:
                response = requests.get(self.base_url, params={
                    'q': query, 'from': from_date, 'sortBy': 'publishedAt',
                    'language': 'en', 'apiKey': self.api_key,
                    'pageSize': page_size, 'page': page
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

    def _extract_location(self, article):
        """Extract location from article text (title/description/content)"""
        combined = f"{article.get('title', '')} {article.get('description', '')} {article.get('content', '')}".lower()
        combined_clean = re.sub(r'[^\w\s]', ' ', combined)

        for city in self.GUJARAT_CITIES:
            pattern = rf'\b{city.lower()}\b'
            if re.search(pattern, combined_clean):
                return f"{city}, Gujarat"

        if 'gujarat' in combined_clean:
            return 'Gujarat'

        return None
    def _tokenize(self, text):
        """
        Convert text into a set of lowercase word tokens.
        SAFE: no substrings, no regex traps.
        """
        text = (text or '').lower()
        text = re.sub(r'[^a-z0-9 ]+', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return set(text.split())


    def _extract_incident_type(self, a):
        tokens = self._tokenize(f"{a.get('title')} {a.get('description')} {a.get('content')}")

        RULES = [
            ('Education', {
                'education', 'student', 'students', 'college', 'university',
                'iim', 'iit', 'nit', 'placement', 'placements', 'campus', 'exam'
            }),
            ('Business', {
                'business', 'company', 'industry', 'investment', 'economy',
                'market', 'startup', 'profit', 'loss', 'revenue'
            }),
            ('Health', {
                'health', 'hospital', 'doctor', 'medical', 'covid', 'vaccine'
            }),
            ('Infrastructure', {
                'road', 'bridge', 'metro', 'highway', 'construction', 'project'
            }),
            ('Weather', {
                'rain', 'flood', 'cyclone', 'storm', 'heatwave'
            }),
            ('Politics', {
                'election', 'minister', 'government', 'policy', 'cabinet'
            }),
            ('Sports', {
                'cricket', 'match', 'tournament', 'ipl', 'sports'
            }),
            # Crime LAST (dangerous keywords)
            ('Crime', {
                'murder', 'arrest', 'rape', 'robbery',
                'theft', 'police', 'fir', 'custody', 'assault'
            }),
        ]

        for label, keywords in RULES:
            for kw in keywords:
                if kw == kw and kw in tokens:
                    return label

        return 'General'

    def _process_articles(self, articles):
        """Process articles -> filter, extract location, incident type"""
        processed = []

        print(f"\n🔍 Processing {len(articles)} articles...")

        for article in articles:
            if not self._is_valid_article(article):
                continue

            location = self._extract_location(article)
            if not location:
                continue

            incident_type = self._extract_incident_type(article)
            self.stats['by_incident'][incident_type] = self.stats['by_incident'].get(incident_type, 0) + 1

            article['location'] = location
            article['incident_type'] = incident_type
            processed.append(article)

        self.stats['filtered'] = len(processed)
        print(f"✅ Valid after filtering: {len(processed)}")
        return processed

    def _save_to_database(self, articles):
        """Save articles with smart categorization"""
        print(f"\n💾 Saving {len(articles)} articles...")

        saved_news_ids = []

        for article in articles:
            try:
                url = (article.get('url') or '').strip()
                if not url:
                    continue

                # Duplicate check
                if News.query.filter_by(url=url).first():
                    self.stats['duplicates'] += 1
                    continue

                source_obj = article.get('source', {}) or {}
                source_name = source_obj.get('name') or 'Unknown'

                # Determine category first (so stats increment safe)
                category = self._get_source_category(source_obj)
                if category not in self.stats['by_category']:
                    self.stats['by_category'][category] = 0

                # Get or create source record
                source = Source.query.filter_by(source_name=source_name).first()
                if not source:
                    source = Source(source_name=source_name, category=category)
                    db.session.add(source)
                    db.session.flush()
                else:
                    # update category if changed (optional)
                    if source.category != category:
                        source.category = category
                        db.session.flush()

                # increment category distribution for this saved article
                self.stats['by_category'][category] += 1

                icon = {'public': '🟢', 'neutral': '🔵', 'political': '🟡'}.get(category, '🔵')
                print(f"   {icon} {source_name} → {category.upper()}")

                # parse published date safely
                published_at = article.get('publishedAt')
                try:
                    pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00')).date()
                except Exception:
                    pub_date = datetime.now().date()

                # Create news record
                news = News(
                    source_id=source.source_id,
                    title=(article.get('title') or '')[:500],
                    summary=article.get('description'),
                    content=article.get('content'),
                    location=article.get('location'),
                    incident_type=article.get('incident_type'),
                    url=url,
                    image_url=article.get('urlToImage'),
                    published_date=pub_date
                )

                db.session.add(news)
                db.session.flush()
                saved_news_ids.append(news.news_id)
                self.stats['inserted'] += 1

            except Exception as e:
                print(f"   ❌ Error saving article: {str(e)[:200]}")
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
            return

        print(f"\n🔗 Creating incidents...")
        news_list = News.query.filter(News.news_id.in_(news_ids)).all()

        # Group by (type, location)
        groups = {}
        for news in news_list:
            key = (news.incident_type, news.location)
            groups.setdefault(key, []).append(news)

        for (itype, loc), articles in groups.items():
            existing = Incident.query.filter_by(incident_type=itype, location=loc).first()

            if existing:
                # Link to existing
                for news in articles:
                    link = IncidentNews.query.filter_by(incident_id=existing.incident_id, news_id=news.news_id).first()
                    if not link:
                        db.session.add(IncidentNews(
                            incident_id=existing.incident_id,
                            news_id=news.news_id,
                            reported_at=news.published_date or datetime.now()
                        ))

                # Update existing dates
                dates = [n.published_date for n in articles if n.published_date]
                if dates:
                    if min(dates) < existing.first_reported:
                        existing.first_reported = min(dates)
                    if max(dates) > existing.last_reported:
                        existing.last_reported = max(dates)

                self.stats['incidents_updated'] += 1
            else:
                # Create new incident
                dates = [n.published_date for n in articles if n.published_date]
                incident = Incident(
                    incident_type=itype,
                    location=loc,
                    first_reported=min(dates) if dates else datetime.now().date(),
                    last_reported=max(dates) if dates else datetime.now().date()
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
                print(f"   ✅ {itype} at {loc} ({len(articles)} articles)")

        db.session.commit()
        print(f"   Total: {self.stats['incidents_created']} new, {self.stats['incidents_updated']} updated")

    def run_ingestion(self, days=7, page_size=100, max_pages=2):
        """Run complete pipeline"""
        articles = self.fetch_gujarat_news(days, page_size, max_pages)
        if not articles:
            return self.stats

        processed = self._process_articles(articles)
        if not processed:
            return self.stats

        saved_ids = self._save_to_database(processed)

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
