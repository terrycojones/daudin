from __future__ import print_function

import sys
import traceback
import shlex
from os.path import expanduser

from daudinlib.parse import lineSplitter
from daudinlib.pipeline import Pipeline


class _DaudinBase:

    def __init__(self, pipeline=None):
        self.pipeline = pipeline or Pipeline()

    def runCommandLine(self, text):
        commands = list(lineSplitter(text))
        nCommands = len(commands)
        for i, command in enumerate(commands, start=1):
            if self.runCommand(command, i, nCommands) is False:
                return False
        return True

    def _handleSpecial(self, command):
        strippedCommand = command.strip()
        pipeline = self.pipeline

        if strippedCommand.startswith('%cd'):
            if strippedCommand == '%cd':
                dir_ = expanduser('~')
            else:
                args = shlex.split(command[3:])
                if len(args) > 1:
                    print('Only one argument can be given to cd.',
                          file=sys.stderr)
                    dir_ = None
                else:
                    dir_ = args[0]

            if dir_ is not None:
                try:
                    pipeline.cd(dir_)
                except FileNotFoundError:
                    print('No such directory %r' % dir_, file=sys.stderr)

            return True

        if strippedCommand == '%d':
            pipeline.toggleDebug()
            return True

        if strippedCommand == '%r':
            if pipeline.loadInitFile():
                print('Reloaded.', file=sys.stderr)
            else:
                print('Daudin init file %r does not exist.' %
                      pipeline.initFile, file=sys.stderr)
            return True

        if strippedCommand == '%t':
            pipeline.toggleTracebacks()
            # If we just turned on traceback printing, make sure debug
            # printing is also on.
            if pipeline.printTracebacks:
                pipeline.debug = True
            return True

        if strippedCommand == '%u':
            pipeline.undo()
            return True

        if strippedCommand == '_':
            pipeline.print_()
            return True

        return False


class REPL(_DaudinBase):
    """Manage an interactive daudin session.

    @param pipeline: A C{daudinlib.pipeline.Pipeline} instance.
    @param ps1: A C{str} to use as the primary prompt, or a no-argument
        function that returns a C{str}. Note that the passed value will
        only be used if C{sys.ps1} is not already set. The value may have
        already been set when reading the user's daudin init file.
    @param ps2: A C{str} to use as the secondary prompt, or a no-argument
        function that returns a C{str}. Note that the passed value will
        only be used if C{sys.ps2} is not already set. The value may have
        already been set when reading the user's daudin init file.
    """

    DEFAULT_PS1 = '>>> '
    DEFAULT_PS2 = '... '

    def __init__(self, pipeline=None, ps1=DEFAULT_PS1, ps2=DEFAULT_PS2):
        super().__init__(pipeline)

        try:
            sys.ps1
        except AttributeError:
            sys.ps1 = ps1

        try:
            sys.ps2
        except AttributeError:
            sys.ps2 = ps2

        self.prompt = sys.ps1

    def reset(self):
        self.pipeline.reset()
        self.prompt = sys.ps1

    def _readStdin(self):
        while True:
            if callable(self.prompt):
                prompt = self.prompt()
            else:
                prompt = self.prompt
            try:
                text = input(prompt)
            except KeyboardInterrupt:
                print('^C', file=sys.stderr)
                self.reset()
            except EOFError:
                print('^D', file=sys.stderr)
                sys.exit()
            else:
                yield text

    def run(self):
        for commandLine in self._readStdin():
            self.runCommandLine(commandLine)

    def runCommand(self, command, commandNumber=1, nCommands=1):
        pipeline = self.pipeline

        if self._handleSpecial(command):
            return

        try:
            incomplete, doPrint = pipeline.run(command, commandNumber,
                                               nCommands)
        except KeyboardInterrupt:
            print('^C', file=sys.stderr)
            self.reset()
            return False
        except Exception:
            print(traceback.format_exc(), file=sys.stderr)
            self.reset()
            return False
        else:
            self.prompt = sys.ps2 if incomplete else sys.ps1
            if doPrint:
                pipeline.print_()

        return True


class Batch(_DaudinBase):

    def run(self, fp):
        runCommandLine = self.runCommandLine
        for commandLine in fp:
            runCommandLine(commandLine.rstrip())

    def runCommand(self, command, commandNumber=1, nCommands=1):
        if not self._handleSpecial(command):
            _, doPrint = self.pipeline.run(command, commandNumber, nCommands)

            if doPrint:
                self.pipeline.print_()

        return True
