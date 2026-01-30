"""
Incident model.
"""
from app.extensions import db


class Incident(db.Model):
    """Incident model for grouping related news articles."""
    
    __tablename__ = 'incidents'
    
    incident_id = db.Column(db.Integer, primary_key=True)
    incident_type = db.Column(db.String(50))
    location = db.Column(db.String(100))
    first_reported = db.Column(db.Date)
    last_reported = db.Column(db.Date)
    
    # Relationships
    news_links = db.relationship('IncidentNews', backref='incident', lazy='dynamic', cascade='all, delete-orphan')
    analysis = db.relationship('AnalysisCache', backref='incident', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Incident {self.incident_type} at {self.location}>'
