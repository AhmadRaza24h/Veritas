"""
Entry point for the Veritas Flask application.
"""
from app import create_app
from app.extensions import db

app = create_app()

@app.shell_context_processor
def make_shell_context():
    """Make database instance available in Flask shell."""
    from app.models import User, Source, News, Incident, IncidentNews, UserHistory, AnalysisCache
    return {
        'db': db,
        'User': User,
        'Source': Source,
        'News': News,
        'Incident': Incident,
        'IncidentNews': IncidentNews,
        'UserHistory': UserHistory,
        'AnalysisCache': AnalysisCache
    }

if __name__ == '__main__':
    app.run()
