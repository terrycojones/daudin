import sys
from unittest import TestCase

from daudinlib.interaction import REPL
from daudinlib.pipeline import Pipeline


class TestREPL(TestCase):
    """Test the REPL class."""

    def testSetPrompts(self):
        """
        Setting the prompts via __init__ must work.
        """
        pl = Pipeline(loadInitFile=False)
        repl = REPL(pipeline=pl, ps1='x', ps2='y')
        self.assertEqual('x', repl.prompt)
        self.assertEqual('x', sys.ps1)
        self.assertEqual('y', sys.ps2)

    def testToggleDebug(self):
        """
        The REPL instance must be able to toggle the pipeline debug setting.
        """
        pl = Pipeline(loadInitFile=False)
        repl = REPL(pl)
        repl.runCommandLine('%d')
        self.assertIs(True, pl.debug)
        repl.runCommandLine('%d')
        self.assertIs(False, pl.debug)

    def testToggleTracebacks(self):
        """
        The REPL instance must be able to toggle the printing of tracebacks.
        """
        pl = Pipeline(loadInitFile=False)
        repl = REPL(pl)
        repl.runCommandLine('%t')
        self.assertIs(True, pl.printTracebacks)
        self.assertIs(True, pl.debug)
        repl.runCommandLine('%t')
        self.assertIs(False, pl.printTracebacks)
        # Note that turning off traceback printing does not turn off debug.
        self.assertIs(True, pl.debug)

    def testAttributes(self):
        """
        A REPL instance must have the expected attributes.
        """
        pl = Pipeline(loadInitFile=False)
        repl = REPL(pl)
        self.assertIs(pl, repl.pipeline)
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

    def testNumber(self):
        """
        The REPL instance must be in the expected state after processing a
        number.
        """
        pl = Pipeline(loadInitFile=False)
        repl = REPL(pl)
        repl.runCommandLine('4')
        self.assertAlmostEqual(4, pl.stdin)
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

    def testNumberPipeOneLine(self):
        """
        The REPL instance must be in the expected state after processing a
        command line containing a number followed by a pipe symbol.
        """
        pl = Pipeline(loadInitFile=False)
        repl = REPL(pl)
        repl.runCommandLine('4 |')
        self.assertAlmostEqual(4, pl.stdin)
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

    def testNumberPipeTwoLines(self):
        """
        The REPL instance must be in the expected state after processing a
        command line containing a number and then a second command line with
        just a pipe symbol.
        """
        pl = Pipeline(loadInitFile=False)
        repl = REPL(pl)
        repl.runCommandLine('4')
        self.assertFalse(pl.inPipeline)
        self.assertEqual(4, pl.stdin)
        repl.runCommandLine('')
        self.assertEqual(4, pl.stdin)
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

    def testIncompleteDict(self):
        """
        The REPL instance must be in the expected state after processing a
        an incomplete dict.
        """
        pl = Pipeline(loadInitFile=False)
        repl = REPL(pl)
        repl.runCommandLine('{ "a": 6, "b": ')
        # Is this next line correct? Should it be None?
        self.assertIs(None, pl.stdin)
        self.assertEqual(REPL.DEFAULT_PS2, repl.prompt)

    def testDictOnTwoLines(self):
        """
        The REPL instance must be in the expected state after processing a
        a dict given on two lines.
        """
        pl = Pipeline(loadInitFile=False)
        repl = REPL(pl)
        repl.runCommandLine('{ "a": 6, "b": ')
        repl.runCommandLine('7 }')
        self.assertEqual({'a': 6, 'b': 7}, pl.stdin)
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

    def testInitialEmptyCommands(self):
        """
        We should be able to hit ENTER repeatedly in a new session, while
        stdin remains as None and the prompt is unchanged.
        """
        pl = Pipeline(loadInitFile=False)
        repl = REPL(pl)

        repl.runCommandLine('')
        self.assertEqual(None, pl.stdin)
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

        repl.runCommandLine('')
        self.assertEqual(None, pl.stdin)
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

    def testInitialWhitespaceCommands(self):
        """
        We should be able to repeatedly enter whitespace commands in a new
        session, while stdin remains as None and the prompt is unchanged.
        """
        pl = Pipeline(loadInitFile=False)
        repl = REPL(pl)

        repl.runCommandLine('  ')
        self.assertEqual(None, pl.stdin)
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

        repl.runCommandLine('  \t  ')
        self.assertEqual(None, pl.stdin)
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

    def testEmptyCommands(self):
        """
        We should be able to hit ENTER repeatedly without changing
        the pending stdin value or the prompt.
        """
        pl = Pipeline(loadInitFile=False)
        repl = REPL(pl)

        repl.runCommandLine('4')
        self.assertEqual(4, pl.stdin)
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

        repl.runCommandLine('')
        self.assertEqual(4, pl.stdin)
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

        repl.runCommandLine('')
        self.assertEqual(4, pl.stdin)
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

    def testWhitespaceCommands(self):
        """
        We should be able to repeatedly enter whitespace commands without
        changing the pending stdin value or the prompt.
        """
        pl = Pipeline(loadInitFile=False)
        repl = REPL(pl)

        repl.runCommandLine('4')
        self.assertEqual(4, pl.stdin)
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

        repl.runCommandLine(' ')
        self.assertEqual(4, pl.stdin)
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

        repl.runCommandLine('\t\t')
        self.assertEqual(4, pl.stdin)
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

    def testEchoCat(self):
        """
        We should be able to pipe echo output to cat.
        """
        pl = Pipeline(loadInitFile=False)
        repl = REPL(pl)
        repl.runCommandLine('echo hi | cat')
        self.assertEqual(['hi'], pl.stdin)
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

    def testEchoCatCat(self):
        """
        We should be able to pipe echo output to cat twice.
        """
        pl = Pipeline(loadInitFile=False)
        repl = REPL(pl)
        repl.runCommandLine('echo hi | cat | cat')
        self.assertEqual(['hi'], pl.stdin)
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

    def testAddUnderscoreVar(self):
        """
        We should be able to add to the _ variable even when not in
        a pipeline.
        """
        pl = Pipeline(loadInitFile=False)
        repl = REPL(pl)
        repl.runCommandLine('7')
        repl.runCommandLine('_ + 10')
        self.assertEqual(17, pl.stdin)
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)


