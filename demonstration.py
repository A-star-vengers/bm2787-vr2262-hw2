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

path = partial(os.path.join, os.path.dirname(__file__))
path.__doc__ = 'Get the full path relative to the directory of this file.'

from_thread = partial(get_event_loop().run_in_executor, None)
from_thread.__doc__ = 'Run a function in another thread.'


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
