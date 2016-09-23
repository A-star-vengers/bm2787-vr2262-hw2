from tests.util import Test, setUpModule, tearDownModule

import demo.models as models

utils = (setUpModule, tearDownModule)


class TestUser(Test):
    def test_create(self):
        with self.session.begin():
            self.session.add(models.User(username='a', password_hash=b'b'))
        user = self.session.query(models.User).one()
        self.assertEqual(user.username, 'a')
