#!/usr/bin/env python3
"""COMS W4156 demo. Use Python 3.5."""
from asyncio import get_event_loop
from functools import partial
import os.path

from passlib.hash import bcrypt_sha256

from sqlalchemy import exists
from sqlalchemy.orm import sessionmaker

import tornado.ioloop
from tornado.platform.asyncio import AsyncIOMainLoop
import tornado.web

if __name__ == '__main__':
    from demo.options import parse_command_line
    parse_command_line()

from demo import models  # noqa

User = models.User
Clue = models.Clue
Puzzle = models.Puzzle
PuzzleClue = models.PuzzleClue

path = partial(os.path.join, os.path.dirname(__file__))
path.__doc__ = 'Get the full path relative to the directory of this file.'

from_thread = partial(get_event_loop().run_in_executor, None)
from_thread.__doc__ = 'Run a function in another thread.'

def words_overlap(word1, word2):
    """Determines if two words overlap."""
    first1, last1 = word1
    first2, last2 = word2

    return ((first1 >= first2 and first1 <= last2) or
           (last1 >= first2 and last1 <= last2))

def clue_fits(puzzle, clue, row, col, direction):
    """Determines if a clue fits inside a puzzle."""
    line_len = puzzle.nrows if direction else puzzle.ncols
    first = row if direction else col
    last = first + len(clue.answer) -1

    # Check if it fits inside puzzle
    if last >= line_len:
        return False

    # Check if it doesn't overlap with another clue
    for p_clue in puzzle.clues:
        p_clue_first = p_clue.row if p_clue.direction else p_clue.col
        p_clue_last = p_clue_first + len(p_clue.clue.answer) - 1
        if p_clue.direction == direction:
            if (direction and p_clue.col == col) or (not direction and p_clue.row == row):
                if words_overlap((first,last),(p_clue_first,p_clue_last)):
                    return False

    # Check if letters in the word match the other words already in the puzzle
    matrix = puzzle.as_matrix()
    for letter in clue.answer:
        if matrix[row][col] is not None and matrix[row][col] != letter:
            return False
        if direction:
            row += 1
        else:
            col += 1

    return True


class BaseHandler(tornado.web.RequestHandler):
    """The base class for all handlers."""

    @property
    def session(self):
        """The database session.

        For modification use session.begin context manager.
        """
        return self.application.session

    def get_current_user(self):
        """Return the signed-in user object or None.

        The object is available in templates as current_user.
        """
        user_id = self.get_secure_cookie('user')
        if not user_id:
            return None
        return self.session.query(User).get(user_id.decode())

    def get_user_by_name(self, name):
        """Return a user by username or None."""
        return (
            self.session
            .query(User)
            .filter_by(username=name)
            .one_or_none()
        )


class MainHandler(BaseHandler):
    """The root URL handler."""

    def get(self):
        """Render /."""
        self.render('index.html')


class CreateUserHandler(BaseHandler):
    """User creation handler."""

    def get(self):
        """Render /auth/create/."""
        self.render('create_user.html', error=None)

    async def post(self):
        """Coroutine for creating a user."""
        name = self.get_argument('username')
        if self.session.query(exists().where(User.username == name)).scalar():
            self.render('create_user.html', error='user already exists')
            return
        pw = self.get_argument('password')
        hashed_pw = (await from_thread(bcrypt_sha256.encrypt, pw)).encode()
        with self.session.begin():
            user = User(username=name, password_hash=hashed_pw)
            self.session.add(user)
        self.set_secure_cookie('user', str(user.id))
        self.redirect(self.get_argument('next', '/'))


class LoginHandler(BaseHandler):
    """Handler for logging in."""

    def get(self):
        """Render /auth/login/."""
        self.render('login.html', error=None)

    async def post(self):
        """Coroutine for logging in."""
        user = self.get_user_by_name(self.get_argument('username'))
        if not user:
            self.render(
                'login.html', error='no such username, create account first')
            return
        password = self.get_argument('password')
        correct_password = await from_thread(
            bcrypt_sha256.verify, password, user.password_hash)
        if correct_password:
            self.set_secure_cookie('user', str(user.id))
            self.redirect(self.get_argument('next', '/'))
            return
        self.render('login.html', error='incorrect password')


