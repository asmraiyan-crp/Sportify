"""Database connection and session management for Sportify backend."""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, Session
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

# Create engine
engine = create_engine(
	DATABASE_URL,
	echo=False,
	future=True
)

# Create session factory
SessionLocal = sessionmaker(
	autocommit=False,
	autoflush=False,
	bind=engine
)


def get_db() -> Generator[Session, None, None]:
	"""Get a database session for dependency injection."""
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()


def init_db():
	"""Initialize the database by creating all tables."""
	Base.metadata.create_all(bind=engine)


def get_session() -> Session:
	"""Get a new database session."""
	return SessionLocal()
