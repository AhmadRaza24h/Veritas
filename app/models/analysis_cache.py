"""
Analysis Cache model.
"""
from datetime import datetime
from app.extensions import db


class AnalysisCache(db.Model):
    """Cache for analysis results."""
    
    __tablename__ = 'analysis_cache'
    
    analysis_id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.incident_id', ondelete='CASCADE'))
    credibility_score = db.Column(db.Integer)
    public_pct = db.Column(db.Integer)
    neutral_pct = db.Column(db.Integer)
    political_pct = db.Column(db.Integer)
    perspective_summary = db.Column(db.Text)
    generated_at =  db.Column(db.DateTime, default=datetime.now)
    
    __table_args__ = (
        db.CheckConstraint('credibility_score BETWEEN 0 AND 100', name='check_credibility'),
        db.CheckConstraint('public_pct BETWEEN 0 AND 100', name='check_public_pct'),
        db.CheckConstraint('neutral_pct BETWEEN 0 AND 100', name='check_neutral_pct'),
        db.CheckConstraint('political_pct BETWEEN 0 AND 100', name='check_political_pct'),
    )
    
    def __repr__(self):
        return f'<AnalysisCache incident:{self.incident_id}>'