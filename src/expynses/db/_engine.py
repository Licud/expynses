from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from ._models import Base

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def init_db(db_path: Path) -> None:
    """Create the database file and tables if they don't exist yet."""
    global _engine, _session_factory

    db_path.parent.mkdir(parents=True, exist_ok=True)
    _engine = create_engine(f"sqlite:///{db_path}")
    _session_factory = sessionmaker(_engine)
    Base.metadata.create_all(_engine)


def get_session() -> Session:
    if _session_factory is None:
        raise RuntimeError("init_db() must be called before using the database")
    return _session_factory()
