from unittest import TestCase

from daudinlib.pipeline import Pipeline


class TestPipeline(TestCase):
    """Test the Pipeline class."""

    def testNumber(self):
        """A number should be processed correctly."""
        p = Pipeline(loadInitFile=False)
        p.run('4')
        self.assertEqual(4, p.stdin)

    def testString(self):
        """A string should be processed correctly."""
        p = Pipeline(loadInitFile=False)
        p.run('"hello"')
        self.assertEqual('hello', p.stdin)

    def testTrue(self):
        """True should be processed correctly."""
        p = Pipeline(loadInitFile=False)
        p.run('True')
        self.assertIs(True, p.stdin)

    def testFalse(self):
        """False should be processed correctly."""
        p = Pipeline(loadInitFile=False)
        p.run('False')
        self.assertIs(False, p.stdin)

    def testNone(self):
        """None should be processed correctly."""
        p = Pipeline(loadInitFile=False)
        p.run('None')
        self.assertEqual(None, p.stdin)

    def testArithmetic(self):
        """Arithmetic should work."""
        p = Pipeline(loadInitFile=False)
        p.run('(3 + 4 + 5) / 4')
        self.assertEqual(3, p.stdin)

    def testFloats(self):
        """Floating point arithmetic should work."""
        p = Pipeline(loadInitFile=False)
        p.run('6.3 / 1.8')
        self.assertEqual(3.5, p.stdin)

    def testInPipelineWithTrailingPipe(self):
        """
        The pipeline must have inPipeline True when the command line ends in a
        pipe.
        """
        p = Pipeline(loadInitFile=False)
        p.run('6', 1, 2)
        p.run('', 2, 2)
        self.assertTrue(p.inPipeline)
        p.run('6', 1, 2)
        self.assertTrue(p.inPipeline)

    def testNotInPipelineInitially(self):
        """
        The pipeline must have inPipeline False when it is created.
        """
        p = Pipeline(loadInitFile=False)
        self.assertFalse(p.inPipeline)

    def testInPipelineWithLeadingPipe(self):
        """
        The pipeline must have inPipeline True when the command line starts
        with a pipe.
        """
        p = Pipeline(loadInitFile=False)
        p.run('6', 1, 1)
        p.run('', 1, 2)
        self.assertTrue(p.inPipeline)

    def testInPipelineWithIntermediateCommand(self):
        """
        The pipeline must have inPipeline True when the command is one of the
        middle commands of a multi-command command line.
        """
        p = Pipeline(loadInitFile=False)
        p.run('6', 3, 5)
        self.assertTrue(p.inPipeline)


class TestREADME(TestCase):
    """Test the examples from the README."""

    def testAreaFunction(self):
        """Define an area function and call it."""
        p = Pipeline(loadInitFile=False)
        p.run('from math import pi')
        self.assertFalse(p.incomplete)
        # self.assertFalse(p.inPipeline)

        p.run('def area(r):')
        self.assertTrue(p.incomplete)
        # self.assertFalse(p.inPipeline)

        p.run('  return r ** 2 * pi', True)
        self.assertTrue(p.incomplete)
        # self.assertFalse(p.inPipeline)

        p.run('', True)
        self.assertFalse(p.incomplete)
        # self.assertFalse(p.inPipeline)

        p.run('area(2.0)')
        self.assertFalse(p.incomplete)
        # self.assertFalse(p.inPipeline)

        self.assertAlmostEqual(12.566370614359172, p.stdin)
