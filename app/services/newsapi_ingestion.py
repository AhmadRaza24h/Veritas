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

from app.models import News, Source
from app.extensions import db

logger = logging.getLogger(__name__)


class NewsAPIIngestion:
    """NewsAPI Ingestion Service with enhanced classification and grouping"""

    # Major countries for location extraction
    COUNTRIES = [
        'USA', 'United States', 'America', 'UK', 'United Kingdom', 'Britain',
        'India', 'China', 'Russia', 'France', 'Germany', 'Japan', 'Australia',
        'Canada', 'Brazil', 'Mexico', 'Italy', 'Spain', 'South Africa',
        'Argentina', 'South Korea', 'Indonesia', 'Turkey', 'Saudi Arabia',
        'Iran', 'Iraq', 'Israel', 'Palestine', 'Egypt', 'Nigeria', 'Pakistan',
        'Bangladesh', 'Vietnam', 'Thailand', 'Philippines', 'Malaysia',
        'Singapore', 'New Zealand', 'Ukraine', 'Poland', 'Netherlands',
        'Belgium', 'Sweden', 'Norway', 'Denmark', 'Finland', 'Switzerland',
        'Austria', 'Greece', 'Portugal', 'Ireland', 'Czech Republic'
    ]

    # Major cities for location extraction
    CITIES = [
        'New York', 'London', 'Paris', 'Tokyo', 'Mumbai', 'Delhi', 'Beijing',
        'Shanghai', 'Moscow', 'Sydney', 'Toronto', 'Los Angeles', 'Chicago',
        'Houston', 'San Francisco', 'Washington', 'Boston', 'Seattle',
        'Berlin', 'Madrid', 'Rome', 'Amsterdam', 'Brussels', 'Vienna',
        'Stockholm', 'Oslo', 'Copenhagen', 'Helsinki', 'Zurich', 'Geneva',
        'Dubai', 'Abu Dhabi', 'Riyadh', 'Tel Aviv', 'Jerusalem', 'Cairo',
        'Lagos', 'Nairobi', 'Johannesburg', 'Cape Town', 'Karachi', 'Lahore',
        'Dhaka', 'Bangkok', 'Manila', 'Jakarta', 'Singapore', 'Hong Kong',
        'Seoul', 'Taipei', 'Melbourne', 'Brisbane', 'Auckland', 'Wellington',
        'Mexico City', 'São Paulo', 'Rio de Janeiro', 'Buenos Aires',
        'Santiago', 'Lima', 'Bogotá', 'Caracas', 'Havana', 'Miami'
    ]

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
        self.similarity_threshold = 0.52  # Optimized for global news
        logger.info("✅ Loaded similarity detection model (threshold: 0.55)")
        
        self.stats = {
            'fetched': 0, 'filtered': 0, 'inserted': 0, 'duplicates': 0,
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

        # Exact id match
        if nid and nid in self.SOURCE_CATEGORY_MAP:
            return self.SOURCE_CATEGORY_MAP[nid]

        # Exact name match
        if nname and nname in self.SOURCE_CATEGORY_MAP:
            return self.SOURCE_CATEGORY_MAP[nname]

        # Partial match
        for key, category in self.SOURCE_CATEGORY_MAP.items():
            if key in nname or key in nid:
                return category

        # Fallback
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
        """
        Improved incident classification using strong substring matching.
        First matching category wins.
        """
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
        Extract location using word boundary matching only.
        No greedy regex patterns.
        """
        text = f"{article.get('title', '')} {article.get('description', '')}"
        
        # Check city list using word boundary
        for city in self.CITIES:
            if re.search(rf'\b{re.escape(city)}\b', text, re.IGNORECASE):
                return city

        # Check country list using word boundary
        for country in self.COUNTRIES:
            if re.search(rf'\b{re.escape(country)}\b', text, re.IGNORECASE):
                return country

        # Fallback
        return 'Global'

    def _check_similarity_with_embedding(self, article_embedding, recent_news_embeddings):
        """
        Check if article is similar to recent news using pre-calculated embedding.
        Compares with both DB articles AND articles saved earlier in same batch.
        
        Args:
            article_embedding: Pre-calculated embedding for new article
            recent_news_embeddings: Dict {news_id: (embedding, group_id)}
            
        Returns:
            tuple: (is_similar, original_group_id, similarity_score)
        """
        try:
            if not recent_news_embeddings:
                return False, None, 0.0
            
            # Compare with each recent article (DB + same batch)
            max_similarity = 0.0
            most_similar_group_id = None
            
            for news_id, (existing_embedding, group_id) in recent_news_embeddings.items():
                # Calculate cosine similarity
                similarity = cosine_similarity(
                    article_embedding.reshape(1, -1),
                    existing_embedding.reshape(1, -1)
                )[0][0]
                
                if similarity > max_similarity:
                    max_similarity = similarity
                    most_similar_group_id = group_id
            
            # Check if similar enough (0.60 threshold)
            is_similar = max_similarity >= self.similarity_threshold
            
            return is_similar, most_similar_group_id, float(max_similarity)
            
        except Exception as e:
            logger.error(f"Error in similarity check: {e}")
            return False, None, 0.0

    def _process_and_save(self, articles):
        """Process articles with improved classification and save to database"""
        print(f"\n💾 Processing and saving {len(articles)} articles...")

        # 🔥 STEP 1: Preload recent news (last 5 days)
        days_ago = datetime.utcnow() - timedelta(days=5)
        recent_news = News.query.filter(
            News.published_date >= days_ago.date()
        ).all()

        recent_news_embeddings = {}

        if recent_news:
            print(f"   📊 Pre-calculating embeddings for {len(recent_news)} recent articles (last 5 days)...")
            texts = [f"{n.title} {n.summary or ''}" for n in recent_news]
            embeddings = self.similarity_model.encode(texts)

            for i, n in enumerate(recent_news):
                recent_news_embeddings[n.news_id] = (
                    embeddings[i],
                    n.group_id or n.news_id
                )
        
        # 🔥 STEP 2: Batch encode NEW API articles
        print(f"   🚀 Batch encoding new articles...")
        valid_articles = [a for a in articles if self._is_valid_article(a)]
        new_texts = [
            f"{a.get('title','')} {a.get('description','')}"
            for a in valid_articles
        ]
        
        new_embeddings = self.similarity_model.encode(new_texts) if new_texts else []

        saved_news_ids = []

        # Process each article with pre-calculated embeddings
        for idx, article in enumerate(valid_articles):
            try:
                new_embedding = new_embeddings[idx]

                url = (article.get('url') or '').strip()
                if not url:
                    continue

                # Duplicate check
                if News.query.filter_by(url=url).first():
                    self.stats['duplicates'] += 1
                    continue

                # Extract location using improved method
                location = self._extract_location(article)

                # Classify incident type with 2+ keyword matching
                incident_type = self._classify_incident(article)
                self.stats['by_incident'][incident_type] = self.stats['by_incident'].get(incident_type, 0) + 1

                # Get or create source
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

                # Track category stats
                self.stats['by_category'][category] = self.stats['by_category'].get(category, 0) + 1

                # Parse published date
                published_at = article.get('publishedAt')
                try:
                    pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00')).date()
                except Exception:
                    pub_date = datetime.now().date()

                # Check similarity with existing news AND batch articles
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

                print(f"   🔍 Similarity Score: {max_similarity:.3f}")

                # Create news record
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
                db.session.flush()  # Get news_id

                # Set group_id based on similarity (threshold: 0.55)
                if max_similarity >= self.similarity_threshold:
                    news.group_id = matched_group_id
                    print(f"  🔗 Linked to group {matched_group_id} (similarity: {max_similarity:.3f}) | {incident_type} | {location}")
                else:
                    news.group_id = news.news_id
                    print(f"  ✨ New story (group: {news.news_id}) | {incident_type} | {location}")

                # Flush again to persist group_id
                db.session.flush()
                
                # 🔥 ADD NEW ARTICLE INTO MEMORY (CRITICAL FIX)
                recent_news_embeddings[news.news_id] = (
                    new_embedding,
                    news.group_id
                )

                saved_news_ids.append(news.news_id)
                self.stats['inserted'] += 1

            except Exception as e:
                print(f"   ❌ Error saving article: {str(e)[:200]}")
                db.session.rollback()
                continue

        try:
            db.session.commit()
            print(f"✅ Saved {self.stats['inserted']} global news articles!")
        except Exception as e:
            print(f"❌ Commit error: {e}")
            db.session.rollback()
            return []

        return saved_news_ids

    def run_ingestion(self, days=30, page_size=100, max_pages=2):
        """Run complete pipeline"""
        articles = self.fetch_global_news(days, page_size, max_pages)
        if not articles:
            return self.stats

        saved_ids = self._process_and_save(articles)
        return self.stats

    def print_stats(self):
        """Print detailed statistics"""
        print("\n" + "=" * 70)
        print("📊 FINAL STATISTICS")
        print("=" * 70)
        print(f"   Fetched:       {self.stats['fetched']}")
        print(f"   Saved:         {self.stats['inserted']}")
        print(f"   Duplicates:    {self.stats['duplicates']}")

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
