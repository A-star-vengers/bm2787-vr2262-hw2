"""ORM models."""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from demo.options import options

metadata = sa.MetaData(schema=options.db_schema)
Base = declarative_base(metadata=metadata)

sa.event.listen(
    Base.metadata,
    'before_create',
    sa.DDL("""
        ALTER DATABASE {} SET TIMEZONE TO "UTC";
        CREATE SCHEMA IF NOT EXISTS public;
        CREATE SCHEMA IF NOT EXISTS {};
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA pg_catalog;
    """.format(options.db_database, options.db_schema)),
)


def create_engine():
    """Connect to the database using the application-level options."""
    connection_string = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(
        options.db_user, options.db_password, options.db_host,
        options.db_port, options.db_database)
    return sa.create_engine(connection_string)


class User(Base):
    """This model represents an application user."""

    __tablename__ = 'user'
    id = sa.Column(
        pg.UUID, primary_key=True, server_default=func.uuid_generate_v4())
    username = sa.Column(sa.Text, nullable=False, unique=True)
    password_hash = sa.Column(pg.BYTEA, nullable=False)
