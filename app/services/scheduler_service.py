"""
Background scheduler service - API-Only with smart rate limiting.
Automatically creates incidents when fetching news.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from app.extensions import db
from app.models import News
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SchedulerService:
    """Scheduler with optimized NewsAPI usage (100 requests/day limit)."""
    
    def __init__(self, app=None):
        self.scheduler = BackgroundScheduler()
        self.app = app
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize scheduler with Flask app."""
        self.app = app
        
        # Configure scheduler
        self.scheduler.configure(
            timezone='Asia/Kolkata',
            job_defaults={
                'coalesce': False,
                'max_instances': 1
            }
        )
        
        # Add jobs
        self._add_jobs()
        
        # Start scheduler
        self.scheduler.start()
        logger.info("=" * 70)
        logger.info("✅ SMART SCHEDULER STARTED (API-ONLY + AUTO-INCIDENTS)")
        logger.info("=" * 70)
        
        # Shutdown on app close
        import atexit
        atexit.register(lambda: self.scheduler.shutdown())
    
    def _add_jobs(self):
        """Add optimized scheduled jobs."""
        
        # Job 1: Morning news fetch (9 AM) - 30 articles
        self.scheduler.add_job(
            func=self._fetch_morning_news,
            trigger=CronTrigger(hour=9, minute=0),
            id='fetch_morning',
            name='Morning News Fetch',
            replace_existing=True
        )
        logger.info("📅 Scheduled: Morning fetch at 9:00 AM (30 articles)")
        
        # Job 2: Afternoon news fetch (2 PM) - 30 articles
        self.scheduler.add_job(
            func=self._fetch_afternoon_news,
            trigger=CronTrigger(hour=14, minute=0),
            id='fetch_afternoon',
            name='Afternoon News Fetch',
            replace_existing=True
        )
        logger.info("📅 Scheduled: Afternoon fetch at 2:00 PM (30 articles)")
        
        # Job 3: Evening news fetch (8 PM) - 30 articles
        self.scheduler.add_job(
            func=self._fetch_evening_news,
            trigger=CronTrigger(hour=20, minute=0),
            id='fetch_evening',
            name='Evening News Fetch',
            replace_existing=True
        )
        logger.info("📅 Scheduled: Evening fetch at 8:00 PM (30 articles)")
        
        # Job 4: Cleanup old data (daily at 2 AM)
        self.scheduler.add_job(
            func=self._cleanup_old_data_job,
            trigger=CronTrigger(hour=2, minute=0),
            id='cleanup_old_data',
            name='Clean Old Data',
            replace_existing=True
        )
        logger.info("📅 Scheduled: Cleanup at 2:00 AM (60+ days old)")
        
        logger.info("=" * 70)
        logger.info("📊 DAILY API USAGE: 90 requests (10 buffer for testing)")
        logger.info("=" * 70)
    
    def _fetch_morning_news(self):
        """Morning news fetch job (9 AM)."""
        with self.app.app_context():
            try:
                logger.info("=" * 70)
                logger.info("🌅 MORNING NEWS FETCH STARTED")
                logger.info("=" * 70)
                
                # ✅ FIXED: Correct class name
                from app.services.newsapi_ingestion import NewsAPIIngestion
                
                api_key = os.getenv('NEWSAPI_KEY')
                if not api_key:
                    logger.error("❌ NEWSAPI_KEY not found!")
                    return
                
                service = NewsAPIIngestion(api_key)
                stats = service.run_ingestion(days=7, page_size=30, max_pages=1)
                
                logger.info(f"✅ Morning: {stats['inserted']} articles, {stats['incidents_created']} incidents")
                
            except Exception as e:
                logger.error(f"❌ Morning fetch error: {e}")
    
    def _fetch_afternoon_news(self):
        """Afternoon news fetch job (2 PM)."""
        with self.app.app_context():
            try:
                logger.info("=" * 70)
                logger.info("🌤️  AFTERNOON NEWS FETCH STARTED")
                logger.info("=" * 70)
                
                # ✅ FIXED: Correct class name
                from app.services.newsapi_ingestion import NewsAPIIngestion
                
                api_key = os.getenv('NEWSAPI_KEY')
                if not api_key:
                    logger.error("❌ NEWSAPI_KEY not found!")
                    return
                
                service = NewsAPIIngestion(api_key)
                stats = service.run_ingestion(days=7, page_size=30, max_pages=1)
                
                logger.info(f"✅ Afternoon: {stats['inserted']} articles, {stats['incidents_created']} incidents")
                
            except Exception as e:
                logger.error(f"❌ Afternoon fetch error: {e}")
    
    def _fetch_evening_news(self):
        """Evening news fetch job (8 PM)."""
        with self.app.app_context():
            try:
                logger.info("=" * 70)
                logger.info("🌆 EVENING NEWS FETCH STARTED")
                logger.info("=" * 70)
                
                # ✅ FIXED: Correct class name
                from app.services.newsapi_ingestion import NewsAPIIngestion
                
                api_key = os.getenv('NEWSAPI_KEY')
                if not api_key:
                    logger.error("❌ NEWSAPI_KEY not found!")
                    return
                
                service = NewsAPIIngestion(api_key)
                stats = service.run_ingestion(days=7, page_size=30, max_pages=1)
                
                logger.info(f"✅ Evening: {stats['inserted']} articles, {stats['incidents_created']} incidents")
                
            except Exception as e:
                logger.error(f"❌ Evening fetch error: {e}")
    
    def _cleanup_old_data_job(self):
        """Cleanup old news (>60 days)."""
        with self.app.app_context():
            try:
                logger.info("=" * 70)
                logger.info("🧹 CLEANUP JOB STARTED")
                logger.info("=" * 70)
                
                cutoff_date = datetime.utcnow().date() - timedelta(days=60)
                
                old_count = News.query.filter(
                    News.published_date < cutoff_date
                ).count()
                
                if old_count == 0:
                    logger.info("  ✅ No old data to clean")
                else:
                    deleted = News.query.filter(
                        News.published_date < cutoff_date
                    ).delete()
                    
                    db.session.commit()
                    logger.info(f"  ✅ Deleted {deleted} articles older than {cutoff_date}")
                
                logger.info("=" * 70)
                logger.info("✅ Cleanup completed")
                logger.info("=" * 70)
                
            except Exception as e:
                logger.error(f"❌ Cleanup error: {e}")
                db.session.rollback()
    
    def get_jobs(self):
        """Get list of all scheduled jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs


# Global scheduler instance
scheduler_service = SchedulerService()