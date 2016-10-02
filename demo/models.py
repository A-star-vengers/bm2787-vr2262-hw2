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

class Puzzle(Base):
    """This model represents a crossword puzzle"""
    __tablename__ = "puzzle"
    id = sa.Column(
        pg.UUID, primary_key=True, server_default=func.uuid_generate_v4())
    name = sa.Column(sa.Text, nullable=False, unique=True)
    nrows = sa.Column(sa.Integer, nullable=False)
    ncols = sa.Column(sa.Integer, nullable=False)
    clues = sa.orm.relationship("PuzzleClue")

    def as_matrix(self):
        """ Return the puzzle as a matrix of letters."""
        matrix = [[None for i in range(self.ncols)] for j in range(self.nrows)]
        for clue in self.clues:
            if clue.direction: # Down
                row = clue.row
                for letter in clue.clue.answer:
                    matrix[row][clue.col] = letter
                    row += 1
            else: # Across
                col = clue.col
                for letter in clue.clue.answer:
                    matrix[clue.row][col] = letter
                    col += 1
        return matrix

class Clue(Base):
    """This model represents a clue/answer pair"""
    __tablename__ = "clue"
    id = sa.Column(
        pg.UUID, primary_key=True, server_default=func.uuid_generate_v4())
    answer = sa.Column(sa.Text, nullable=False, unique=True)
    clue = sa.Column(sa.Text, nullable=False)

class PuzzleClue(Base):
    """This model represents clues that belongs to a puzzle"""
    __tablename__ = "puzzle_clue"
    id = sa.Column(
        pg.UUID, primary_key=True, server_default=func.uuid_generate_v4())
    puzzle_id = sa.Column(pg.UUID, sa.ForeignKey("puzzle.id"), nullable=False)
    clue_id = sa.Column(pg.UUID, sa.ForeignKey("clue.id"), nullable=False)
    row = sa.Column(sa.Integer, nullable=False)
    col = sa.Column(sa.Integer, nullable=False)
    direction = sa.Column(sa.Boolean, nullable=False)
    clue = sa.orm.relationship("Clue")

