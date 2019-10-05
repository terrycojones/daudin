#!/usr/bin/env python

from __future__ import print_function

import os
import sys
import six
import readline
from code import compile_command
from io import StringIO, TextIOWrapper
from contextlib import contextmanager
from os.path import exists, join, expanduser
from subprocess import CalledProcessError

if six.PY3:
    from subprocess import run, PIPE
else:
    from subprocess import check_output


class CompletedProcess:
    def __init__(self, stdout):
        self.stdout = stdout


def setupReadline():
    """Initialize the readline library and command history.

    @return: A C{bool} to indicate whether standard input is a terminal
        (and therefore interactive).
    """
    if not os.isatty(0):
        # Standard input is closed or is a pipe etc. So there's no user
        # typing at us, and so no point in setting up readline.
        return False

    # Readline code from https://docs.python.org/3.7/library/readline.html
    histfile = os.path.join(os.path.expanduser('~'), '.pysh_history')

    try:
        readline.read_history_file(histfile)
        historyLen = readline.get_current_history_length()
    except FileNotFoundError:
        open(histfile, 'wb').close()
        historyLen = 0

    try:
        readline.append_history_file
    except AttributeError:
        # We won't be able to save readline history. This can happen on
        # Python 3.5 at least - not sure why.
        pass
    else:
        import atexit

        def saveHistory(prevHistoryLen, histfile):
            newHistoryLen = readline.get_current_history_length()
            readline.set_history_length(1000)
            readline.append_history_file(newHistoryLen - prevHistoryLen,
                                         histfile)

        atexit.register(saveHistory, historyLen, histfile)

    return True


@contextmanager
def newStdout(so=None):
    originalStdout = sys.stdout
    so = so or StringIO()
    sys.stdout = so
    try:
        yield so
    except Exception:
        raise
    finally:
        sys.stdout = originalStdout


@contextmanager
def newStdin(fp):
    originalStdin = sys.stdin
    sys.stdin = fp
    try:
        yield fp
    except Exception:
        raise
    finally:
        sys.stdin = originalStdin


