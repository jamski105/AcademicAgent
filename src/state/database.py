"""
SQLAlchemy Database Models für Academic Agent v2.1

Tables:
- research_sessions: Recherche-Sessions
- candidates: Paper-Kandidaten (aus APIs)
- papers: Ausgewählte Papers (nach Ranking)
- quotes: Extrahierte Zitate

v2.1 Changes:
- DB path is now per-run (runs/{timestamp}/session.db)
- No default DB path - must be provided by coordinator
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# Base
Base = declarative_base()


# ============================================
# Models
# ============================================

class ResearchSession(Base):
    """Recherche-Session"""
    __tablename__ = "research_sessions"

    id = Column(String, primary_key=True)  # UUID
    query = Column(Text, nullable=False)
    mode = Column(String, default="standard")  # quick/standard/deep/custom
    status = Column(String, default="in_progress")  # in_progress/completed/failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    config = Column(JSON, nullable=True)  # Research mode config

    # Relationships
    candidates = relationship("Candidate", back_populates="session", cascade="all, delete-orphan")
    papers = relationship("Paper", back_populates="session", cascade="all, delete-orphan")
    quotes = relationship("Quote", back_populates="session", cascade="all, delete-orphan")


class Candidate(Base):
    """Paper-Kandidat (aus API)"""
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("research_sessions.id"), nullable=False)

    # Metadaten
    doi = Column(String, unique=True, index=True)
    title = Column(Text, nullable=False)
    authors = Column(JSON)  # List of authors
    year = Column(Integer)
    venue = Column(String)  # Journal/Conference
    abstract = Column(Text)
    citations = Column(Integer, default=0)  # Citation count (for ranking)

    # API Info
    source_api = Column(String)  # crossref/openalex/semantic_scholar
    api_metadata = Column(JSON)  # Original API response

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    session = relationship("ResearchSession", back_populates="candidates")


class Paper(Base):
    """Ausgewähltes Paper (nach Ranking)"""
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("research_sessions.id"), nullable=False)

    # Metadaten (von Candidate übernommen)
    doi = Column(String, nullable=False, index=True)
    title = Column(Text, nullable=False)
    authors = Column(JSON)
    year = Column(Integer)
    venue = Column(String)
    abstract = Column(Text)
    citations = Column(Integer, default=0)

    # Scoring
    relevance_score = Column(Float)
    recency_score = Column(Float)
    quality_score = Column(Float)
    authority_score = Column(Float)
    total_score = Column(Float, index=True)
    rank = Column(Integer)  # 1-based ranking

    # PDF Info
    pdf_url = Column(String, nullable=True)
    pdf_path = Column(String, nullable=True)  # Local path
    pdf_source = Column(String, nullable=True)  # unpaywall/core/dbis_browser
    pdf_downloaded = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("ResearchSession", back_populates="papers")
    quotes = relationship("Quote", back_populates="paper", cascade="all, delete-orphan")


class Quote(Base):
    """Extrahiertes Zitat"""
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("research_sessions.id"), nullable=False)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)

    # Zitat
    quote_text = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    context_before = Column(Text, nullable=True)  # 50 words before
    context_after = Column(Text, nullable=True)  # 50 words after

    # Validierung
    validated = Column(Boolean, default=False)  # Gegen PDF validiert
    word_count = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("ResearchSession", back_populates="quotes")
    paper = relationship("Paper", back_populates="quotes")


# ============================================
# Database Manager
# ============================================

class DatabaseManager:
    """Manages Database Connection & Sessions"""

    def __init__(self, db_path: Path):
        """
        Initialize Database Manager

        Args:
            db_path: Path to SQLite DB (required in v2.1)
                    Should be: runs/{timestamp}/session.db

        Raises:
            ValueError: If db_path is None

        Example:
            db_manager = DatabaseManager(db_path=Path("runs/2026-02-27_14-30-00/session.db"))
        """
        if db_path is None:
            raise ValueError("db_path is required in v2.1 (runs/{timestamp}/session.db)")

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create Engine
        self.engine = create_engine(f"sqlite:///{self.db_path}", echo=False)

        # Create Tables
        Base.metadata.create_all(self.engine)

        # SessionMaker
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_session(self):
        """Get SQLAlchemy Session (context manager)"""
        return self.SessionLocal()

    def reset_database(self):
        """Drop all tables and recreate (for testing)"""
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)


# ============================================
# Convenience Functions
# ============================================

def get_db_manager(db_path: Path) -> DatabaseManager:
    """
    Get DatabaseManager instance

    Args:
        db_path: Path to SQLite DB (required)

    Returns:
        DatabaseManager instance
    """
    return DatabaseManager(db_path=db_path)


if __name__ == "__main__":
    """Test Database"""
    import tempfile
    import uuid

    print("Testing Database Models...")

    # Test DB
    temp_db = Path(tempfile.mktemp(suffix=".db"))
    db_manager = DatabaseManager(db_path=temp_db)

    with db_manager.get_session() as session:
        # Create Research Session
        research_session = ResearchSession(
            id=str(uuid.uuid4()),
            query="DevOps Governance",
            mode="quick"
        )
        session.add(research_session)
        session.commit()

        print(f"✅ Created session: {research_session.id}")

        # Add Candidate
        candidate = Candidate(
            session_id=research_session.id,
            doi="10.1109/test.2024",
            title="Test Paper",
            authors=["Author 1", "Author 2"],
            year=2024,
            source_api="crossref"
        )
        session.add(candidate)
        session.commit()

        print(f"✅ Created candidate: {candidate.title}")

        # Query
        all_sessions = session.query(ResearchSession).all()
        print(f"✅ Found {len(all_sessions)} session(s)")

    # Cleanup
    temp_db.unlink()
    print("\n✅ Database tests passed!")
