from __future__ import annotations
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL=os.getenv("DATABASE_URL","postgresql+psycopg://autotube:autotube_dev@localhost:5432/autotube")
engine=create_engine(DATABASE_URL,pool_pre_ping=True)
SessionLocal=sessionmaker(bind=engine,autoflush=False,autocommit=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db=SessionLocal()
    try: yield db
    finally: db.close()
