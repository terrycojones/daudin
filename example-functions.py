import sys
from operator import itemgetter
from collections import defaultdict

from math import pi, e

from os import getcwd

from pprint import pprint


def pp():
    "Pretty print the current pipeline value."
    pprint(_)
    return _


def sus(n=None, print_=True):
    """Perform the shell equivalent of sort | uniq -c | sort -n -r

    @param n: The C{int} maximum number of items to return.
    @param print_: If C{True}, output is printed. Else a C{list} of
        C{(count, word)} C{tuple}s is returned (thus becoming the value of
        C{_} that will be available to the next pipeline command)
    """
    lines = defaultdict(int)

    for line in _:
        lines[line] += 1

    it = enumerate(
        sorted(lines.items(), key=itemgetter(1), reverse=True), start=1)

    if print_:
        for i, (line, count) in it:
            print('%d %s' % (count, line))
            if n is not None and i >= n:
                break
    else:
        result = []
        for i, (line, count) in it:
            result.append((count, line))
            if n is not None and i >= n:
                break
        return result


def ll():
    "Get the last line of a list of lines (of shell output)."
    return _[-1]


def fl():
    "Get the first line of a list of lines (of shell output)."
    return _[0]


def push(*args):
    "Treat _ as a stack (a list) and push args onto it."
    if isinstance(_, list):
        _.extend(args)
        return _
    else:
        return [_] + list(args)


def pop():
    "Treating _ as a stack (a list), pop & print the top of the stack."
    print(_.pop(), file=sys.stderr)
    return _


def clear():
    "Treating _ as a stack (a list), clear the stack."
    return []


def apply(n=None):
    """Treating _ as a stack (a list), pop a function from the top of
       the stack and apply it to a given number of arguments"""
    if _:
        if n is not None:
            if len(_) < n + 1:
                print('Could not apply - not enough stack items',
                      file=sys.stderr)
            else:
                func = _.pop()
                args = reversed(_[-n:])
        else:
            func = _.pop()
            args = reversed(_)
        return func(*args)
    else:
        print('Empty stack!', file=sys.stderr)
        return _
