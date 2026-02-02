"""
Incident model.
"""
from app.extensions import db


class Incident(db.Model):
    """Incident model - grouped news articles."""
    
    __tablename__ = 'incidents'
    
    incident_id = db.Column(db.Integer, primary_key=True)
    incident_type = db.Column(db.String(50))
    location = db.Column(db.String(100))
    first_reported = db.Column(db.Date)
    last_reported = db.Column(db.Date)
    
    def __repr__(self):
        return f'<Incident {self.incident_type} at {self.location}>'