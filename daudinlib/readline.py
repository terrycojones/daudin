import rlcompleter
import readline
import os
from itertools import count
import glob


class Completer:

    def __init__(self, local):
        self.local = local

    def complete(self, text, state):
        if state == 0:
            self.completions = []
            append = self.completions.append
            for path in glob.glob(text + '*'):
                if os.path.isdir(path):
                    if not path.endswith(os.sep):
                        path += os.sep
                else:
                    path += ' '
                append(path)

            pycompleter = rlcompleter.Completer(namespace=self.local).complete
            for i in count():
                completion = pycompleter(text, i)
                if completion is None:
                    break
                else:
                    append(completion)

        try:
            return self.completions[state]
        except IndexError:
            return None


def setupReadline(local):
    """Initialize the readline library and command history.

    @return: A C{bool} to indicate whether standard input is a terminal
        (and therefore interactive).
    """
    readline.parse_and_bind('tab: complete')
    readline.set_completer_delims(' \t\n')
    readline.set_completer(Completer(local).complete)

    # Readline code from https://docs.python.org/3.7/library/readline.html
    histfile = os.path.join(os.path.expanduser('~'), '.daudin_history')

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
