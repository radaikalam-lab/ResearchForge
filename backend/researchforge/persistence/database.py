"""Database session and engine management for ResearchForge."""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

from researchforge.configuration.settings import get_settings
from researchforge.persistence.models import Base


class DatabaseManager:
    """Manages database connection, engine, and sessions."""

    def __init__(self, db_url: str | None = None) -> None:
        settings = get_settings()
        raw_url = db_url or settings.database_url
        self.db_url = raw_url.replace("sqlite+aiosqlite://", "sqlite://")
        connect_args = {}
        poolclass = None
        if self.db_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
            poolclass = StaticPool if ":memory:" in self.db_url else NullPool

        if poolclass:
            self.engine: Engine = create_engine(self.db_url, connect_args=connect_args, poolclass=poolclass)
        else:
            self.engine: Engine = create_engine(self.db_url, connect_args=connect_args)
        self.session_factory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

    def dispose(self) -> None:
        """Dispose of underlying engine connection pool."""
        self.engine.dispose()

    def create_tables(self) -> None:
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self) -> None:
        """Drop all database tables."""
        Base.metadata.drop_all(bind=self.engine)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""
        session: Session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Global database manager instance
_default_db_manager: DatabaseManager | None = None


def get_db_manager(db_url: str | None = None) -> DatabaseManager:
    """Retrieve or initialize the global database manager."""
    global _default_db_manager
    if _default_db_manager is None or (db_url is not None and _default_db_manager.db_url != db_url):
        _default_db_manager = DatabaseManager(db_url)
        _default_db_manager.create_tables()
    return _default_db_manager


def init_db(db_url: str | None = None) -> DatabaseManager:
    """Initialize database and create schema."""
    mgr = get_db_manager(db_url)
    mgr.create_tables()
    return mgr
