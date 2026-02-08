#!/usr/bin/env python3
"""
Fetch Gujarat news - Complete automated solution
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.services.newsapi_ingestion import NewsAPIIngestion


def fetch_newsapi():
    """Fetch news and create incidents automatically"""
    print("=" * 60)
    print("📰 GUJARAT NEWS FETCHER (All-in-One)")
    print("=" * 60)
    
    api_key = os.getenv('NEWSAPI_KEY')
    
    if not api_key:
        print("\n❌ NEWSAPI_KEY not found!")
        sys.exit(1)
    
    app = create_app()
    
    with app.app_context():
        ingestion = NewsAPIIngestion(api_key)
        ingestion.run_ingestion(days=7, page_size=100, max_pages=2)
        ingestion.print_stats()


if __name__ == '__main__':
    fetch_newsapi()