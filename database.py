from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, declarative_base
from settings import settings

### Local Development ###

## SQLite3 -- for local development
# SQLALCHEMY_DATABASE_URL = 'sqlite:///./todoapp.db'
# engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})

## PostgreSQL
# SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:test1234!@localhost/TodoApplicationDatabase'  # Leaving my test password here for reference
# SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:'+ settings.DATABASE_PASSWORD +'@localhost/TodoApplicationDatabase'
# engine = create_engine(SQLALCHEMY_DATABASE_URL)


### Production Deployment using Render ###

## PostgreSQL -- using Render's PostgreSQL
SQLALCHEMY_DATABASE_URL = 'postgresql://todosapp_9t8r_user:'+ settings.DATABASE_PASSWORD +'@dpg-d9prp0m1egvs73cqc47g-a/todosapp_9t8r'
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# create a sessionmaker for the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# create a base class for the models to inherit from

## Legacy Approach 
# Base = declarative_base()

## Modern Approach 
class Base(DeclarativeBase):
    pass