class LogoutHandler(BaseHandler):
    """Handler for logging out."""

    def get(self):
        """Clear user cookie and redirect."""
        self.clear_cookie('user')
        self.redirect(self.get_argument('next', '/'))


class CreateClueHandler(BaseHandler):
    """Clue creation handler."""

    def get(self):
        """Render /clue/create/."""
        self.render('create_clue.html', error=None)

    def post(self):
        """Method for creating a clue."""
        clue = self.get_argument('clue')
        answer = self.get_argument('answer').upper()
        with self.session.begin():
            self.session.add(Clue(clue=clue, answer=answer))
        self.render('create_clue.html', error='Clue created')

class CreatePuzzleHandler(BaseHandler):
    """Puzzle creation handler."""

    def get(self):
        """Render /puzzle/create/."""
        self.render('create_puzzle.html', error=None)

    def post(self):
        """Method for creating a puzzle."""
        name = self.get_argument('name')
        nrows = self.get_argument('nrows')
        ncols = self.get_argument('ncols')
        with self.session.begin():
            puzzle = Puzzle(name=name, nrows=nrows, ncols=ncols)
            self.session.add(puzzle)
        self.redirect('/puzzle/edit/{}'.format(puzzle.name))

class EditPuzzleHandler(BaseHandler):
    """Puzzle edition handler."""

    def get(self, name):
        """Render /puzzle/edit/{name}."""
        with self.session.begin():
            puzzle = self.session.query(Puzzle).filter_by(name=name).first()
            all_clues = self.session.query(Clue).all()
        if puzzle is None:
            raise tornado.web.HTTPError(404)

        used_clues = [c.clue for c in puzzle.clues]
        available_clues = [c for c in all_clues if c not in used_clues]
        self.render('edit_puzzle.html', puzzle=puzzle, clues=available_clues, error=None)

    def post(self, name):
        """Method for editing a puzzle."""
        clue = self.get_argument('clue')
        row = int(self.get_argument('row'))
        col = int(self.get_argument('col'))
        direction = bool(int(self.get_argument('direction')))
        with self.session.begin():
            puzzle = self.session.query(Puzzle).filter_by(name=name).first()
            all_clues = self.session.query(Clue).all()
            clue = self.session.query(Clue).filter_by(id=clue).first()

        error = None
        used_clues = [c.clue for c in puzzle.clues]
        available_clues = [c for c in all_clues if c not in used_clues]
        if clue is None:
            error = "Clue does not exist"
        elif not clue_fits(puzzle, clue, row, col, direction):
            error = "Clue does not fit"
        else:
            puzzle_clue = PuzzleClue(row=row,col=col,direction=direction)
            puzzle_clue.clue = clue
            puzzle.clues.append(puzzle_clue)
            available_clues.remove(clue)
            self.session.flush()

        self.render('edit_puzzle.html', puzzle=puzzle, clues=available_clues, error=error)


class Application(tornado.web.Application):
    """The demo application."""

    def __init__(self, session=None):
        """Create an Application.

        Has the demo URLs and settings as well as a process-wide database
        session.
        """
        with open(path('COOKIE_SECRET'), 'rb') as cookie_file:
            cookie_secret = cookie_file.read()
        urls = [
            (r'/', MainHandler),
            (r'/auth/create', CreateUserHandler),
            (r'/auth/login', LoginHandler),
            (r'/auth/logout', LogoutHandler),
            (r'/clue/create', CreateClueHandler),
            (r'/puzzle/create', CreatePuzzleHandler),
            (r'/puzzle/edit/([^/]+)', EditPuzzleHandler),
        ]
        settings = {
            'template_path': path('templates'),
            'xsrf_cookies': None,
            'cookie_secret': cookie_secret,
            'login_url': '/auth/login',
        }
        super().__init__(urls, **settings)
        if session is None:
            engine = models.create_engine()
            models.Base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine, autocommit=True)
            self.session = Session()
        else:
            self.session = session


if __name__ == '__main__':
    AsyncIOMainLoop().install()
    Application().listen(8888)
    print('Listening on port 8888')
    get_event_loop().run_forever()
