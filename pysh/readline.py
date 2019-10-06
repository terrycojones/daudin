import readline
import os


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
