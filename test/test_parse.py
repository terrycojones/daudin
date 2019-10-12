from unittest import TestCase

from daudinlib.parse import lineSplitter


class TestLineSplitter(TestCase):
    """Test the lineSplitter function."""

    def testEmptyString(self):
        """An empty string should result in a list with an empty string."""
        self.assertEqual([''],
                         list(lineSplitter('')))

    def testString(self):
        """A string with no | should result in the same string."""
        self.assertEqual(['hello'],
                         list(lineSplitter('hello')))

    def testPlainStrings(self):
        """An unescaped | should result in the two expected fields."""
        self.assertEqual(['hello ', ' there'],
                         list(lineSplitter('hello | there')))

    def testEscaped(self):
        """An escaped | should result in one field, with the escape remvoed."""
        self.assertEqual([r'echo hi | wc -c'],
                         list(lineSplitter(r'echo hi \| wc -c')))
