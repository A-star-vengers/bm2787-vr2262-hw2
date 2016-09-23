import asyncio
from functools import partial
import unittest

from sqlalchemy import DDL
from sqlalchemy.orm import sessionmaker

from tornado.platform.asyncio import AsyncIOLoop
from tornado.testing import AsyncHTTPTestCase

from demo.options import options
options.db_schema = 'test'  # noqa

import demo.models as models
import demonstration
from demonstration import Application

engine = models.create_engine()
Session = sessionmaker()


def setUpModule():
    engine.execute(DDL('DROP SCHEMA IF EXISTS test CASCADE'))
    try:
        models.Base.metadata.create_all(engine)
    except Exception:
        engine.execute(DDL('DROP SCHEMA IF EXISTS test CASCADE'))
        raise


def tearDownModule():
    engine.execute(DDL('DROP SCHEMA IF EXISTS test CASCADE'))


class Test(unittest.TestCase):
    def setUp(self):
        self.connection = engine.connect()
        self.transaction = self.connection.begin()
        self.session = Session(bind=self.connection, autocommit=True)
        super().setUp()

    def tearDown(self):
        self.session.close()
        self.transaction.rollback()
        self.connection.close()
        super().tearDown()


class HTTPTest(Test, AsyncHTTPTestCase):
    def get_new_ioloop(self):
        io_loop = AsyncIOLoop()
        asyncio.set_event_loop(io_loop.asyncio_loop)
        demonstration.from_thread = partial(
            io_loop.asyncio_loop.run_in_executor, None)
        return io_loop

    def get_app(self):
        self.app = Application(self.session)
        return self.app

    def fetch(self, *args, **kwargs):
        return self.http_client.fetch(self.get_url(*args), **kwargs)
