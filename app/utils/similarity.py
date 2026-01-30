"""
Similarity matching utility.

Similar Incident Detection:
- Match by location
- Match by category/incident_type
- Within ±30 days
"""
from datetime import timedelta
from app.models import Incident, IncidentNews, News
from app.extensions import db


def find_similar_incidents(incident, limit=5, days_range=30):
    """
    Find similar incidents based on location, type, and date.
    
    Args:
        incident: The incident to find similarities for
        limit: Maximum number of similar incidents to return
        days_range: Days range for date matching (±days_range)
        
    Returns:
        list: List of similar Incident objects
    """
    if not incident:
        return []
    
    # Get date range
    date_from = None
    date_to = None
    
    if incident.first_reported:
        date_from = incident.first_reported - timedelta(days=days_range)
        date_to = incident.last_reported or incident.first_reported
        date_to = date_to + timedelta(days=days_range)
    
    # Build query for similar incidents
    query = db.session.query(Incident).filter(
        Incident.incident_id != incident.incident_id
    )
    
    # Filter by location (if available)
    if incident.location:
        query = query.filter(
            Incident.location.ilike(f'%{incident.location}%')
        )
    
    # Filter by incident type (if available)
    if incident.incident_type:
        query = query.filter(
            Incident.incident_type == incident.incident_type
        )
    
    # Filter by date range (if available)
    if date_from and date_to:
        query = query.filter(
            db.or_(
                db.and_(
                    Incident.first_reported >= date_from,
                    Incident.first_reported <= date_to
                ),
                db.and_(
                    Incident.last_reported >= date_from,
                    Incident.last_reported <= date_to
                )
            )
        )
    
    # Get results
    similar_incidents = query.limit(limit).all()
    
    return similar_incidents
