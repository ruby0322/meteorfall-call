from sqlalchemy import Engine

from app.db.models import Base


def init_database(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)
