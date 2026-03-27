from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import settings

# Railway Postgres URLs start with postgres:// but SQLAlchemy requires postgresql://
_db_url = settings.DATABASE_URL
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)

_is_sqlite = "sqlite" in _db_url

if _is_sqlite:
    engine = create_engine(
        _db_url,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG,
    )
else:
    # Postgres — use connection pooling suited for Railway's managed Postgres
    engine = create_engine(
        _db_url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,   # test connections before use (handles Railway restarts)
        echo=settings.DEBUG,
    )


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if _is_sqlite:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
