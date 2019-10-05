## Pysh - a Python command-line shell

Here is a script, `pysh.py`, providing a UNIX command-line shell based on
Python.

## Aim

Provide a Python shell that is at once as convenient to use as the regular
shell (in particular providing pipelines) but which uses Python as its
programming language.

## Usage

Just run `pysh.py` and enter commands interactively.

### Examples

It looks like a regular shell:

```sh
$ pysh.py
>>> ls -l
total 16
-rw-rw-r-- 1 terry terry   350 Oct  5 13:06 README.md
-rwxrwxr-x 1 terry terry 10422 Oct  5 13:03 pysh.py
>>> ls -l | wc -l
3
```

But in fact it's Python all the way down:

```sh
$ pysh.py
>>> ls | for i in sys.stdin:
...   print(len(i))
...
9
7
```

In the further examples on this page, the invocation of `pysh.py` is
omitted.

You can see you really do have full Python:

```sh
>>> def triple(x):
...   return int(x) * 3
...
>>> echo a b c | wc -w | triple(sys.stdin[0])
9
```

(The `[0]` in the above is needed because shell commands always return a
list of strings.)

And you have the shell too:

```sh
>>> def triple(x):
...   return int(x) * 3
...
>>> cat | wc -w | triple(sys.stdin[0])
a b c
^D
9
```

in the above, the `cat` is reading from the terminal, as normal.

## Pipelines

Shell pipelines are super cool. So in `pysh` you're *always* in a pipeline.
The current pipeline value is kept in `sys.stdin`:

```python
>>> -6 | abs(sys.stdin) | sys.stdin * 6
36
```

The current pipeline value is also available in the special variable `_` as
a convenience:

```python
>>> -6 | abs(_) | _ * 6
36
```

### Exiting a pipeline

Just enter control-D as you normally would to end input. The current
pipeline value will then be printed (unless it has just been printed
because you hit ENTER).  A new pipeline is immediately started.

### Undo in a pipeline

If you run a command that alters the pipeline content and you want to
restore it to its former value, you can undo with `%u`.

There is only a single undo at the moment. This can obviously be improved,
and a redo command could be added.

## Readline

