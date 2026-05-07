"""Database connection and session management for Sportify backend."""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from model.model import Base

# Database connection config (kept directly in code per project preference)
# Note: square brackets are placeholders in docs and should not be included in real credentials.
DATABASE_URL = URL.create(
	"postgresql+psycopg2",
	username="postgres.pyahykjyflsxnzlzudep",
	password="QcFDM5kKBO2pE2Qn",
	host="aws-1-ap-northeast-1.pooler.supabase.com",
	port=6543,
	database="postgres",
)

# Create engine with SSL options for Supabase
engine = create_engine(
	DATABASE_URL,
	echo=False,
	future=True,
	pool_size=5,
	max_overflow=10,
	pool_pre_ping=True,
	pool_recycle=300,  # Recycle connections every 5 minutes
	pool_use_lifo=True,
	connect_args={
		"sslmode": "require",
		"connect_timeout": 10,
		"keepalives": 1,
		"keepalives_idle": 30,
		"keepalives_interval": 10,
		"keepalives_count": 5,
	},
)

# Create session factory
SessionLocal = sessionmaker(
	autocommit=False,
	autoflush=False,
	bind=engine
)


#db_session = scoped_session(SessionLocal)


def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)

def get_session() -> Session:
    """Get a raw, new database session (useful for background tasks/scripts)."""
    return SessionLocal()