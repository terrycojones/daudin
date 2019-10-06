## Pysh - a Python command-line shell

Here is a script, `shell.py`, providing a UNIX command-line shell based on
Python.

## Aim

Provide a Python shell that is at once as convenient to use as the regular
shell (in particular providing pipelines) but which uses Python as its
programming language.

## Usage

Just run `shell.py` and enter commands interactively.

Should run fine on a modern Python (I am using 3.7.3) and will run with
some issues on Python 2.7 (please send me feedback, open issues, create
pull requests).

### Examples

The following all assume you have run `shell.py` (which prints the `>>>`
prompt in the examples).

Like a regular shell, you have immediate access to UNIX tools:

```python
>>> ls -l
total 16
-rw-rw-r-- 1 terry terry   350 Oct  5 13:06 README.md
-rwxrwxr-x 1 terry terry 10422 Oct  5 13:03 shell.py
>>> ls -l | wc -l
3
>>> echo hello there > /tmp/xxx
>>> cat /tmp/xxx
hello there
```

But in fact it's Python all the way down:

```python
>>> from math import pi
>>> def area(r):
...   return r ** 2 * pi
...
>>> area(2.0)
12.566370614359172
```

And you can seamlessly mix UNIX commands with Python:

```python
>>> ls | for i in sys.stdin:
...   print(len(i))
...
9
7
```

```python
>>> def triple(x):
...   return int(x) * 3
...
# The [0] in the following is needed because shell commands always return a
# list of strings.
>>> echo a b c | wc -w | triple(sys.stdin[0])
9
```

```python
>>> def triple(x):
...   return int(x) * 3
...
# In the following, cat reads from the terminal, as normal.
>>> cat | wc -w | triple(sys.stdin[0])
a b c
^D
9
```

```python
>>> import this | grep 'better than'
Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
Flat is better than nested.
Sparse is better than dense.
```


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

If you hit ENTER in the middle of a pipeline, the current value of
`sys.stdin` is printed (but the pipeline is still intact).  The pipeline
value is not shown in between running commands joined with the `|` pipe
symbol.

So this

```python
>>> ls | wc -l
2
```

is equivalent to this

```python
>>> ls
README.md
shell.py
# The pipeline is still present, with 2 strings in it.
>>> wc -l
2
```

except the latter prints the result of the `ls` because I hit ENTER between
the commands.

### Exiting a pipeline

Just enter control-D as you normally would to end input. The current
pipeline value will then be printed (unless it has just been printed
because you hit ENTER).  A new pipeline is immediately started.

### Undo in a pipeline

If you run a command that alters the pipeline content and you want to
restore it to its former value, you can undo with `%u`.

There is only a single undo at the moment. This can obviously be improved,
and a redo command could be added.

## Command substitution

In regular shells there is a way to have part of a command line executed in
a sub-shell and the output of that sub-shell replaces that part of the
original command.

For example, suppose you want to get the value of `date` into a variable.
In the Bash shell you could do this:

```sh
$ date=$(date)
$ echo date
Sat Oct  5 22:36:24 CEST 2019
```

In `pysh` there is a `sh` function that you can use to pass commands to a
sub-shell. So, equivalently:

```python
>>> date = sh('date')
>>> date
Sat Oct  5 22:36:24 CEST 2019
```

If you then wanted to extract the month from the `date` output, in the
shell you could do this:

```sh
# Working from the date variable set above:
$ month=$(echo $date | cut -f2 -d' ')
# Calling date again:
$ month=$(date | cut -f2 -d' ')
$ echo $month
Oct
```

Same thing in `pysh`:

```python
# Working from the date variable set above:
>>> month = date.split()[1]
# Calling date again:
>>> month = sh('date').split()[1]
# Using cut to have the shell do all the work (note the use of \| in the
# following to ensure that pysh doesn't incorrectly split the command
# into two pieces.
>>> month = sh('date \| cut -f2 -d" "')
```

## Readline

