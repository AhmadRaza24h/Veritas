"""
NewsAPI Ingestion Service for Gujarat State-Level News
Custom source categorization mapping
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
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://newsapi.org/v2/everything'
        self.stats = {
            'fetched': 0, 'filtered': 0, 'inserted': 0, 'duplicates': 0,
            'incidents_created': 0, 'incidents_updated': 0,
            'by_category': {'public': 0, 'neutral': 0, 'political': 0},
            'by_incident': {}
        }
    
    def _get_source_category(self, source_obj):
        """
        Smart source categorization with normalization
        """
        raw_id = (source_obj.get('id') or '').lower()
        raw_name = (source_obj.get('name') or '').lower()

        # Normalize (remove special chars, extra spaces)
        name = re.sub(r'[^a-z0-9 ]', '', raw_name)
        name = re.sub(r'\s+', ' ', name).strip()

        # STRONG RULES
        PUBLIC_SOURCES = [
            'times of india', 'indian express', 'hindustan times',
            'ndtv', 'news18', 'the hindu', 'ahmedabad mirror',
            'divya bhaskar', 'gujarat samachar', 'sandesh',
            'the wire', 'scroll', 'newslaundry', 'the quint',
            'alt news', 'caravan', 'the print', 'rediff',
            'statetimes'
        ]

        POLITICAL_SOURCES = [
            'pib', 'press information bureau', 'doordarshan',
            'dd news', 'sansad tv', 'all india radio'
        ]

        NEUTRAL_SOURCES = [
            'reuters', 'bloomberg', 'bbc', 'cnbc', 'business standard',
            'economic times', 'moneycontrol', 'livemint', 'businessline',
            'globalsecurity', 'globenewswire', 'oilprice', 'nature',
            'insurance journal', 'yahoo'
        ]

        # Match by NAME
        for s in PUBLIC_SOURCES:
            if s in name:
                return 'public'

        for s in POLITICAL_SOURCES:
            if s in name:
                return 'political'

        for s in NEUTRAL_SOURCES:
            if s in name:
                return 'neutral'

        # Keyword fallback
        if 'gov' in name or 'government' in name:
            return 'political'

        return 'neutral'
    
    def fetch_gujarat_news(self, days=7, page_size=100, max_pages=2):
        """Fetch Gujarat news"""
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
                    print(f"   ⚠️  Error {response.status_code}")
                    break
            except Exception as e:
                print(f"   ❌ {e}")
                break
        
        self.stats['fetched'] = len(all_articles)
        print(f"✅ Total: {len(all_articles)}")
        return all_articles
    
    def _is_valid_article(self, article):
        """Quality check"""
        title = article.get('title', '')
        desc = article.get('description', '')
        
        if not title or not desc or len(title) < 10:
            return False
        
        combined = f"{title} {desc} {article.get('content', '')}".lower()
        if any(x in combined for x in ['[removed]', '[deleted]', 'subscribe to']):
            return False
        
        return True
    
    def _extract_location(self, article):
        """Extract location"""
        combined = f"{article.get('title', '')} {article.get('description', '')} {article.get('content', '')}".lower()
        combined_clean = re.sub(r'[^\w\s]', ' ', combined)
        
        for city in self.GUJARAT_CITIES:
            pattern = rf'\b{city.lower()}(based|\'s| district)?\b'
            if re.search(pattern, combined_clean):  
                return f"{city}, Gujarat"
        
        if 'gujarat' in combined_clean:
            return 'Gujarat'
        
        return None
    
    def _extract_incident_type(self, article):
        """Extract incident type with priority rules"""
        combined = f"{article.get('title', '')} {article.get('description', '')} {article.get('content', '')}".lower()

        INCIDENT_RULES = [
            # High priority (hard incidents)
            ('Crime', [
                'murder', 'arrest', 'rape', 'robbery', 'theft',
                'police', 'fir', 'custody', 'crime', 'assault'
            ]),
            ('Fire', [
                'fire', 'blaze', 'explosion', 'short circuit', 'burnt'
            ]),
            ('Accident', [
                'accident', 'collision', 'crash', 'hit', 'killed',
                'injured', 'road mishap'
            ]),
            ('Weather', [
                'flood', 'rain', 'cyclone', 'storm', 'heatwave',
                'monsoon', 'weather alert'
            ]),
            
            # Infrastructure
            ('Infrastructure', [
                'metro', 'bridge', 'highway', 'road', 'flyover',
                'construction', 'project', 'pipeline'
            ]),
            
            # Business (expanded)
            ('Business', [
                'investment', 'invest', 'funding', 'startup',
                'company', 'firm', 'industry', 'industrial',
                'plant', 'factory', 'manufacturing',
                'economy', 'economic', 'market', 'stock',
                'revenue', 'profit', 'loss', 'crore'
            ]),
            
            # Health
            ('Health', [
                'hospital', 'covid', 'health', 'vaccine',
                'medical', 'doctor', 'disease', 'infection'
            ]),
            
            # Education
            ('Education', [
                'exam', 'university', 'college', 'school',
                'student', 'neet', 'jee', 'board exam'
            ]),
            
            # Politics (lower priority)
            ('Politics', [
                'election', 'minister', 'bjp', 'congress',
                'government', 'policy', 'cabinet', 'cm', 'pm'
            ]),
            
            # Sports
            ('Sports', [
                'cricket', 'ipl', 'match', 'tournament', 'sports'
            ]),
        ]

        for incident, keywords in INCIDENT_RULES:
            if any(kw in combined for kw in keywords):
                return incident

        return 'General'
    
    def _process_articles(self, articles):
        """Process articles"""
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
            print(f"   ✅ {incident_type:15s} {location:20s} {article['title'][:50]}...")       
            processed.append(article)
        
        self.stats['filtered'] = len(processed)
        print(f"✅ Valid: {len(processed)}")
        return processed
    
    def _save_to_database(self, articles):
        """Save articles with smart categorization"""
        print(f"\n💾 Saving {len(articles)} articles...")
        
        saved_news_ids = []
        
        for article in articles:
            try:
                url = article.get('url', '').strip()
                if not url:
                    continue
                
                # Check duplicate
                if News.query.filter_by(url=url).first():
                    self.stats['duplicates'] += 1
                    continue
                
                source_obj = article.get('source', {})
                source_name = source_obj.get('name', 'Unknown')
                
                # Get or create source
                source = Source.query.filter_by(source_name=source_name).first()
                category = self._get_source_category(source_obj)
                
                if not source:
                    # Create new
                    source = Source(source_name=source_name, category=category)
                    db.session.add(source)
                    db.session.flush()
                else:
                    # Update if needed
                    if source.category != category:
                        source.category = category
                        db.session.flush()
                
                self.stats['by_category'][category] += 1
                
                icon = {'public': '🟢', 'neutral': '🔵', 'political': '🟡'}[category]
                print(f"   {icon} {source_name} → {category.upper()}")
                
                # Parse date
                published_at = article.get('publishedAt')
                try:
                    pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00')).date()
                except:
                    pub_date = datetime.now().date()
                
                # Create news
                news = News(
                    source_id=source.source_id,
                    title=article.get('title', '')[:500],
                    summary=article.get('description', ''),
                    content=article.get('content', ''),
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
                print(f"   ❌ Error: {str(e)[:80]}")
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
            # Check existing
            existing = Incident.query.filter_by(incident_type=itype, location=loc).first()
            
            if existing:
                # Link to existing
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
                
                # Update dates
                dates = [n.published_date for n in articles if n.published_date]
                if dates:
                    if min(dates) < existing.first_reported:
                        existing.first_reported = min(dates)
                    if max(dates) > existing.last_reported:
                        existing.last_reported = max(dates)
                
                self.stats['incidents_updated'] += 1
            else:
                # Create new
                dates = [n.published_date for n in articles if n.published_date]
                incident = Incident(
                    incident_type=itype,
                    location=loc,
                    first_reported=min(dates) if dates else datetime.now().date(),
                    last_reported=max(dates) if dates else datetime.now().date()
                )
                db.session.add(incident)
                db.session.flush()
                
                # Link articles
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
                count = self.stats['by_category'][cat]
                pct = (count / total * 100)
                icon = {'public': '🟢', 'neutral': '🔵', 'political': '🟡'}[cat]
                print(f"   {icon} {cat.upper():10s} {count:3d} ({pct:5.1f}%)")
        
        print(f"\n📋 By Incident Type:")
        for itype, count in sorted(self.stats['by_incident'].items(), key=lambda x: x[1], reverse=True):
            print(f"   {itype:15s} {count}")
        print("=" * 70)