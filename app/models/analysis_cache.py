"""
AnalysisCache model.
"""
from datetime import datetime
from app.extensions import db


class AnalysisCache(db.Model):
    """Analysis cache model for storing precomputed analysis results."""
    
    __tablename__ = 'analysis_cache'
    
    analysis_id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.incident_id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # Credibility metrics
    credibility_score = db.Column(db.Integer)
    
    # Perspective metrics
    public_pct = db.Column(db.Integer)
    neutral_pct = db.Column(db.Integer)
    political_pct = db.Column(db.Integer)
    
    perspective_summary = db.Column(db.Text)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint('credibility_score >= 0 AND credibility_score <= 100', name='check_credibility_score'),
        db.CheckConstraint('public_pct >= 0 AND public_pct <= 100', name='check_public_pct'),
        db.CheckConstraint('neutral_pct >= 0 AND neutral_pct <= 100', name='check_neutral_pct'),
        db.CheckConstraint('political_pct >= 0 AND political_pct <= 100', name='check_political_pct'),
    )
    
    def __repr__(self):
        return f'<AnalysisCache incident={self.incident_id} score={self.credibility_score}>'
