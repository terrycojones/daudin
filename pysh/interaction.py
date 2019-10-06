from __future__ import print_function

import sys
import six
from os.path import exists, join, expanduser
from subprocess import CalledProcessError

from pysh.parse import lineSplitter
from pysh.pipeline import Pipeline


def interact():
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
        except KeyboardInterrupt:
            print('^C', file=sys.stderr)
            pl = Pipeline(local)
            prompt = sys.ps1
            exitOnControlD = True
            continue
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
            for command in lineSplitter(text):
                if command == '%d':
                    pl.toggleDebug()
                    doPrint = False
                elif command == '%u':
                    pl.undo()
                elif command == '%r':
                    if exists(rc):
                        exec(open(rc).read(), local)
                        print('Reloaded.', file=sys.stderr)
                        doPrint = False
                    else:
                        print('pysh init file %r does not exist.' % rc,
                              file=sys.stderr)
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
                    except KeyboardInterrupt:
                        print('^C', file=sys.stderr)
                        pl = Pipeline(local)
                        prompt = sys.ps1
                        break
                    except Exception as e:
                        print(e, file=sys.stderr)
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
