import unittest

from evernotebot.bot.shortcuts import get_cached_object


class TestShortucts(unittest.TestCase):
    def test_get_cached_object(self):
        cache = {}
        result = get_cached_object(cache, None, constructor=lambda: {"default": 1})
        self.assertEqual(result, {"default": 1})
        result = get_cached_object(cache, "x", constructor=lambda: {"x": 2})
        self.assertEqual(result, {"x": 2})
        result = get_cached_object(cache, "y", constructor=lambda: {"y": 3})
        self.assertEqual(result, {"y": 3})
        self.assertEqual(len(cache), 3)
        result = get_cached_object(cache, "x")
        self.assertEqual(len(cache), 3)
        self.assertEqual(result, {"x": 2})
        failed = False
        try:
            get_cached_object(cache, "invalid")
        except KeyError:
            failed = True
        self.assertTrue(failed)

