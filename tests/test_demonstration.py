from passlib.hash import bcrypt_sha256

from tornado.escape import json_encode
from tornado.gen import Task
from tornado.testing import gen_test

from tests.util import HTTPTest, setUpModule, tearDownModule

import demo.models as models

utils = (setUpModule, tearDownModule)


class TestHandlers(HTTPTest):
    @gen_test
    async def test_login(self):
        with self.session.begin():
            self.session.add(models.User(
                username='a',
                password_hash=bcrypt_sha256.encrypt('b').encode(),
            ))
        response = await self.fetch(
            '/auth/login?username=a&password=b',
            method='POST',
            follow_redirects=False,
            raise_error=False,
            body=''
        )
        self.assertEqual(response.code, 302, msg=response.body)
        self.assertIn('user', response.headers['Set-Cookie'])
