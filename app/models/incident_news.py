"""
IncidentNews model (Many-to-Many relationship).
"""
from datetime import datetime
from app.extensions import db


class IncidentNews(db.Model):
    """Junction table linking incidents and news articles."""
    
    __tablename__ = 'incident_news'
    
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.incident_id', ondelete='CASCADE'), primary_key=True)
    news_id = db.Column(db.Integer, db.ForeignKey('news.news_id', ondelete='CASCADE'), primary_key=True)
    reported_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<IncidentNews incident={self.incident_id} news={self.news_id}>'