class TestREADME(TestCase):
    """Test the examples from the README."""

    def testAreaFunction(self):
        """Define an area function and call it."""
        pl = Pipeline(loadInitFile=False)
        repl = REPL(pl)

        repl.runCommandLine('from math import pi')
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

        repl.runCommandLine('def area(r):')
        self.assertEqual(REPL.DEFAULT_PS2, repl.prompt)

        repl.runCommandLine('  return r ** 2 * pi')
        self.assertEqual(REPL.DEFAULT_PS2, repl.prompt)

        repl.runCommandLine('')
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

        repl.runCommandLine('area(2.0)')
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

        self.assertAlmostEqual(12.566370614359172, pl.stdin)

    def testTripleFunction(self):
        pl = Pipeline(loadInitFile=False)
        repl = REPL(pl)

        repl.runCommandLine('def triple(x):')
        self.assertEqual(REPL.DEFAULT_PS2, repl.prompt)

        repl.runCommandLine('  return int(x) * 3')
        self.assertEqual(REPL.DEFAULT_PS2, repl.prompt)

        repl.runCommandLine('')
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

        repl.runCommandLine('echo a b c | wc -w | triple(_[0])')
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

        self.assertEqual(9, pl.stdin)

    def testTripleFunctionWithLinebreaks(self):
        pl = Pipeline(loadInitFile=False)
        repl = REPL(pl)

        repl.runCommandLine('def triple(x):')
        self.assertEqual(REPL.DEFAULT_PS2, repl.prompt)

        repl.runCommandLine('  return int(x) * 3')
        self.assertEqual(REPL.DEFAULT_PS2, repl.prompt)

        repl.runCommandLine('')
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

        repl.runCommandLine('echo a b c')
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

        repl.runCommandLine('| wc -w |')
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

        repl.runCommandLine('triple(_[0])')
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

        self.assertEqual(9, pl.stdin)

    def testTripleFunctionWithIntermediateCleanup(self):
        pl = Pipeline(loadInitFile=False)
        repl = REPL(pl)

        repl.runCommandLine('def triple(x):')
        self.assertEqual(REPL.DEFAULT_PS2, repl.prompt)

        repl.runCommandLine('  return int(x) * 3')
        self.assertEqual(REPL.DEFAULT_PS2, repl.prompt)

        repl.runCommandLine('')
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

        repl.runCommandLine('echo a b c | wc -w |')
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

        pl.toggleDebug()
        repl.runCommandLine('ll = lambda x: x[0]')
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

        repl.runCommandLine('ll(_)')
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

        repl.runCommandLine('triple(_)')
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

        self.assertEqual(9, pl.stdin)

    def testAbsArithmetic(self):
        pl = Pipeline(loadInitFile=False)
        repl = REPL(pl)
        repl.runCommandLine('-6 | abs(_) | _ * 7')
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)
        self.assertEqual(42, pl.stdin)

    def testInterpretingSection(self):
        """
        Test the commands carried out in the 'How commands are interpreted'
        section.
        """
        pl = Pipeline(loadInitFile=False)
        repl = REPL(pl)
        repl.runCommandLine('4')
        self.assertEqual(4, pl.stdin)

        repl.runCommandLine('_')
        self.assertEqual(4, pl.stdin)

        repl.runCommandLine('[3, 6, 9]')
        self.assertEqual([3, 6, 9], pl.stdin)

        repl.runCommandLine("print('hello')")
        self.assertEqual('hello', pl.stdin)

        repl.runCommandLine('echo hello too')
        self.assertEqual(['hello too'], pl.stdin)

        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)
