"""
News model.
"""
from app.extensions import db


class News(db.Model):
    """News article model."""
    
    __tablename__ = 'news'
    
    news_id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('sources.source_id', ondelete='SET NULL'))
    title = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text)
    content = db.Column(db.Text)
    location = db.Column(db.String(100))  # Now stores CITY, not area
    incident_type = db.Column(db.String(50))
    published_date = db.Column(db.Date)
    image_url = db.Column(db.String(1000))  # Store image URL
    url = db.Column(db.Text, unique=True)  # ⭐ NEW: Article URL
    group_id = db.Column(db.Integer, nullable=True)  # Add this line
    
    # Relationships
    source = db.relationship('Source', backref='news')
    
    def __repr__(self):
        return f'<News {self.title[:50]}>'
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'news_id': self.news_id,
            'title': self.title,
            'summary': self.summary,
            'location': self.location,
            'incident_type': self.incident_type,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'source': self.source.source_name if self.source else None,
            'image_url': self.image_url,    
            'url': self.url,  # ⭐ NEW
            'group_id': self.group_id  # Add this line
        }