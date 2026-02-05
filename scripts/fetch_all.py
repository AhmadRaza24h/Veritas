#!/usr/bin/env python3
"""
Fetch Ahmedabad news (API-Only).
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.services.newsapi_ingestion import NewsAPIIngestionService


def fetch_all():
    """Fetch news from NewsAPI only."""
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print(" 🚀 API-ONLY FETCH: AHMEDABAD LOCAL NEWS")
        print("=" * 70)
        print()
        
        service = NewsAPIIngestionService()
        count = service.fetch_ahmedabad_news(page_size=30, days=7)
        
        print()
        print("=" * 70)
        print(f" ✅ TOTAL STORED: {count} AHMEDABAD ARTICLES")
        print("=" * 70)


if __name__ == '__main__':
    fetch_all()