`pysh` uses the [GNU](https://www.gnu.org/)
[readline](https://docs.python.org/3/library/readline.html) library
to make it easy to edit and re-enter commands.

The `pysh` history is stored in `~/.pysh_history`.

## Startup file

`pysh` will read and execute code in a `~/.pysh.py` file, if any. This is a
good place to put convenience functions you write that you want readily
accessible. See examples <a href="#functions">below</a>.

Use the special `%r` (reload) command to re-read your startup file.

## Exiting pysh

In most shells, a control-D exits. But in `pysh` it terminates the current
pipeline. If you immediately give a second control-D, `pysh`
will exit completely.

You can also just call the Python builtin function `quit()` or use
`sys.exit()` (both of which can be given an `int` exit status).

## How commands are interpreted

`pysh` first tries to run a command with
[eval](https://docs.python.org/3/library/functions.html#eval).  If that
succeeds, the result becomes `sys.stdin` for the next command. If `eval`
fails,
[code.compile_command](https://docs.python.org/3/library/code.html#code.compile_command)
is used to try to compile the command. If a full command is found, it is
given to [exec](https://docs.python.org/3/library/functions.html#exec) to
execute.  If a partial command (e.g., the beginning of a function
definition or a dictionary or list etc.), a secondary prompt (`sys.ps2`) is
printed.  If a command cannot be compiled or executed, execution is
attempted via the shell using
[subprocess](https://docs.python.org/3.7/library/subprocess.html). The
current `sys.stdin` is given to the shell.  The output of the shell
command, if any, is converted to a Python `list` of strings (though `pysh`
initially prints it as a single string). The list of strings becomes the
next `sys.stdin`. If the shell command produces no output, `sys.stdin` is
set to `[]` for the next command (arguably a value of `None` could be used
instead, but it's more consistent to have all shell commands return a list
of strings, even if empty).

## Changing directory

Changing directory has to be handled a little specially because although a
`cd` command can be handed off to a shell, the change of directory in that
shell will have no effect on your current process. That's why `cd` has to
be a special "built-in" command in regular shells.

In `pysh` you can change dir using regular Python:

```sh
>>> import os
>>> os.chdir('/tmp')
>>> pwd
/tmp
```

but that's a bit laborious.  So there's a `cd` function provided for you:

```sh
>>> cd('/tmp')
>>> pwd
/tmp
```

To ease this, at the price of a litle ugliness, there's also a "built-in"
special command called `%cd`:

```sh
>>> %cd /tmp
>>> pwd
/tmp
```

*Warning*: I don't really like these special commands! `pysh` is 99.9% pure
Python and doesn't absolutely require these kinds of hacks (which in this
case actually break some infrequently used syntax, such as entering a
multi-line value using Python's `%` operator if you happen to have a
variable called `cd` defined). So I may remove it entirely.
But... changing directory is rather common, so I'm not sure.

Importantly, changing directory does not affect the current pipeline value.
So you can change directory in the middle of a pipeline:

```sh
$ pysh.py
>>> mkdir /tmp/a /tmp/b
>>> cd('/tmp/a')
>>> touch x y z
>>> ls
x
y
z
>>> cd('/tmp/b')
>>> for i in _:
...   with open(i + '.txt', 'w') as fp:
...     print('I am file', i, file=fp)
...
>>> cat x.txt
I am file x
```

## Changing prompt

Just set `sys.ps1` or `sys.ps2`:

```sh
>>> sys.ps1 = '$ '
$ 3 + 4
7
```

## Debugging

To turn on debugging output, set `self.debug` to a true value:

```sh
>>> self.debug = 1
>>> 4
                    Processing '4'.
                    Trying eval '4'
                    Eval -> 4
4
```

or run `self.toggleDebug`.


<a id="functions"></a>
## Functions

Here are some functions I wrote to give a flavor of what you can do and how
to do it.

```python
import sys
from operator import itemgetter
from collections import defaultdict

from pprint import pprint


def pp():
    "Pretty print standard input"
    pprint(sys.stdin)
    return sys.stdin


def sus(n=None, print_=True):
    """Perform the shell equivalent of sort | uniq -c | sort -n -r

    @param n: The C{int} maximum number of items to return.
    @param print_: If C{True}, output is printed. Else a C{list} of
        C{(count, word)} C{tuple}s is returned (thus becoming the value of
        C{sys.stdin} that will be available to the next pipeline command)
    """
    lines = defaultdict(int)

    for line in sys.stdin:
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
    "Get the last line of a list of lines (shell output)."
    return sys.stdin[-1]


def fl():
    "Get the first line of a list of lines (shell output)."
    return sys.stdin[0]


def push(*args):
    "Treat sys.stdin as a stack (a list) and push args onto it."
    if isinstance(sys.stdin, list):
        sys.stdin.extend(args)
        return sys.stdin
    else:
        return [sys.stdin] + list(args)


def pop():
    "Treating sys.stdin as a stack (a list), pop & print the top of the stack."
    print(sys.stdin.pop(), file=sys.stderr)
    return sys.stdin


def clear():
    "Treating sys.stdin as a stack (a list), clear the stack."
    return []


def apply(n=None):
    """Treating sys.stdin as a stack (a list), pop a function from the top of
       the stack and apply it to a given number of arguments"""
    if sys.stdin:
        if n is not None:
            if len(sys.stdin) < n + 1:
                print('Could not apply - not enough stack items',
                      file=sys.stderr)
            else:
                func = sys.stdin.pop()
                args = reversed(sys.stdin[-n:])
        else:
            func = sys.stdin.pop()
            args = reversed(sys.stdin)
        return func(*args)
    else:
        print('Empty stack!', file=sys.stderr)
        return sys.stdin
```
