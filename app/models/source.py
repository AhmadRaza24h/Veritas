"""
Source model.
"""
from app.extensions import db


class Source(db.Model):
    """Source model for news sources with categorization."""
    
    __tablename__ = 'sources'
    
    source_id = db.Column(db.Integer, primary_key=True)
    source_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(20), nullable=False)
    
    __table_args__ = (
        db.CheckConstraint(
            "category IN ('public', 'neutral', 'political')",
            name='check_source_category'
        ),
    )
    
    def __repr__(self):
        return f'<Source {self.source_name} ({self.category})>'