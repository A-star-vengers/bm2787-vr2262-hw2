from passlib.hash import bcrypt_sha256

from tornado.testing import gen_test

from tests.util import HTTPTest, setUpModule, tearDownModule

import demo.models as models
import demonstration
import unittest

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


class TestPuzzleUtils(unittest.TestCase):
    def test_words_overlap(self):
        words_overlap = demonstration.words_overlap
        self.assertEqual(words_overlap((0, 1), (2, 3)), False)
        self.assertEqual(words_overlap((0, 2), (1, 3)), True)
        self.assertEqual(words_overlap((1, 3), (0, 2)), True)
        self.assertEqual(words_overlap((2, 3), (0, 1)), False)

    def test_clue_fits(self):
        clue_fits = demonstration.clue_fits

        clue = models.Clue(answer="AAAA")
        puzzle = models.Puzzle(nrows=5, ncols=5, clues=[])

        # Test fitness
        self.assertEqual(clue_fits(puzzle, clue, 0, 0, False), True)
        self.assertEqual(clue_fits(puzzle, clue, 0, 1, False), True)
        self.assertEqual(clue_fits(puzzle, clue, 0, 2, False), False)
        self.assertEqual(clue_fits(puzzle, clue, 0, 0, True), True)
        self.assertEqual(clue_fits(puzzle, clue, 1, 0, True), True)
        self.assertEqual(clue_fits(puzzle, clue, 2, 0, True), False)

        p_clue1 = models.PuzzleClue(row=0, col=0, direction=False)
        p_clue2 = models.PuzzleClue(row=2, col=1, direction=False)
        p_clue3 = models.PuzzleClue(row=4, col=4, direction=False)
        p_clue1.clue = models.Clue(answer="AABB")
        p_clue2.clue = models.Clue(answer="ABBB")
        p_clue3.clue = models.Clue(answer="A")

        puzzle.clues = [p_clue1, p_clue2, p_clue3]

        """
        [ A A B B _ ]
        [ _ _ _ _ _ ]
        [ _ A B B B ]
        [ _ _ _ _ _ ]
        [ _ _ _ _ A ]
        """

        # Test overlap
        self.assertEqual(clue_fits(puzzle, clue, 2, 0, False), False)
        self.assertEqual(clue_fits(puzzle, clue, 4, 0, False), True)
        self.assertEqual(clue_fits(puzzle, clue, 4, 1, False), False)

        # Test letter matching
        self.assertEqual(clue_fits(puzzle, clue, 0, 0, True), True)
        self.assertEqual(clue_fits(puzzle, clue, 0, 1, True), True)
        self.assertEqual(clue_fits(puzzle, clue, 0, 2, True), False)
