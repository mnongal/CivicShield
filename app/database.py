import json
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import Date, JSON, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / '.env')
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{(ROOT / "civicshield.db").as_posix()}')
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {})


class Base(DeclarativeBase):
    pass


class Program(Base):
    """One SQLAlchemy model works with both SQLite and PostgreSQL."""

    __tablename__ = 'programs'
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(30))
    summary: Mapped[str] = mapped_column(String(1000))
    source_url: Mapped[str] = mapped_column(String(500))
    last_updated: Mapped[date | None] = mapped_column(Date, nullable=True)
    verified_at: Mapped[date] = mapped_column(Date)
    details: Mapped[dict] = mapped_column(JSON)


def initialize():
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        for row in json.loads((ROOT / 'data/programs.json').read_text(encoding='utf-8')):
            row['last_updated'] = date.fromisoformat(row['last_updated']) if row['last_updated'] else None
            row['verified_at'] = date.fromisoformat(row['verified_at'])
            # Upsert curated seed records, so restarting also applies reviewed data updates.
            session.merge(Program(**row))
        session.commit()


def get_programs() -> list[Program]:
    with Session(engine) as session:
        return list(session.scalars(select(Program).order_by(Program.id)))


def public_program(p: Program) -> dict:
    return {key: getattr(p, key) for key in ('id', 'name', 'category', 'summary', 'source_url', 'last_updated', 'verified_at', 'details')}
