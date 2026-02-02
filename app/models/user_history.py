"""
User History model.
"""
from datetime import datetime
from app.extensions import db


class UserHistory(db.Model):
    """User viewing history."""
    
    __tablename__ = 'user_history'
    
    history_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'))
    news_id = db.Column(db.Integer, db.ForeignKey('news.news_id', ondelete='CASCADE'))
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    news = db.relationship('News', backref='history')
    
    def __repr__(self):
        return f'<UserHistory user:{self.user_id} news:{self.news_id}>'