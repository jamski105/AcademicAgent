"""State Manager für Academic Agent v2.0 - Verwaltet Research Session State"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from .database import DatabaseManager, ResearchSession, Candidate, Paper, Quote


class StateManager:
    """Manages Research Session State (SQLite + JSON Backup)"""

    def __init__(self, db_path: Optional[Path] = None, json_backup_dir: Optional[Path] = None):
        self.db_manager = DatabaseManager(db_path=db_path)
        self.json_backup_dir = json_backup_dir or Path.home() / ".cache" / "academic_agent" / "backups"
        self.json_backup_dir.mkdir(parents=True, exist_ok=True)

    def create_session(self, query: str, mode: str = "standard", config: Optional[Dict] = None) -> str:
        """Create new research session"""
        session_id = str(uuid.uuid4())
        with self.db_manager.get_session() as db_session:
            session = ResearchSession(id=session_id, query=query, mode=mode, config=config)
            db_session.add(session)
            db_session.commit()
        return session_id

    def save_candidates(self, session_id: str, candidates: List[Dict[str, Any]]) -> None:
        """Save paper candidates from APIs"""
        with self.db_manager.get_session() as db_session:
            for cand_data in candidates:
                candidate = Candidate(session_id=session_id, **cand_data)
                db_session.add(candidate)
            db_session.commit()

    def save_papers(self, session_id: str, papers: List[Dict[str, Any]]) -> None:
        """Save selected papers after ranking"""
        with self.db_manager.get_session() as db_session:
            for paper_data in papers:
                paper = Paper(session_id=session_id, **paper_data)
                db_session.add(paper)
            db_session.commit()

    def save_quotes(self, session_id: str, paper_id: int, quotes: List[Dict[str, Any]]) -> None:
        """Save extracted quotes"""
        with self.db_manager.get_session() as db_session:
            for quote_data in quotes:
                quote = Quote(session_id=session_id, paper_id=paper_id, **quote_data)
                db_session.add(quote)
            db_session.commit()

    def get_session(self, session_id: str) -> Optional[ResearchSession]:
        """Get research session"""
        with self.db_manager.get_session() as db_session:
            return db_session.query(ResearchSession).filter_by(id=session_id).first()

    def get_candidates(self, session_id: str) -> List[Dict[str, Any]]:
        """Get candidates from database"""
        with self.db_manager.get_session() as db_session:
            candidates = db_session.query(Candidate).filter_by(session_id=session_id).all()
            return [
                {
                    "doi": c.doi,
                    "title": c.title,
                    "authors": c.authors,
                    "year": c.year,
                    "venue": c.venue,
                    "abstract": c.abstract,
                    "citations": c.citations or 0,
                    "source_api": c.source_api,
                    "api_metadata": c.api_metadata
                }
                for c in candidates
            ]

    def mark_completed(self, session_id: str) -> None:
        """Mark session as completed"""
        with self.db_manager.get_session() as db_session:
            session = db_session.query(ResearchSession).filter_by(id=session_id).first()
            if session:
                session.status = "completed"
                session.completed_at = datetime.utcnow()
                db_session.commit()

    def export_to_json(self, session_id: str) -> Path:
        """Export session to JSON (backup)"""
        with self.db_manager.get_session() as db_session:
            session = db_session.query(ResearchSession).filter_by(id=session_id).first()
            if not session:
                raise ValueError(f"Session not found: {session_id}")

            data = {
                "session_id": session.id,
                "query": session.query,
                "mode": session.mode,
                "status": session.status,
                "created_at": session.created_at.isoformat(),
                "papers": [{"title": p.title, "doi": p.doi} for p in session.papers],
                "quotes_count": len(session.quotes)
            }

            json_path = self.json_backup_dir / f"{session_id}.json"
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=2)

            return json_path


if __name__ == "__main__":
    import tempfile
    temp_db = Path(tempfile.mktemp(suffix=".db"))
    sm = StateManager(db_path=temp_db)
    sid = sm.create_session("Test Query")
    print(f"✅ Created session: {sid}")
    sm.mark_completed(sid)
    print("✅ State Manager works!")
    temp_db.unlink()
