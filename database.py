from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, declarative_base

## SQLite3 
SQLALCHEMY_DATABASE_URL = 'sqlite:///./todosapp.db'
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})

## PostgreSQL
# SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:test1234!@localhost/TodoApplicationDatabase'
# engine = create_engine(SQLALCHEMY_DATABASE_URL)

# create a sessionmaker for the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# create a base class for the models to inherit from

## Legacy Approach 
# Base = declarative_base()

## Modern Approach 
class Base(DeclarativeBase):
    pass