`pysh` uses the [GNU](https://www.gnu.org/)
[readline](https://docs.python.org/3/library/readline.html) library to make
it easy to edit and re-enter commands. The history is stored in
`~/.pysh_history`.

<a id="start-up"></a>
## Start-up file

`pysh` will initially read and execute code in a `~/.pysh.py` file, if
any. This is a good place to put convenience functions you write that you
want readily accessible. See examples <a href="#functions">below</a>.

Use the special `%r` (reload) command to re-read your start-up file.

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
definition or a dictionary or list etc.) is found, a secondary prompt
(`sys.ps2`) is printed.  If a command cannot be compiled or executed,
execution is attempted via the shell (`/bin/sh`) using
[subprocess](https://docs.python.org/3.7/library/subprocess.html). The
current `sys.stdin` is provided to the shell on standard input.  The output
of the shell command, if any, is converted to a Python `list` of strings
(though `pysh` initially prints this as a single string for the user). The
list of strings becomes the next `sys.stdin`. If the shell command produces
no output, `sys.stdin` is set to `[]` for the next command (a value of
`None` could be used instead, but it's more consistent to have all shell
commands return a list of strings, even if empty).

If a command returns a value (or if `None` is returned but the command
prints something) that value becomes the new pipeline value.

```python
>>> 4
4
>>> _
4
>>> [3, 6, 9]
[3, 6, 9]
>>> print('hello')
hello
>>> echo hello
hello
# Note that the echo command actually returns a list of strings, and that is
# the value that sys.stdin is set to.  But, as mentioned above, when pysh
# first prints the output from the shell command the lines are joined with \n.
>>> _
['hello']
```

### Shortcoming

Although the above works well almost all the time, it is not perfect. In
particular it is possible that you enter a valid Python expression but that
`eval` and `exec` cannot run it (e.g., `len(None)`). In that case the
command is fed to the shell, which results in an error similar to

```python
>>> len(None)
/bin/sh: 1: Syntax error: word unexpected (expecting ")")
Process error: Command 'len(None)' returned non-zero exit status 2.
None
```

You can turn on debugging (use the special `%d` command, described <a
href="#debugging">below</a>) to get some idea of what happened:

```python
>>> %d
>>> len(None)
                    Processing 'len(None)'.
                    Trying eval 'len(None)'.
                    Could not eval: object of type 'NoneType' has no len().
                    Trying to compile 'len(None)'.
                    Command compiled OK.
                    Could not exec: object of type 'NoneType' has no len().
/bin/sh: 1: Syntax error: word unexpected (expecting ")")
Process error: Command 'len(None)' returned non-zero exit status 2.
None
```


## Changing directory

Changing directory has to be handled a little specially because although a
`cd` command can be handed off to a shell, the change of directory in that
shell will have no effect on your current process. That's why `cd` has to
be a special "built-in" command in regular shells.

In `pysh` you can change dir using regular Python:

```python
>>> import os
>>> os.chdir('/tmp')
>>> pwd
/tmp
```

but that's a bit laborious.  So there's a `cd` function provided for you:

```python
>>> cd('/tmp')
>>> pwd
/tmp
```

To ease this, at the price of a litle ugliness, there's also a "built-in"
special command called `%cd`:

```python
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

```python
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

## Changing prompts

Just set `sys.ps1` or `sys.ps2`:

```python
>>> sys.ps1 = '% '
% 3 + 4
7
```

<a id="debugging"></s>
## Debugging

You can turn on debugging output using the special `%d` command, or set
`self.debug` to a true value:

```python
>>> self.debug = 1
>>> 4
                    Processing '4'.
                    Trying eval '4'.
                    Eval returned 4.
4
```

or run `self.toggleDebug()`.

<a id="functions"></a>
## Functions

Here are some functions I wrote to give a flavor of what you can do and how
to do it. These all live in my `~/.pysh.py` start-up file (described <a
href="#start-up">above</a>).

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


# The following functions (push, pop, clear, apply) show how you can use
# sys.stdin as a stack. You might never want to do that, but it illustrates
# how pysh pipelines can be used to implement a stack machine.

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

## Background & thanks

I wrote `pysh` on the evening of Oct 4, 2019 following a discussion about
shells with [Derek Smith](https://www.zoo.cam.ac.uk/directory/derek-smith)
after he overheard me talking to a student. I was saying how awesome the
shell is (really meaning its pipelines and the power you get from it
falling back onto external programs in `$PATH` when it encounters a
non-keyword).

Derek said he thinks the shell and having to use one in the first place
really sucks.  He asked two questions, illustrating his strong objections:

1. First, he asked why we have to program the shell in this archaic painful
   language when we use a completely different language to get our "real"
   work done. Why can't it all just be one language?

   I told him how I love pipelines and how natural they are. They are
   completely unlike what we normally do as programmers and that we somehow
   got used to. In "normal" programming you need to either a) nest
   functions inside-out (innermost is executed first) in a typical
   language, or b) use prefix syntax and nested inside-out functions as in
   [Lisp](https://en.wikipedia.org/wiki/Lisp_(programming_language)), or c)
   perhaps worst of all, push all your arguments onto a stack and then
   use postix, as in a
   [Reverse Polish Notation](https://en.wikipedia.org/wiki/Reverse_Polish_notation)
   (RPN) calculator or other stack-based language.

   Unlike in those other environments, in a shell pipeline you indicate
   what you want to get done in the "natural" (for many people)
   left-to-right order. You give arguments in a natural place. The shell
   takes care of making the data flow through the pipeline behind the
   scenes, hooking up standard input and output between successive
   commands.

   I mentioned an experimental new shell
   ([nushell](http://www.jonathanturner.org/2019/08/introducing-nushell.html))
   to Derek, that [Nelson Minar](https://twitter.com/nelson) had recently
   pointed me to. I told Derek how `nushell` lets structured data flow
   along the pipeline.

2. He gave an outraged snort and asked his second deadly question: but why
   structured data? Why can't a number, a string, a list, an object, a
   function (or even "structured data"), flow along the pipeline? Derek is
   a Lisp programmer, and has been for decades.  He's never seen a reason
   to move to any other programming environment. If you know about Lisp and
   its typical programming environment (not to mention the
   [Lisp Machine](https://en.wikipedia.org/wiki/Lisp_machine)) you can
   easily appreciate why.

I recently wrote
[a Python RPN calculator](https://github.com/terrycojones/rpnpy/) that lets
you put anything onto the stack and operate on it, so I've been thinking
about very general and syntactically easy use of Python like this, but in
the context of a stack, not the shell.

With Derek's two provocative questions burning brightly in my mind, I
started thinking about how to write a shell that was all Python, with the
elegance of shell pipelines (both conceptually and syntactically), and that
would allow anything to flow along the pipeline. And, for bonus points,
make it easy to use and seamlessly tie in to all the UNIX commands a
regular shell provides access to.

Once I had the basic idea of what to write, the code was pretty
straightforward to put together due to Python's strong support for parsing,
compiling, evaluating, and execing Python code and the nice
[subprocess](https://docs.python.org/3.7/library/subprocess.html)
library. The rest was just glue and a REPL loop.  An initial working
version was about 280 lines of code (now up to 384) and could be written in
one evening. The code is still quite ugly and brittle (no tests, various
exceptions will probably still cause `pysh` to exit). It's also not going
to be great at handling massive outputs.  But it works fine as an initial
proof of concept.

I'm going to try using `pysh` for real and see what kinds of additional
helper functions I end up adding and how things go in general.  It's easy
to imagine some things, like a smart `cd` command (I've written quite a few
shell `cd` commands over the years, including a client-server one :-)). The
prompt could be a function. Many things could be done with history. Etc.

Thanks for reading, and thanks Derek & Nelson.

Terry Jones (@terrycojones)<br>
terry@jon.es