class Pipeline:

    IGNORE = object()

    def __init__(self, local):
        self.stdin = None
        self.stdout = None
        self.incomplete = False
        self.text = ''
        self.debug = False
        self.local = local
        self.lastResultIsList = None

        for key, value in (('sys', sys), ('self', self),
                           ('sh', self.sh), ('cd', self.cd)):
            local.setdefault(key, value)

    def run(self, command):
        self.lastResultIsList = False
        self._debug('Processing %r.' % (command,))

        if self.incomplete:
            handled = False
        else:
            handled, doPrint = self._tryEval(command)

        if not handled:
            doPrint = self._tryExec(command)

        return not self.incomplete, doPrint

    def _tryEval(self, command):
        stripped = command.strip()

        if not stripped:
            return False, False

        doPrint = True

        self._debug('Trying eval %r' % (stripped,))
        try:
            with newStdout() as so, newStdin(self.stdin):
                self.local['_'] = self.stdin
                result = eval(stripped, self.local)
        except Exception as e:
            self._debug('Could not eval (%s). Trying exec.' % e)
            return False, False
        else:
            self._debug('Eval -> %r' % (result,))
            self.text = ''
            if result is None:
                stdoutValue = so.getvalue()
                if stdoutValue:
                    result = stdoutValue
                    self._debug('Eval printed -> %r' % (stdoutValue,))
            elif isinstance(result, CompletedProcess):
                if result.stdout:
                    doPrint = True
                    if result.stdout.endswith('\n'):
                        result.stdout = result.stdout[:-1]
                    result = result.stdout.split('\n')
                    self.lastResultIsList = True
                else:
                    doPrint = False
                    result = []

            if result is self.IGNORE:
                doPrint = False
            else:
                self.stdin = result

            return True, doPrint

    def _tryExec(self, command):
        doPrint = False
        if not self.incomplete:
            command = command.lstrip()
        if self.text:
            fullCommand = self.text + '\n' + command
        else:
            fullCommand = command

        self._debug('Trying compile %r' % (fullCommand,))

        exception = None

        try:
            codeobj = compile_command(fullCommand)
        except (OverflowError, SyntaxError, ValueError) as e:
            self._debug('%s: %s' % (e.__class__.__name__, e))
            self.text = ''
            self.incomplete = False
            exception = e
        else:
            self._debug('Compiled OK')
            so = StringIO()
            if codeobj:
                self.local['_'] = self.stdin
                with newStdout(so), newStdin(self.stdin):
                    try:
                        exec(codeobj, self.local)
                    except Exception as e:
                        exception = e
                self.text = ''
                self.incomplete = False
            else:
                self._debug('Incomplete command')
                self.incomplete = True
                self.text = fullCommand

        if exception is None:
            stdoutValue = so.getvalue()
            if stdoutValue:
                self._debug('Exec printed -> %r' % (stdoutValue,))
                self.stdin = stdoutValue
                doPrint = True
        else:
            result = self.sh(fullCommand)
            if result.stdout:
                doPrint = True
                if result.stdout.endswith('\n'):
                    result.stdout = result.stdout[:-1]
                self.stdin = result.stdout.split('\n')
                self.lastResultIsList = True
            else:
                self.stdin = []
                doPrint = False

        return doPrint

    def sh(self, *args, **kwargs):
        """
        Execute a shell command, with input from our C{self.stdin}.

        @param args: Arguments to be given to subprocess.run (or check_output
            for Python 2).
        @param kwargs: Keyword arguments that will be passed to subprocess.run
            (or check_output for Python 2).
        @raise CalledProcessError: If the command results in an error.
        @return: A C{CompletedProcess} instance.
        """
        shell = len(args) == 1 and isinstance(args[0], str)

        if self.stdin is None:
            stdin = None
        elif isinstance(self.stdin, list):
            stdin = '\n'.join(self.stdin) + '\n'
        else:
            stdin = str(self.stdin)

        if six.PY3:
            return CompletedProcess(
                run(*args, check=True, stdout=PIPE, input=stdin, text=True,
                    encoding='UTF-8', shell=shell, universal_newlines=True,
                    **kwargs).stdout)
        else:
            return CompletedProcess(
                check_output(*args, stdin=stdin, shell=shell,
                             universal_newlines=True, **kwargs))

    def cd(self, dest):
        os.chdir(dest)
        return self.IGNORE

    def toggleDebug(self):
        self.debug = not self.debug

    def _debug(self, *args, **kwargs):
        if self.debug:
            kwargs.setdefault('file', sys.stderr)
            origEnd = kwargs.get('end', '\n')
            kwargs['end'] = ''
            print(' ' * 20, **kwargs)
            kwargs['end'] = origEnd
            print(*args, **kwargs)
        return self.IGNORE

    def print_(self):
        if isinstance(self.stdin, TextIOWrapper):
            s = self.stdin.read()
            print(s, end='' if s.endswith('\n') else '\n')
        elif isinstance(self.stdin, str):
            print(self.stdin, end='' if self.stdin.endswith('\n') else '\n')
        elif self.lastResultIsList:
            print('\n'.join(self.stdin))
        else:
            print(self.stdin)


def main():
    local = {}
    rc = join(expanduser('~'), '.pysh.py')
    if exists(rc):
        exec(open(rc).read(), local)

    try:
        sys.ps1
    except AttributeError:
        sys.ps1 = '>>> '

    try:
        sys.ps2
    except AttributeError:
        sys.ps2 = '... '

    prompt = sys.ps1
    exitOnControlD = printOnControlD = True
    pl = Pipeline(local)

    while True:
        doPrint = True
        try:
            if six.PY3:
                text = input(prompt)
            else:
                text = raw_input(prompt)
        except EOFError:
            print('^D', file=sys.stderr)
            if exitOnControlD:
                sys.exit()
            else:
                if doPrint and printOnControlD:
                    pl.print_()
                    printOnControlD = False
                else:
                    printOnControlD = True
                pl = Pipeline(local)
                prompt = sys.ps1
                exitOnControlD = True
        else:
            exitOnControlD = False
            for command in text.split('|'):
                if command == '%d':
                    pl.toggleDebug()
                    doPrint = False
                elif command.startswith('%cd '):
                    pl.cd(command.split(None, 1)[1])
                    doPrint = False
                else:
                    try:
                        complete, doPrint = pl.run(command)
                    except CalledProcessError as e:
                        # A process in the middle of a pipeline gave an
                        # error. Quit the pipeline (similar to set -o
                        # pipefail in bash) and reset ourselves.
                        print('Process error: %s' % e, file=sys.stderr)
                        pl = Pipeline(local)
                        prompt = sys.ps1
                        break
                    else:
                        prompt = sys.ps1 if complete else sys.ps2
            if doPrint:
                pl.print_()
                printOnControlD = False
            else:
                printOnControlD = True


if __name__ == '__main__':
    interactive = setupReadline()
    main()
