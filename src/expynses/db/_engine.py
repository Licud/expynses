from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from alembic.config import Config
from alembic import command


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None

def init_db() -> None:
    global _engine, _session_factory

    url = "sqlite:///data/expynses.db"

    cfg = Config()
    cfg.set_main_option("script_location", "alembic")
    cfg.set_main_option("sqlalchemy.url", url)

    db_path = Path(url.replace("sqlite:///", ""))

    db_path.parent.mkdir(parents=True, exist_ok=True)
    _engine = create_engine(f"sqlite:///{db_path}")
    _session_factory = sessionmaker(_engine)

    command.upgrade(cfg, "head")


def get_session() -> Session:
    if _session_factory is None:
        raise RuntimeError("init_db() must be called before using the database")
    return _session_factory()
