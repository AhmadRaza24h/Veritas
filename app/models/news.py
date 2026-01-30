"""
News model.
"""
from app.extensions import db


class News(db.Model):
    """News model for storing news articles."""
    
    __tablename__ = 'news'
    
    news_id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('sources.source_id', ondelete='SET NULL'))
    title = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text)
    content = db.Column(db.Text)
    location = db.Column(db.String(100))
    incident_type = db.Column(db.String(50))
    published_date = db.Column(db.Date)
    
    # Relationships
    incidents = db.relationship('IncidentNews', backref='news_article', lazy='dynamic', cascade='all, delete-orphan')
    history = db.relationship('UserHistory', backref='news_article', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<News {self.title[:50]}>'
