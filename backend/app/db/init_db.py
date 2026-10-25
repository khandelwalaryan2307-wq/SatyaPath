from ..core.database import engine
from ..models.base import Base

def init_db():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")

if __name__ == "__main__":
    init_db()
