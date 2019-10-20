import sys
from unittest import TestCase
from io import StringIO

from daudinlib.interaction import REPL, Batch
from daudinlib.pipeline import Pipeline


class TestREPL(TestCase):
    """Test the REPL class."""
    def setup_method(self, method):
        try:
            del sys.ps1
        except AttributeError:
            pass
        try:
            del sys.ps2
        except AttributeError:
            pass

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


class TestInteractiveREADME(TestCase):
    """Test some examples from the README when entered interactively."""
    def setup_method(self, method):
        try:
            del sys.ps1
        except AttributeError:
            pass
        try:
            del sys.ps2
        except AttributeError:
            pass

    def testAreaFunction(self):
        """Define an area function and call it."""
        pl = Pipeline(loadInitFile=False)
        repl = REPL(pl)

        repl.runCommandLine('from math import pi')
        self.assertEqual(REPL.DEFAULT_PS1, repl.prompt)

        repl.runCommandLine('def area(r):')
        self.assertEqual(REPL.DEFAULT_PS2, repl.prompt)

        repl.runCommandLine('    return r ** 2 * pi')
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

        repl.runCommandLine('    return int(x) * 3')
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

        repl.runCommandLine('    return int(x) * 3')
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

        repl.runCommandLine('    return int(x) * 3')
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


class TestBatch(TestCase):
    """Test the Batch class."""

    def testAttributes(self):
        """
        A Batch instance must have the expected attributes.
        """
        pl = Pipeline(loadInitFile=False)
        batch = Batch(pl)
        self.assertIs(pl, batch.pipeline)

    def testAddUnderscoreVar(self):
        """
        We should be able to add to the _ variable even when not in
        a pipeline.
        """
        commands = StringIO('7\n_ + 10\n')
        out = StringIO()
        pl = Pipeline(loadInitFile=False, outfp=out)
        Batch(pl).run(commands)
        self.assertEqual('7\n17\n', out.getvalue())

    def testEchoPipedToWc(self):
        commands = StringIO('echo a b c | wc -w')
        out = StringIO()
        pl = Pipeline(loadInitFile=False, outfp=out, usePtys=False)
        Batch(pl).run(commands)
        self.assertEqual('3\n', out.getvalue())


class TestBatchREADME(TestCase):
    """Test some examples from the README when run non-interactively."""

    def testAreaFunction(self):
        """Define an area function and call it."""
        commands = StringIO('''
from math import pi
def area(r):
    return r ** 2 * pi

area(2.0)
''')
        out = StringIO()
        pl = Pipeline(loadInitFile=False, outfp=out)
        Batch(pl).run(commands)
        self.assertTrue(out.getvalue().startswith('12.56637'))

    def testTripleFunction(self):
        commands = StringIO('''
def triple(x):
    return int(x) * 3

echo a b c | wc -w | triple(_[0])
''')
        out = StringIO()
        pl = Pipeline(loadInitFile=False, outfp=out)
        Batch(pl).run(commands)
        self.assertEqual('9\n', out.getvalue())

    def testTripleFunctionWithLinebreaks(self):
        commands = StringIO('''
def triple(x):
    return int(x) * 3

echo a b c
| wc -w |
triple(_[0])
''')
        out = StringIO()
        pl = Pipeline(loadInitFile=False, outfp=out, usePtys=False)
        Batch(pl).run(commands)
        self.assertEqual('a b c\n9\n', out.getvalue())

    def testTripleFunctionWithIntermediateCleanup(self):
        commands = StringIO('''
def triple(x):
    return x * 3

echo a b c | wc -w

# Write a little function to convert the first line of _ to an int.
f = lambda line: int(line[0])

| f(_) | triple(_)
''')
        out = StringIO()
        pl = Pipeline(loadInitFile=False, outfp=out, usePtys=False)
        Batch(pl).run(commands)
        self.assertEqual('3\n9\n', out.getvalue())

    def testAbsArithmetic(self):
        commands = StringIO('-6 | abs(_) | _ * 7')
        out = StringIO()
        pl = Pipeline(loadInitFile=False, outfp=out)
        Batch(pl).run(commands)
        self.assertEqual('42\n', out.getvalue())

    def testInterpretingSection(self):
        """
        Test the commands carried out in the 'How commands are interpreted'
        section.
        """
        commands = StringIO('''
4
_
[3, 6, 9]
print('hello')
echo hello too
''')
        out = StringIO()
        pl = Pipeline(loadInitFile=False, outfp=out)
        Batch(pl).run(commands)
        self.assertEqual('4\n4\n[3, 6, 9]\nhello\n', out.getvalue())
