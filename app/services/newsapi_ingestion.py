"""
NewsAPI ingestion service - Ahmedabad Local News ONLY.
Optimized for quality and accuracy.
"""
import requests
from datetime import datetime, timedelta
from app.models import News, Source
from app.extensions import db
import logging
import os
import re

logger = logging.getLogger(__name__)


class NewsAPIIngestionService:
    """Service to fetch ONLY Ahmedabad news from NewsAPI."""
    
    def __init__(self):
        self.api_key = os.environ.get('NEWSAPI_KEY')
        self.base_url = 'https://newsapi.org/v2/everything'
        
        if not self.api_key:
            logger.warning("⚠️  NEWSAPI_KEY not found in environment variables")
    
    def fetch_ahmedabad_news(self, page_size=30, days=29):
        """
        Fetch Ahmedabad-specific news from NewsAPI.
        
        Args:
            page_size: Number of articles per request (default: 30)
            days: Number of days to look back (default: 7)
        
        Returns:
            int: Number of articles stored
        """
        if not self.api_key:
            logger.error("❌ Cannot fetch: NEWSAPI_KEY not configured")
            return 0
        
        try:
            # Calculate date range
            to_date = datetime.utcnow()
            from_date = to_date - timedelta(days=days)
            
            # STRICT Ahmedabad query
            params = {
                'q': 'Ahmedabad',  # Only Ahmedabad
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d'),
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': page_size,  # Configurable
                'apiKey': self.api_key
            }
            
            logger.info(f"📡 Fetching Ahmedabad news from NewsAPI (pageSize={page_size})...")
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'ok':
                articles = data['articles']
                total_results = data.get('totalResults', 0)
                
                logger.info(f"  📊 Total available: {total_results}")
                logger.info(f"  📥 Received: {len(articles)} articles")
                
                count = self._process_articles(articles)
                
                logger.info(f"  ✅ Stored: {count} Ahmedabad articles")
                
                return count
            else:
                error_msg = data.get('message', 'Unknown error')
                logger.error(f"❌ NewsAPI Error: {error_msg}")
                return 0
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request failed: {e}")
            return 0
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return 0
    
    def _process_articles(self, articles):
        """Process and store articles with strict Ahmedabad filtering."""
        stored_count = 0
        skipped_duplicate = 0
        skipped_location = 0
        
        for article in articles:
            try:
                # Skip removed/deleted articles
                if not article.get('title') or article['title'] == '[Removed]':
                    continue
                
                # Check if duplicate (by title)
                if News.query.filter_by(title=article['title']).first():
                    skipped_duplicate += 1
                    continue
                
                # STRICT location check
                text_to_check = ' '.join([
                    article.get('title', ''),
                    article.get('description', ''),
                    article.get('content', '')
                ])
                
                location = self._extract_ahmedabad_location(text_to_check)
                
                if not location:
                    skipped_location += 1
                    continue  # Skip non-Ahmedabad news
                
                # Get or create source
                source_name = article['source']['name']
                source = Source.query.filter_by(source_name=source_name).first()
                
                if not source:
                    category = self._categorize_source(source_name)
                    source = Source(source_name=source_name, category=category)
                    db.session.add(source)
                    db.session.flush()
                
                # Categorize incident type
                incident_type = self._categorize_incident(
                    article.get('title', ''),
                    article.get('description', '')
                )
                
                # Parse published date
                try:
                    published_date = datetime.strptime(
                        article['publishedAt'][:10], '%Y-%m-%d'
                    ).date()
                except:
                    published_date = datetime.utcnow().date()
                
                # Get image URL (NewsAPI provides this!)
                image_url = article.get('urlToImage')
                
                # Validate image URL
                if image_url:
                    # Remove query parameters that might cause issues
                    image_url = image_url.split('?')[0] if '?' in image_url else image_url
                    # Basic validation
                    if not image_url.startswith('http'):
                        image_url = None
                
                # Create news entry
                news = News(
                    source_id=source.source_id,
                    title=article['title'][:500],
                    summary=article.get('description', '')[:500] if article.get('description') else None,
                    content=article.get('content', article.get('description', ''))[:2000],
                    location=location,
                    incident_type=incident_type,
                    published_date=published_date,
                    image_url=image_url
                )
                
                db.session.add(news)
                stored_count += 1
                
            except Exception as e:
                logger.error(f"❌ Error processing article: {e}")
                continue
        
        # Commit all at once
        try:
            db.session.commit()
            
            # Log statistics
            logger.info(f"  📊 Skipped duplicates: {skipped_duplicate}")
            logger.info(f"  📊 Skipped non-Ahmedabad: {skipped_location}")
            
        except Exception as e:
            logger.error(f"❌ Database commit failed: {e}")
            db.session.rollback()
            return 0
        
        return stored_count
    
    def _extract_ahmedabad_location(self, text):
        """
        SMART Ahmedabad location extraction.
        More lenient but still accurate.
        """
        text_lower = text.lower()
        text_clean = re.sub(r'[^\w\s]', ' ', text_lower)
    
        # PRIORITY 1: Direct Ahmedabad mention
        ahmedabad_keywords = ['ahmedabad', 'amdavad', 'ahmadabad', 'ahmdabad']
        has_ahmedabad = any(kw in text_clean for kw in ahmedabad_keywords)
    
        if has_ahmedabad:
            # Check for specific areas
            ahmedabad_areas = [
                'maninagar', 'vastrapur', 'sg highway', 'paldi', 'satellite',
                'navrangpura', 'bodakdev', 'cg road', 'ashram road', 'law garden',
                'gota', 'kalupur', 'nehru bridge', 'ellis bridge', 'thaltej',
                'bopal', 'chandkheda', 'sabarmati', 'iscon', 'prahlad nagar',
                'motera', 'science city', 'riverfront', 'kankaria', 'naroda',
                'vastral', 'nikol', 'odhav', 'narol', 'sarkhej', 'shahibaug'
            ]
        
            for area in ahmedabad_areas:
                if area in text_clean:
                    return f"{area.title()}, Ahmedabad"
        
            return 'Ahmedabad, Gujarat'
    
        # PRIORITY 2: Gandhinagar (state capital, close to Ahmedabad)
        if 'gandhinagar' in text_clean:
            return 'Gandhinagar, Gujarat'
    
        # PRIORITY 3: Gujarat WITH Ahmedabad metro cities
        gujarat_cities_near_ahmedabad = {
            'sanand': 'Sanand, Ahmedabad District',
            'bavla': 'Bavla, Ahmedabad District',
            'dholka': 'Dholka, Ahmedabad District',
            'viramgam': 'Viramgam, Ahmedabad District',
        }
    
        for city, location in gujarat_cities_near_ahmedabad.items():
            if city in text_clean:
                return location
    
        # PRIORITY 4: Gujarat state news (broader but still relevant)
        if 'gujarat' in text_clean:
            # Accept if it's clearly Gujarat state news
            # This will capture: "Gujarat government", "Gujarat CM", etc.
            return 'Gujarat'
    
        # PRIORITY 5: IIT Gandhinagar, PDPU, etc (educational institutions)
        educational_keywords = [
            'iit gandhinagar', 'pdpu', 'nid ahmedabad', 'cept', 
            'ld engineering', 'nirma university'
        ]
    
        for keyword in educational_keywords:
            if keyword in text_clean:
                return 'Ahmedabad, Gujarat'
    
        return None  # Only reject if clearly NOT Gujarat/Ahmedabad
    
    def _categorize_source(self, source_name):
        """Categorize news source."""
        source_lower = source_name.lower()
        
        # Political sources
        if any(word in source_lower for word in ['government', 'ministry', 'official', 'pib']):
            return 'political'
        
        # Public/citizen sources
        if any(word in source_lower for word in ['citizen', 'public', 'blog', 'medium']):
            return 'public'
        
        # Default: neutral (news media)
        return 'neutral'
    
    def _categorize_incident(self, title, description):
        """Categorize incident type based on keywords."""
        text = ((title or '') + ' ' + (description or '')).lower()
        
        categories = {
            'Accident': ['accident', 'collision', 'crash', 'hit', 'injured', 'mishap', 'fatal', 'died'],
            'Crime': ['robbery', 'theft', 'murder', 'assault', 'crime', 'arrest', 'police', 'fir', 'rape', 'kidnap', 'fraud', 'scam'],
            'Weather': ['rain', 'flood', 'storm', 'weather', 'waterlogging', 'cyclone', 'thunder', 'heatwave', 'drought'],
            'Infrastructure': ['metro', 'road', 'bridge', 'construction', 'development', 'project', 'airport', 'railway', 'brts'],
            'Politics': ['election', 'minister', 'government', 'policy', 'party', 'cm', 'pm', 'mla', 'mp', 'parliament', 'bjp', 'congress', 'aap'],
            'Event': ['festival', 'celebration', 'event', 'concert', 'gathering', 'function', 'ceremony', 'navratri', 'diwali', 'uttarayan'],
            'Traffic': ['traffic', 'jam', 'congestion', 'vehicle', 'highway', 'flyover', 'road block', 'diversion'],
            'Fire': ['fire', 'blaze', 'burn', 'flames', 'smoke'],
            'Health': ['hospital', 'health', 'medical', 'doctor', 'patient', 'covid', 'disease', 'vaccine', 'deaths', 'treatment'],
            'Education': ['school', 'college', 'university', 'education', 'student', 'exam', 'result', 'admission', 'iit', 'nit'],
            'Business': ['business', 'economy', 'market', 'stock', 'company', 'startup', 'investment', 'industry', 'trade'],
            'Sports': ['cricket', 'football', 'sports', 'match', 'game', 'player', 'team', 'tournament', 'stadium'],
        }
        
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'General'