"""
NewsAPI Ingestion Service for Global World News
With improved similarity detection, incident classification, and location extraction
"""
import requests
import re
from collections import defaultdict
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

    # Combined states map for countries (avoid short ambiguous abbreviations)
    STATES = {
        'United States': {
            'California': ['California', 'Los Angeles', 'San Francisco', 'San Diego'],
            'Texas': ['Texas', 'Houston', 'Dallas', 'Austin'],
            'New York': ['New York', 'New York City', 'Buffalo'],
            'Florida': ['Florida', 'Miami', 'Orlando'],
            'Illinois': ['Illinois', 'Chicago'],
            'Pennsylvania': ['Pennsylvania', 'Philadelphia'],
            'Ohio': ['Ohio', 'Columbus'],
            'Georgia': ['Georgia', 'Atlanta'],
            'North Carolina': ['North Carolina', 'Charlotte', 'Raleigh'],
            'Michigan': ['Michigan', 'Detroit'],
            'Washington': ['Washington State', 'Seattle'],
            'Arizona': ['Arizona', 'Phoenix'],
            'Massachusetts': ['Massachusetts', 'Boston'],
            'Virginia': ['Virginia', 'Richmond'],
            'Colorado': ['Colorado', 'Denver']
        },
        'India': {
            'Gujarat': ['Gujarat', 'Ahmedabad'],
            'Maharashtra': ['Maharashtra', 'Mumbai', 'Pune'],
            'Delhi': ['Delhi', 'New Delhi'],
            'Karnataka': ['Karnataka', 'Bengaluru', 'Bangalore'],
            'Tamil Nadu': ['Tamil Nadu', 'Chennai'],
            'Uttar Pradesh': ['Uttar Pradesh', 'Lucknow'],
            'West Bengal': ['West Bengal', 'Kolkata'],
            'Rajasthan': ['Rajasthan', 'Jaipur'],
            'Madhya Pradesh': ['Madhya Pradesh', 'Bhopal'],
            'Kerala': ['Kerala', 'Thiruvananthapuram'],
            'Punjab': ['Punjab', 'Chandigarh'],
            'Haryana': ['Haryana', 'Gurugram'],
            'Bihar': ['Bihar', 'Patna'],
            'Andhra Pradesh': ['Andhra Pradesh', 'Vishakhapatnam'],
            'Telangana': ['Telangana', 'Hyderabad']
        },
        'United Kingdom': {
            'England': ['England', 'London', 'Manchester', 'Birmingham'],
            'Scotland': ['Scotland', 'Edinburgh', 'Glasgow'],
            'Wales': ['Wales', 'Cardiff'],
            'Northern Ireland': ['Northern Ireland', 'Belfast']
        },
        'China': {
            'Beijing': ['Beijing'],
            'Shanghai': ['Shanghai'],
            'Guangdong': ['Guangdong', 'Guangzhou', 'Shenzhen'],
            'Sichuan': ['Sichuan', 'Chengdu']
        },
        'Russia': {
            'Moscow': ['Moscow'],
            'Saint Petersburg': ['Saint Petersburg'],
            'Siberia': ['Siberia', 'Novosibirsk']
        },
        'France': {
            'Île-de-France': ['Île-de-France', 'Paris'],
            'Provence-Alpes-Côte d\'Azur': ['Marseille', 'Nice']
        },
        'Germany': {
            'Bavaria': ['Bavaria', 'Munich'],
            'Berlin': ['Berlin'],
            'North Rhine-Westphalia': ['North Rhine-Westphalia', 'Cologne', 'Düsseldorf']
        },
        'Japan': {
            'Tokyo': ['Tokyo'],
            'Osaka': ['Osaka'],
            'Hokkaido': ['Hokkaido', 'Sapporo']
        },
        'Australia': {
            'New South Wales': ['New South Wales', 'Sydney'],
            'Victoria': ['Victoria', 'Melbourne'],
            'Queensland': ['Queensland', 'Brisbane']
        },
        'Canada': {
            'Ontario': ['Ontario', 'Toronto'],
            'Quebec': ['Quebec', 'Montreal'],
            'British Columbia': ['British Columbia', 'Vancouver']
        },
        'Brazil': {
            'São Paulo': ['São Paulo', 'Sao Paulo'],
            'Rio de Janeiro': ['Rio de Janeiro']
        },
        'Mexico': {
            'Mexico City': ['Mexico City', 'Ciudad de México'],
            'Jalisco': ['Jalisco', 'Guadalajara']
        },
        'Italy': {'Lazio': ['Lazio', 'Rome'], 'Lombardy': ['Lombardy', 'Milan']},
        'Spain': {'Community of Madrid': ['Madrid'], 'Catalonia': ['Barcelona']},
        'South Africa': {'Gauteng': ['Gauteng', 'Johannesburg'], 'Western Cape': ['Cape Town']},
        'Argentina': {'Buenos Aires': ['Buenos Aires']},
        'South Korea': {'Seoul': ['Seoul'], 'Busan': ['Busan']},
        'Indonesia': {'Jakarta': ['Jakarta'], 'Java': ['Java', 'Surabaya']},
        'Turkey': {'Istanbul': ['Istanbul'], 'Ankara': ['Ankara']},
        'Saudi Arabia': {'Riyadh Province': ['Riyadh'], 'Mecca': ['Mecca']},
        'Iran': {'Tehran Province': ['Tehran']},
        'Iraq': {'Baghdad': ['Baghdad']},
        'Israel': {'Tel Aviv': ['Tel Aviv'], 'Jerusalem': ['Jerusalem']},
        'Palestine': {'Gaza': ['Gaza'], 'West Bank': ['West Bank', 'Ramallah']},
        'Egypt': {'Cairo Governorate': ['Cairo']},
        'Nigeria': {'Lagos State': ['Lagos'], 'Federal Capital Territory': ['Abuja']},
        'Pakistan': {'Punjab': ['Punjab', 'Lahore'], 'Sindh': ['Sindh', 'Karachi']},
        'Bangladesh': {'Dhaka Division': ['Dhaka']},
        'Vietnam': {'Hanoi': ['Hanoi'], 'Ho Chi Minh City': ['Ho Chi Minh City']},
        'Thailand': {'Bangkok': ['Bangkok']},
        'Philippines': {'Metro Manila': ['Manila', 'Metro Manila']},
        'Malaysia': {'Kuala Lumpur': ['Kuala Lumpur']},
        'Singapore': {'Singapore': ['Singapore']},
        'New Zealand': {'Auckland': ['Auckland'], 'Wellington': ['Wellington']},
        'Ukraine': {'Kyiv': ['Kyiv'], 'Lviv': ['Lviv']},
        'Poland': {'Masovian': ['Warsaw']},
        'Netherlands': {'North Holland': ['Amsterdam']},
        'Belgium': {'Brussels-Capital Region': ['Brussels']},
        'Sweden': {'Stockholm County': ['Stockholm']},
        'Norway': {'Oslo': ['Oslo']},
        'Denmark': {'Capital Region': ['Copenhagen']},
        'Finland': {'Uusimaa': ['Helsinki']},
        'Switzerland': {'Zurich': ['Zurich']},
        'Austria': {'Vienna': ['Vienna']},
        'Greece': {'Attica': ['Athens']},
        'Portugal': {'Lisbon': ['Lisbon']},
        'Ireland': {'Leinster': ['Dublin']},
        'Czech Republic': {'Prague': ['Prague']}
    }

    # Source categorization mapping
    SOURCE_CATEGORY_MAP = {

    # ================= PUBLIC (Mass Readership) =================
    # --- Indian ---
    "the times of india": "public",
    "timesofindia.indiatimes.com": "public",
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
    "scroll": "public",
    "scroll.in": "public",
    "the wire": "public",
    "thewire.in": "public",
    "the quint": "public",
    "thequint.com": "public",

    # --- Global Major ---
    "cnn": "public",
    "cnn.com": "public",
    "bbc": "public",
    "bbc.com": "public",
    "bbc.co.uk": "public",
    "bbc news": "public",
    "al jazeera": "public",
    "al jazeera english": "public",
    "aljazeera.com": "public",
    "guardian": "public",
    "theguardian.com": "public",
    "new york times": "public",
    "nytimes.com": "public",
    "new york post": "public",
    "washington post": "public",
    "washingtonpost.com": "public",
    "abc news": "public",
    "abcnews.go.com": "public",
    "cbs news": "public",
    "cbsnews.com": "public",
    "nbc news": "public",
    "nbcnews.com": "public",
    "usa today": "public",
    "usatoday.com": "public",
    "time": "public",
    "time.com": "public",
    "newsweek": "public",
    "newsweek.com": "public",
    "axios": "public",
    "axios.com": "public",
    "cbc news": "public",
    "cbc.ca": "public",
    "rte": "public",
    "rte.ie": "public",
    "independent": "public",
    "independent.co.uk": "public",
    "independent.ie": "public",
    "the-independent.com": "public",
    "the globe and mail": "public",
    "theglobeandmail.com": "public",
    "the irish times": "public",
    "irishtimes.com": "public",
    "the jerusalem post": "public",
    "jpost.com": "public",
    "news24": "public",
    "news24.com": "public",
    "la nacion": "public",
    "lanacion.com.ar": "public",
    "le monde": "public",
    "lemonde.fr": "public",
    "spiegel": "public",
    "spiegel.de": "public",

    # --- Other Public Sources ---
    "themarginalian.org": "public",
    "football italia": "public",
    "nbcsportsbayarea.com": "public",
    "yahoo entertainment": "public",
    "indiancatholicmatters.org": "public",
    "bgr": "public",
    "salon": "public",
    "cna": "public",
    "toynewsi.com": "public",
    "twistedsifter.com": "public",
    "slashdot.org": "public",
    "infoq.com": "public",
    "deadline": "public",
    "lithub.com": "public",
    "javacodegeeks.com": "public",
    "hitc": "public",
    "foot-africa.com": "public",
    "people": "public",
    "wired": "public",
    "dawgs by nature": "public",
    "variety": "public",
    "the big lead": "public",
    "yle news": "public",
    "techradar": "public",
    "kuriositas.com": "public",
    "inside the magic": "public",
    "cgpersia.com": "public",
    "tom's hardware uk": "public",
    "android central": "public",
    "rediff.com": "public",
    "4029tv": "public",
    "rlsbb.to": "public",
    "securityaffairs.com": "public",
    "covers.com": "public",

    # ================= NEUTRAL (Wire / Business Heavy) =================
    "reuters": "neutral",
    "reuters.com": "neutral",
    "associated press": "neutral",
    "apnews.com": "neutral",
    "ap.org": "neutral",
    "bloomberg": "neutral",
    "bloomberg.com": "neutral",
    "afp": "neutral",
    "livemint": "neutral",
    "livemint.com": "neutral",
    "business standard": "neutral",
    "business-standard.com": "neutral",
    "businessline": "neutral",
    "business insider": "neutral",
    "moneycontrol": "neutral",
    "moneycontrol.com": "neutral",
    "economic times": "neutral",
    "economictimes.indiatimes.com": "neutral",
    "financial post": "neutral",
    "financialpost.com": "neutral",
    "fortune": "neutral",
    "fortune.com": "neutral",
    "handelsblatt": "neutral",
    "handelsblatt.com": "neutral",
    "les echos": "neutral",
    "lesechos.fr": "neutral",
    "il sole 24 ore": "neutral",
    "ilsole24ore.com": "neutral",
    "wirtschafts woche": "neutral",
    "national post": "neutral",
    "globenewswire": "neutral",

    # ================= POLITICAL / OFFICIAL =================
    "pib": "political",
    "pib.gov.in": "political",
    "dd news": "political",
    "doordarshan": "political",
    "newsonair": "political",
    "all india radio": "political",
    "politico": "political",
    "politico.com": "political",
    "the hill": "political",
    "thehill.com": "political",
    "national review": "political",
    "breitbart": "political",
    "breitbart.com": "political",
    "rt": "political",
    "russian.rt.com": "political",
    "rbc": "political",
    "rbc.ru": "political",
    "freerepublic.com": "political",
    "sputnikglobe.com": "political",
    "the federalist": "political"
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

        text = f"{article.get('title','')} {article.get('description','')}".lower()

        # ------------------------------------------------------------
        # Override Anchors (High Confidence)
        # ------------------------------------------------------------

        OVERRIDES = {
            "Environment": ["earthquake", "hurricane", "cyclone"],
            "Sports": ["world cup", "olympics", "championship final"],
            "Business": ["ipo", "earnings report", "quarterly results"],
            "Technology": ["ransomware attack", "major data breach"],
            "Infrastructure": ["plane crash", "train derailment"],
            "Law": ["supreme court ruling"],
            "Politics": ["presidential election results"],
        }

        for category, phrases in OVERRIDES.items():
            for phrase in phrases:
                if re.search(rf"\b{re.escape(phrase)}\b", text):
                    return category

        # ------------------------------------------------------------
        # Keyword Dictionary (Balanced & Clean)
        # ------------------------------------------------------------

        CATEGORY_KEYWORDS = {

    "Crime": [
        "murder", "homicide", "rape", "robbery",
        "fraud", "shooting", "stabbing",
        "arrest", "suspect", "charged",
        "indictment", "kidnapping",
        "extortion", "smuggling",
        "drug trafficking", "gang violence",
        "firearm", "criminal network"
    ],

    "Politics": [
        "election", "parliament", "president",
        "prime minister", "government",
        "minister", "policy", "campaign",
        "legislation", "senate",
        "congress", "cabinet",
        "coalition", "voter turnout",
        "referendum", "ballot",
        "political party", "governance"
    ],

    "International": [
        "war", "conflict", "sanctions",
        "military", "troops", "border",
        "ceasefire", "diplomatic",
        "embassy", "foreign relations",
        "peace talks", "missile",
        "alliance", "defense pact"
    ],

    "Business": [
        "ipo", "earnings", "quarterly results",
        "stocks", "stock market",
        "share price", "investors",
        "merger", "acquisition",
        "investment", "revenue",
        "profit", "loss",
        "layoffs", "corporate",
        "inflation", "economic growth",
        "gdp", "bankruptcy"
    ],

    "Technology": [
        "artificial intelligence", "machine learning",
        "cybersecurity", "ransomware",
        "data breach", "malware",
        "hacking", "semiconductor",
        "startup", "software",
        "tech company", "cloud computing",
        "blockchain", "robotics",
        "satellite", "space mission",
        "nasa", "chip manufacturing"
    ],

    "Environment": [
        "earthquake", "flood", "wildfire",
        "hurricane", "cyclone", "drought",
        "climate change", "global warming",
        "carbon emissions", "pollution",
        "deforestation", "heatwave",
        "monsoon", "environmental policy",
        "sustainability", "renewable energy"
    ],

    "Health": [
        "virus", "vaccine", "pandemic",
        "epidemic", "outbreak",
        "hospital", "medical",
        "health ministry",
        "infection", "disease",
        "treatment", "clinical trial",
        "public health", "mental health"
    ],

    "Sports": [
        "match", "tournament", "league",
        "championship", "final",
        "semi-final", "world cup",
        "olympics", "goal",
        "athlete", "coach",
        "cricket", "football",
        "soccer", "tennis",
        "basketball", "nba",
        "nfl", "ipl"
    ],

    "Entertainment": [
        "movie", "film", "box office",
        "celebrity", "concert",
        "album release", "actor",
        "actress", "award ceremony",
        "music festival", "streaming platform",
        "hollywood", "bollywood"
    ],

    "Infrastructure": [
        "plane crash", "aircraft accident",
        "train derailment",
        "bridge collapse",
        "building collapse",
        "industrial explosion",
        "factory blast",
        "road accident",
        "metro disruption",
        "construction failure"
    ],

    "Law": [
        "court ruling", "supreme court",
        "legal appeal", "sentencing",
        "judicial review", "trial",
        "lawsuit", "verdict",
        "bail hearing", "constitutional challenge"
    ],

    "Education": [
        "university", "school",
        "curriculum", "exam",
        "board results",
        "education policy",
        "student protest",
        "academic year",
        "scholarship"
    ],

    "Energy": [
        "oil prices", "gas prices",
        "energy crisis", "opec",
        "power grid", "nuclear energy",
        "solar power", "wind energy",
        "fuel supply", "electricity outage",
        "refinery"
    ],

    "Social Issues": [
        "protest", "demonstration",
        "civil unrest", "human rights",
        "gender equality", "racism",
        "discrimination", "labor strike",
        "activist", "social justice"
    ]
}

        # ------------------------------------------------------------
        # Count Unique Keyword Matches Per Category
        # ------------------------------------------------------------

        category_counts = defaultdict(int)

        for category, keywords in CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if re.search(rf"\b{re.escape(keyword)}\b", text):
                    category_counts[category] += 1

        if not category_counts:
            return "General"

        # ------------------------------------------------------------
        # Determine Winner
        # ------------------------------------------------------------

        sorted_categories = sorted(
            category_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        top_category, top_count = sorted_categories[0]

        # Minimum threshold: at least 2 keyword matches
        if top_count < 2:
            return "General"

        # Tie handling (difference <= 1)
        if len(sorted_categories) > 1:
            second_category, second_count = sorted_categories[1]

            if abs(top_count - second_count) <= 1:
                return "General"

        return top_category


    def _extract_location(self, article):
        """
        Extract location: Priority = State > Country > Global
        Returns format: "State, Country" or "Country"
        """
        text = f"{article.get('title', '')} {article.get('description', '')}"
        
        detected_country = None
        detected_state = None
        
        # Step 1: Check states for any country in the combined STATES mapping
        for country_name, states_map in self.STATES.items():
            for state_name, variants in states_map.items():
                for variant in variants:
                    if re.search(rf"\b{re.escape(variant)}\b", text, re.IGNORECASE):
                        return f"{state_name}, {country_name}"

        # Step 2: Check Countries (if no state found)
        for country_name, variants in self.COUNTRIES.items():
            for variant in variants:
                if re.search(rf"\b{re.escape(variant)}\b", text, re.IGNORECASE):
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