#!/usr/bin/env python3
"""
Manually fetch news from NewsAPI.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.services.newsapi_ingestion import NewsAPIIngestionService


def fetch_newsapi():
    """Fetch news from NewsAPI."""
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print(" 📰 FETCHING NEWS FROM NEWSAPI")
        print("=" * 70)
        print()
        
        service = NewsAPIIngestionService()
        count = service.fetch_ahmedabad_news(page_size=100, days=29)
        
        print()
        print("=" * 70)
        print(f" ✅ SUCCESS: {count} ARTICLES STORED FROM NEWSAPI")
        print("=" * 70)


if __name__ == '__main__':
    fetch_newsapi()