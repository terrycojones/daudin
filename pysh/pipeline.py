import os
import sys
import six
from code import compile_command
from io import StringIO, TextIOWrapper
from contextlib import contextmanager

if six.PY3:
    from subprocess import run, PIPE
else:
    from subprocess import check_output


@contextmanager
def newStdout(stdout=None):
    originalStdout = sys.stdout
    stdout = stdout or StringIO()
    sys.stdout = stdout
    try:
        yield stdout
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
        self.lastStdin = None
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
        self.lastStdin = self.stdin
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

        self._debug('Trying eval %r.' % (stripped,))
        try:
            with newStdout() as so, newStdin(self.stdin):
                self.local['_'] = self.stdin
                result = eval(stripped, self.local)
        except Exception as e:
            self._debug('Could not eval: %s.' % e)
            return False, False
        else:
            self._debug('Eval returned %r.' % (result,))
            self.text = ''
            if isinstance(result, str):
                if result.endswith('\n'):
                    result = result[:-1]
            elif result is None:
                stdout = so.getvalue()
                if stdout:
                    self._debug('Eval printed %r.' % (stdout,))
                    if stdout.endswith('\n'):
                        stdout = stdout[:-1]
                    if stdout.find('\n') > -1:
                        result = stdout.split('\n')
                        self.lastResultIsList = True
                    else:
                        result = stdout
                else:
                    doPrint = False

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

        self._debug('Trying to compile %r.' % (fullCommand,))

        exception = None

        try:
            codeobj = compile_command(fullCommand)
        except (OverflowError, SyntaxError, ValueError) as e:
            self._debug('%s: %s.' % (e.__class__.__name__, e))
            self.text = ''
            self.incomplete = False
            exception = e
        else:
            self._debug('Command compiled OK.')
            so = StringIO()
            if codeobj:
                self.local['_'] = self.stdin
                with newStdout(so), newStdin(self.stdin):
                    try:
                        exec(codeobj, self.local)
                    except Exception as e:
                        self._debug('Could not exec: %s.' % e)
                        exception = e
                    else:
                        self._debug('Exec succeeded.')
                self.text = ''
                self.incomplete = False
            else:
                self._debug('Incomplete command.')
                self.incomplete = True
                self.text = fullCommand

        if exception is None:
            stdoutValue = so.getvalue()
            if stdoutValue:
                self._debug('Exec printed %r.' % (stdoutValue,))
                self.stdin = stdoutValue
                doPrint = True
        else:
            self._debug('Trying shell with stdin %r.' % (self.stdin,))
            result = self.sh(fullCommand)
            if result:
                doPrint = True
                if result.endswith('\n'):
                    result = result[:-1]
                self.stdin = result.split('\n')
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
        @return: The C{str} output of the command.
        """
        shell = len(args) == 1 and isinstance(args[0], str)

        if self.stdin is None:
            stdin = None
        elif isinstance(self.stdin, list):
            stdin = '\n'.join(map(str, self.stdin)) + '\n'
        else:
            stdin = str(self.stdin)

        if six.PY3:
            return run(*args, check=True, stdout=PIPE, input=stdin, text=True,
                       encoding='UTF-8', shell=shell, universal_newlines=True,
                       **kwargs).stdout
        else:
            return check_output(*args, stdin=stdin, shell=shell,
                                universal_newlines=True, **kwargs)

    def cd(self, dest):
        os.chdir(dest)
        return self.IGNORE

    def toggleDebug(self):
        self.debug = not self.debug

    def undo(self):
        self.stdin = self.lastStdin

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
