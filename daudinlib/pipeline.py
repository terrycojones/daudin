import os
import sys
import re
import select
import termios
import tty
import pty
from code import compile_command
from io import StringIO, TextIOWrapper
from contextlib import contextmanager
from os.path import exists, join, expanduser
import traceback
from subprocess import Popen, PIPE, CalledProcessError, run

_originalStdout = sys.stdout

# The following escape sequence regex is taken from
# https://stackoverflow.com/questions/14693701/\
# how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
# Answer by https://stackoverflow.com/users/100297/martijn-pieters
ANSI_esc = re.compile(r'''
    \x1B    # ESC
    [@-_]   # 7-bit C1 Fe
    [0-?]*  # Parameter bytes
    [ -/]*  # Intermediate bytes
    [@-~]   # Final byte
''', re.VERBOSE)


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

    def __init__(self, outfp=sys.stdout, errfp=sys.stderr, loadInitFile=True):
        self.outfp = outfp
        self.errfp = errfp
        self.stdin = None
        self.lastStdin = None
        self.stdout = None
        self.pendingText = ''
        self.debug = False
        self.printTracebacks = False
        self.initFile = join(expanduser('~'), '.daudin.py')
        self.lastResultIsList = None
        self.local = {}
        if loadInitFile:
            self.loadInitFile()
        self.initializeLocal()
        self.inPipeline = False

    @property
    def incomplete(self):
        return bool(self.pendingText)

    def loadInitFile(self):
        """
        Load the user's initialization file.

        @return: A C{bool} indicating whether an init file was loaded.
        """
        if exists(self.initFile):
            exec(open(self.initFile).read(), self.local)
            return True
        return False

    def initializeLocal(self):
        """Update the C{self.local} dict to be used with eval/exec."""
        for key, value in (('self', self), ('sh', self.sh), ('cd', self.cd)):
            self.local.setdefault(key, value)

    def run(self, command, commandNumber=1, nCommands=1):
        self._debug('Processing %r.' % command)
        self.lastStdin = self.stdin
        self.lastResultIsList = False
        strippedCommand = command.strip()

        if self.pendingText:
            # The previous command was incomplete.
            fullCommand = self.pendingText + '\n' + (
                command if strippedCommand else '')
        else:
            fullCommand = strippedCommand

        # This command is executing as part of a pipeline if:
        #   1) we were already in a pipeline (due to the last command line) or
        #   2) this is not the 1st command of a multi-command command line, or
        #   3) this is the first command  of a multi-command command line but
        #      the command is equal (this happens when a command line starts
        #      with a pipe symbol).
        self.inPipeline = self.inPipeline or commandNumber > 1 or (
            nCommands > 1 and commandNumber == 1 and not fullCommand)

        self._debug('%s pipeline.' % ('In' if self.inPipeline else 'Not in'))

        print_ = (commandNumber == nCommands)

        handled, doPrint = self._tryEval(fullCommand, print_)

        if not handled:
            handled, doPrint = self._tryExec(fullCommand, print_)

        if not handled:
            handled, doPrint = self._tryShell(fullCommand, print_)

        if handled:
            if commandNumber == nCommands:
                self.inPipeline = not fullCommand
        else:
            print('Could not handle command %r' % command, file=self.errfp)
            self.reset()

        return bool(self.pendingText), doPrint

    def _tryEval(self, strippedCommand, print_):
        if not strippedCommand:
            self._debug('Eval skipped (command empty).')
            return False, False

        self._debug('Trying eval %r.' % (strippedCommand,))
        try:
            with newStdout() as so:
                self.local['_'] = self.stdin
                result = eval(strippedCommand, self.local)
        except Exception as e:
            self._debug('Could not eval: %s.' % e)
            if self.printTracebacks:
                self._debug(traceback.format_exc())
            return False, False
        else:
            self._debug('Eval returned %r.' % (result,))
            self.pendingText = ''
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
                    print_ = False

            if result is self.IGNORE:
                print_ = False
            else:
                self.stdin = result

            return True, print_

    def _tryExec(self, command, print_):
        self._debug('Trying to compile %r.' % (command,))

        exception = None

        try:
            codeobj = compile_command(command)
        except (OverflowError, SyntaxError, ValueError) as e:
            self._debug('%s: %s.' % (e.__class__.__name__, e))
            if self.printTracebacks:
                self._debug(traceback.format_exc())
            self.pendingText = ''
            exception = e
        else:
            self._debug('Command compiled OK.')
            so = StringIO()
            if codeobj:
                self.local['_'] = self.stdin
                with newStdout(so):
                    try:
                        exec(codeobj, self.local)
                    except Exception as e:
                        self._debug('Could not exec: %s.' % e)
                        if self.printTracebacks:
                            self._debug(traceback.format_exc())
                        exception = e
                    else:
                        self._debug('Exec succeeded.')
                self.pendingText = ''
            else:
                self._debug('Incomplete command.')
                self.pendingText = command

        if exception is None:
            if self.pendingText:
                print_ = False
            else:
                stdout = so.getvalue()
                if stdout:
                    self._debug('Exec printed %r.' % (stdout,))
                    if stdout.endswith('\n'):
                        stdout = stdout[:-1]
                    if stdout.find('\n') > -1:
                        self.stdin = stdout.split('\n')
                        self.lastResultIsList = True
                    else:
                        self.stdin = stdout
                else:
                    print_ = False

            return True, print_
        else:
            return False, False

    def _tryShell(self, command, print_):
        self._debug('Trying shell %r with stdin %r.' % (command, self.stdin,))
        try:
            result = self.sh(command, print_=print_)
        except CalledProcessError as e:
            print('Process error: %s' % e, file=sys.errfp)
            return False, False

        self._debug('Shell returned %r' % (result,))
        if result:
            if result.endswith('\n'):
                result = result[:-1]
            self.stdin = result.split('\n')
            # Set lastResultIsList to False because the result has
            # already been printed in its non-list form. So next time
            # we print it we want to see the list.
            self.lastResultIsList = False
        else:
            self.stdin = []

        return True, False

    def sh(self, *args, print_=False, **kwargs):
        """
        Execute a shell command, with input from our C{self.stdin}.

        @param args: Positional arguments to pass to C{subprocess.run}.
        @param print_: If C{True}, use a pseudo-tty and print the output to
            stdout.
        @param kwargs: Keyword arguments to pass to C{Pipe} or
            C{subprocess.run} (depending on the value of C{print_}).
        @raise CalledProcessError: If the command results in an error.
        @return: The C{str} output of the command.
        """
        kwargs.setdefault('shell', len(args) == 1 and isinstance(args[0], str))

        if self.inPipeline:
            if self.stdin is None:
                stdin = None
            elif isinstance(self.stdin, list):
                stdin = '\n'.join(map(str, self.stdin)) + '\n'
            else:
                stdin = str(self.stdin) + '\n'
        else:
            stdin = None

        run = self._shPty if print_ else self._sh

        return run(stdin, *args, **kwargs)

    def _sh(self, stdin, *args, **kwargs):
        """
        Execute a shell command, with input from C{stdin}.

        @param stdin: The C{str} input to the process, else C{None}.
        @param args: Positional arguments to pass to C{subprocess.run}.
        @param kwargs: Keyword arguments to pass to C{subprocess.run}.
        @raise CalledProcessError: If the command results in an error.
        @return: The C{str} output of the command.
        """
        self._debug('In _sh, stdin is %r' % (stdin,))
        kwargs.setdefault('input', stdin)
        kwargs.setdefault('stdout', PIPE)
        kwargs.setdefault('universal_newlines', True)
        return run(*args, **kwargs).stdout

    def _shPty(self, stdin, *args, **kwargs):
        """
        Run a command in a pseudo-tty, with input from C{stdin}.
        """
        self._debug('In _shPty, stdin is %r' % (stdin,))

        # Detect if we're running under pytest, in which case stdin cannot
        # be used.
        pytest = 'pytest' in sys.modules

        # The following is (slightly) adapted from
        # https://stackoverflow.com/questions/41542960/\
        # run-interactive-bash-with-popen-and-a-dedicated-tty-python
        # Answer by https://stackoverflow.com/users/3555925/liao

        # save original tty setting then set it to raw mode
        if not pytest:
            oldTty = termios.tcgetattr(sys.stdin)

        try:
            if not pytest:
                tty.setraw(sys.stdin.fileno())

            # Open a pseudo-terminal to interact with the subprocess.
            master_fd, slave_fd = pty.openpty()

            # Pass os.setsid to have the process run in a new process group.
            #
            # Note that we should be more careful with kwargs here. If the
            # user has called 'sh' interactively and passed a value for
            # stdin, stdout, stderr, or universal_newlines, the following
            # will cause Python to complain about multiple values for a
            # keyword argument. We should check & warn the user etc.
            process = Popen(
                *args, preexec_fn=os.setsid,
                stdin=(slave_fd if stdin is None else PIPE), stdout=slave_fd,
                stderr=slave_fd, universal_newlines=True, **kwargs)

            # Write the command's stdin to it, if any.
            if stdin is not None:
                # print('WROTE %r' % (stdin,), file=self.errfp)
                os.write(process.stdin.fileno(), stdin.encode())
                process.stdin.close()

            if pytest:
                readFds = [master_fd]
            else:
                readFds = [sys.stdin, master_fd]

            result = b''
            while process.poll() is None:
                r, w, e = select.select(readFds, [], [], 0.05)
                if sys.stdin in r:
                    data = os.read(sys.stdin.fileno(), 10240)
                    # print('READ from stdin %r' % (data,), file=self.errfp)
                    if data == b'\x03':
                        process.terminate()
                    else:
                        os.write(master_fd, data)
                elif master_fd in r:
                    data = os.read(master_fd, 10240)
                    # print('READ from master %r' % (data,), file=self.errfp)
                    if data:
                        result += data
                        os.write(_originalStdout.fileno(), data)

        finally:
            if not pytest:
                # Restore tty settings.
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldTty)

        # TODO: Check all this still needed.
        # print('Shell result %r' % (result,), file=self.errfp)
        return ANSI_esc.sub('', result.decode('utf-8')).replace('\r\n', '\n')

    def cd(self, dest):
        os.chdir(dest)
        return self.IGNORE

    def toggleDebug(self):
        self.debug = not self.debug

    def toggleTracebacks(self):
        self.printTracebacks = not self.printTracebacks

    def undo(self):
        self.stdin = self.lastStdin

    def reset(self):
        self.lastStdin = self.stdin
        self.stdin = None
        self.pendingText = ''
        self.lastResultIsList = None
        self.inPipeline = False

    def _debug(self, *args, **kwargs):
        if self.debug:
            kwargs.setdefault('file', self.errfp)
            origEnd = kwargs.get('end', '\n')
            kwargs['end'] = ''
            print(' ' * 20, **kwargs)
            kwargs['end'] = origEnd
            print(*args, **kwargs)
        return self.IGNORE

    def print_(self):
        if isinstance(self.stdin, TextIOWrapper):
            s = self.stdin.read()
            print(s, end='' if s.endswith('\n') else '\n', file=self.outfp)
        elif isinstance(self.stdin, str):
            print(self.stdin, end='' if self.stdin.endswith('\n') else '\n',
                  file=self.outfp)
        elif self.lastResultIsList:
            print('\n'.join(self.stdin), file=self.outfp)
        else:
            print(self.stdin, file=self.outfp)
