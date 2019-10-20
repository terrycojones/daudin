## Daudin - a Python command-line shell

`daudin` is a UNIX command-line shell based on Python.

The aim is to provide an interactive shell that is as convenient to use as
the regular shell (in particular providing pipelines) but which has Python
as its programming language.

Contents:
<a href="#installation">Installation</a> &middot;
<a href="#usage">Usage</a> &middot;
<a href="#examples">Examples</a> &middot;
<a href="#pipelines">Pipelines</a> &middot;
<a href="#cd">Changing directory</a> &middot;
<a href="#command-substitution">Command substitution</a> &middot;
<a href="#readline">Readline</a> &middot;
<a href="#init-file">Init file</a> &middot;
<a href="#prompts">Prompts</a> &middot;
<a href="#more-usage">More on usage</a> &middot;
<a href="#exiting">Exiting</a> &middot;
<a href="#command-interpretation">Command interpretation</a> &middot;
<a href="#pipeline-python-execution">Pipeline execution</a> &middot;
<a href="#shell-execution">Shell execution</a> &middot;
<a href="#debugging">Debugging</s> &middot;
<a href="#version">Version</a> &middot;
<a href="#background">Background</a> &middot;
<a href="#todo">TODO</a>.


<a id="installation"></a>
## Installation

```sh
$ pip install daudin
```

<a id="usage"></a>
## Usage

Run `daudin` and enter commands interactively.

Should run fine on a recent version of Python 3 (I am using 3.7.3).

<a id="examples"></a>
### Examples

The following examples all assume you have already run `daudin` (which
prints the `>>>` prompt).

Like a regular shell, you have direct access to UNIX tools:

```sh
>>> ls -l
total 44
-rw-r--r-- 1 terry terry   635 Oct 12 17:34 Makefile
-rw-rw-r-- 1 terry terry 16619 Oct 12 23:05 README.md
-rwxrwxr-x 1 terry terry  1261 Oct 12 22:42 daudin
drwxrwxr-x 3 terry terry  4096 Oct 12 22:51 daudinlib
-rw-rw-r-- 1 terry terry  2309 Oct 12 23:05 example-functions.py
-rw-r--r-- 1 terry terry  1546 Oct 12 17:43 setup.py
drwxrwxr-x 3 terry terry  4096 Oct 12 22:48 test
>>> ls | wc -l
7
>>> echo hello there > /tmp/xxx
>>> cat /tmp/xxx
hello there
```

(If regular shell commands are slow to execute, it's probably because your
regular shell is slow to start. Change the default underlying shell used by
`daudin` to something faster, as described <a
href="#shell-execution">below</a>.)

But in fact it's Python all the way down:

```python
>>> from math import pi
>>> pi
3.141592653589793
>>> def area(r):
...   return r ** 2 * pi
...
>>> area(2.0)
12.566370614359172
```

<a id="pipelines"></a>
## Pipelines

Shell pipelines are super cool. As you've seen above `daudin`, has
pipelines that look just like the shell. But there are a few added extras.

You can mix Python and the shell in a `daudin` pipeline:

```
>>> import this | grep 'better than'
Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
Flat is better than nested.
Sparse is better than dense.
Now is better than never.
Although never is often better than *right* now.
```

In Python commands in a `daudin` pipeline, the current pipeline value is
kept in a variable named `_`, which may be of any type:

```python
>>> -6 | abs(_) | _ * 7
42
>>> 'hello' | _.title()
Hello
```

UNIX commands produce lists of strings in `_`:

```python
>>> ls | for name in _:
...   prefix = name.split('.')[0]
...   print(len(prefix), prefix.upper())
...
8 MAKEFILE
6 README
6 DAUDIN
9 DAUDINLIB
17 EXAMPLE-FUNCTIONS
5 SETUP
4 TEST
```

That means you should use `_[0]` if you want to act on just the first line
of UNIX command output:

```python
>>> def triple(x):
...   return int(x) * 3
...
>>> echo a b c | wc -w | triple(_[0])
9
```

Here's the same thing, but with `cat` reading from the terminal:

```python
>>> def triple(x):
...   return int(x) * 3
...
>>> cat | wc -w | triple(_[0])
a b c
^D
9
```

You can really mix things up (UNIX, Python, UNIX, Python):

```python
>>> seq 0 9 | map(lambda x: 2 ** int(x), _) | sum(_)
1023
>>> seq 0 9 | list(map(lambda x: 2 ** int(x), _)) | tee /tmp/powers-of-two | sum(map(int, _))
1023
>>> cat /tmp/powers-of-two
1
2
4
8
16
32
64
128
256
512
```

You can hit ENTER in the middle of a pipeline without disrupting it. So
this:

```python
>>> echo a b c | wc -w
3
```

is equivalent to this

```python
>>> echo a b c |
>>> wc -w
3
```

And if you forget to end a pipeline command-line with a `|` you can just
put one at the start of the next line to continue the pipeline:

```python
>>> echo a b c
a b c
>>> | wc -w
3
```

If you need to write a helper function in the middle of the pipeline before
continuing processing, you can do it:

```python
>>> def triple(x):
...   # Doesn't use int() to convert its argument.
...   return x * 3
...
>>> echo a b c | wc -w
3
>>> f = lambda line: int(line[0])
>>> | f(_) | triple(_)
9
```

Similarly, you can change directories in the middle of a pipeline (see
<a href="#cd">Changing directory</a> below).

You can put comments into the middle of a pipeline

```python
>>> ls -1
Makefile
README.md
daudin
daudinlib
setup.py
test
>>> # The pipeline is still alive!
>>> _
['Makefile', 'README.md', 'daudin', 'daudinlib', 'setup.py', 'test']
>>> | wc -l
6
```

You can also pipe the output of a multi-line Python command directly into
a following command:

```python
>>> ls | for name in _:
...   prefix = name.split('.')[0]
...   print(len(prefix), prefix.upper()) | | sort
17 EXAMPLE-FUNCTIONS
4 TEST
5 SETUP
6 DAUDIN
6 README
7 LICENSE
8 MAKEFILE
9 CHANGELOG
9 DAUDINLIB
```

There are two `|` symbols before the `sort` above because an empty command
is necessary to terminate the compound Python command.

The output above should have been numerically sorted. The pipeline can be
immediately continued using a leading `|`:

```python
>>> | sort -n
4 TEST
5 SETUP
6 DAUDIN
6 README
7 LICENSE
8 MAKEFILE
9 CHANGELOG
9 DAUDINLIB
17 EXAMPLE-FUNCTIONS
```

Here's another example where two `|` symbols can be used to terminate the
Python command in order to continue the pipeline on a single line:

```python
>>> ls | for i in _: print(i[:3]) | | wc -l
11
```

The above could instead be piped into the
[sus](https://github.com/terrycojones/daudin/blob/master/example-functions.py#L40)
function I have in my `~/.daudin.py` file (see <a href="#init-file">Init
file</a> for details on this).  The `sus` Python function does the
equivalent of the shell `sort | uniq -c | sort -nr` trick for finding the
most common inputs:

```python
>>> ls | for i in _: print(i[:3]) | | sus()
3 dau
1 CHA
1 LIC
1 Mak
1 REA
1 dis
1 exa
1 set
1 tes
```

Just to repeat: the `||` provides an empty command (the zero-length string
between the pipe symbols) to terminate the Python `for` block. The space
between the two pipe symbols is optional.

### Undo in a pipeline

If you run a command that alters the pipeline content and you want to
restore it to its former value, you can undo with `%u`.

There is only a single undo at the moment. This could obviously be
improved, and a redo command could be added.

You can of course always save the current pipeline value into a Python
variable:

```python
>>> echo a b c
>>> a = _
```

<a id="cd"></a>
## Changing directory

Changing directory has to be handled a little specially because although a
`cd` command can be handed off to a shell, the change of directory in that
shell will have no effect on your current process. That's why `cd` has to
be a special "built-in" command in regular shells.

In `daudin` you can change dir using regular Python:

```python
>>> import os
>>> os.chdir('/tmp')
>>> pwd
/tmp
```

but that's far too laborious for interactive use.  So there's a `cd`
function provided for you:

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

Changing directory does not affect the current pipeline value.  So you can
change directory in the middle of a pipeline:

```python
>>> mkdir /tmp/a /tmp/b
>>> %cd /tmp/a
>>> touch x y z
>>> ls | %cd /tmp/b | for i in _:
...   with open(i + '.txt', 'w') as fp:
...     print('I am file', i, file=fp)
>>> pwd
/tmp/b
>>> cat x.txt
I am file x
```

<a id="command-substitution"></a>
## Command substitution

In regular shells there is a way to have part of a command line executed in
a sub-shell and the output of that sub-shell replaces that part of the
original command.

For example, suppose you want to get the value of `date` into a variable.
In the [bash](https://en.wikipedia.org/wiki/Bash_(Unix_shell)) shell you
could do this:

```sh
$ d=$(date)
$ echo $d
Sat Oct  5 22:36:24 CEST 2019
```

In `daudin` there is a `sh` function that you can use to pass commands to a
sub-shell. So, equivalently:

```python
>>> d = sh('date')
>>> d
Sat Oct  5 22:36:24 CEST 2019
```

If you then wanted to extract the month from the `date` output, in the
shell you could do this:

```sh
# Working from the d variable set above:
$ month=$(echo $d | cut -f2 -d' ')
# Or you could call date again:
$ month=$(date | cut -f2 -d' ')
$ echo $month
Oct
```

Same thing in `daudin`:

```python
# Working from the d variable set above:
>>> month = d.split()[1]
# Calling date again:
>>> month = sh('date').split()[1]
>>> month
Oct
```

You could also have the shell do all the work via `sh()` but to do that
you'll need to use `\|` in the to ensure that `daudin` doesn't incorrectly
split the shell command into two pieces:

```python
>>> month = sh('date \| cut -f2 -d" "')
```

<a id="readline"></a>
## Readline

`daudin` uses the [GNU](https://www.gnu.org/)
[readline](https://docs.python.org/3/library/readline.html) library to make
it easy to edit and re-enter commands. The history is stored in
`~/.daudin_history`.

`daudin` provides file and directory name completion, as well as Python
completion (the latter using
[rlcompleter](https://docs.python.org/3.8/library/rlcompleter.html)).

<a id="init-file"></a>
## Init file

`daudin` will initially read and execute code in a `~/.daudin.py` file, if
any. This is a good place to put convenience functions you write that you
want readily accessible. The file
[example-functions.py](example-functions.py) has some functions that give a
flavor of how you can add functionality to `daudin`. I have all these in my
`~/.daudin.py` file.

Use the `--noInit` argument when invoking `daudin` to disable loading the
init file.

Use the special `%r` (reload) command to re-read your init file.

<a id="prompts"></a>
## Changing prompts

There are `--ps1` and `--ps2` options that can be given on the command line
to `daudin`. You can also set `sys.ps1` or `sys.ps2` while running:

```python
>>> sys.ps1 = '% '
% 3 + 4
7
```

You can also set `sys.ps1` or `sys.ps2` to be a function that returns a
string. In the [example-functions.py](example-functions.py) file mentioned
above, you can see `sys.ps1` assigned to a simple function returning a
string containing the basename of the current working directory (or `~` if
you are in your home directory) plus the name of the current `git` branch
(if any). The string also contains escape sequences to color the prompt.
This is all extremely simplistic and for now is just an example. It would
make sense to port a more sophisticated prompt package from a shell to
Python and incorporate that.

<a id="more-usage"></a>
## More on usage

As you've seen, you can simply invoke `daudin` with no arguments and it
will start an interactive read-eval-print loop, reading from standard
input.

You can also write scripts and run them by giving the script filename(s) on
the command line:

```sh
$ cat daudin-script
#!/usr/bin/env daudin

def triple(x):
    return int(x) * 3

echo a b c d | wc -w | triple(_[0])
```

```sh
$ daudin daudin-script
12
```

You can provide several script filenames on the command line and they will
be run in turn. If you give a filename of `-` it will cause `daudin` to
read from standard input. Note that if you provide filenames, input piped
into `daudin` will be ignored (to read standard input, use a `-` as just
mentioned).

Finally, you can pipe commands into `daudin`:

```sh
$ echo 33 + 34 | daudin
77
```

### Command-line options

`daudin` understands the following command-line options (run `daudin
--help` to see this):

    usage: daudin [-h] [--ps1 PS1] [--ps2 PS2] [--shell SHELL] [--noInit]
                  [--noPtys] [--debug] [--tracebacks]
                  [FILE [FILE ...]]

    A Python shell.

    positional arguments:
      FILE           A file of commands to run non-interactively. Use "-" to
                     indicate reading from standard input.

    optional arguments:
      -h, --help     show this help message and exit
      --ps1 PS1      The primary shell prompt. Note that this value will be
                     ignored if the user's init file (if any) sets sys.ps1.
      --ps2 PS2      The secondary shell prompt. Note that this value will be
                     ignored if the user's init file (if any) sets sys.ps2.
      --shell SHELL  The shell executable (and its initial argument(s)) that
                     should be used to execute UNIX commands. Default is
                     "$DAUDIN_SHELL" if DAUDIN_SHELL is set in your environment,
                     else "$SHELL -c" if SHELL is set in your environment, else
                     "/bin/sh -c".
      --noInit       Do not load the ~/.daudin.py start-up file.
      --noPtys       Do not run any shell commands in pseudo-ttys.
      --debug        Start in debug mode.
      --tracebacks   Print exception tracebacks (implies --debug).


<a id="exiting"></a>
## Exiting daudin

Just use control-d as you would in any other shell.  Or you can call a
Python builtin function `exit()` or `quit()`, or use `sys.exit()` (all of
which can be given an `int` exit status).

<a id="command-interpretation"></a>
## How commands are interpreted

`daudin` first tries to run a command with
[eval](https://docs.python.org/3/library/functions.html#eval).  If that
succeeds, the result becomes `_` for the next command. If `eval` fails,
[code.compile_command](https://docs.python.org/3/library/code.html#code.compile_command)
is used to try to compile the command. If a full command is found, it is
given to [exec](https://docs.python.org/3/library/functions.html#exec) to
execute.  If a partial command (e.g., the beginning of a function
definition or a dictionary or list etc.) is found, a secondary prompt
(`sys.ps2`) is printed.  If a command cannot be compiled or executed,
execution is attempted via the shell (`/bin/sh`) using
[subprocess](https://docs.python.org/3.7/library/subprocess.html). The
current `_` is provided to the shell on standard input.  The output of the
shell command, if any, is converted to a Python `list` of strings (though
`daudin` initially prints this as a single string for the user). The list
of strings becomes the next `_`. If the shell command produces no output,
`_` is set to `[]` for the next command (a value of `None` could be used
instead, but it's more consistent to have all shell commands return a list
of strings, even if empty).

If a command returns a value (or if `None` is returned but the command
prints something) that value becomes the new pipeline value:

```python
>>> 4
4
>>> _
4
>>> [3, 6, 9]
[3, 6, 9]
>>> print('hello')
hello
>>> echo hello too
hello too
# This echo command actually returns a list of one string, and that is the
# value that _ is set to.  But, as mentioned above, when daudin first
# prints the output from the shell command the lines are joined with '\n'.
>>> _
['hello too']
```

### Shortcoming

Although the above works well almost all the time, it is not perfect. In
particular it is possible that you enter a valid Python expression but that
`eval` and `exec` cannot run it (e.g., `len(None)`). In that case the
command is fed to the shell, which results in an error similar to

```python
>>> len(None)
/bin/sh: 1: Syntax error: word unexpected (expecting ")")
```

You can turn on debugging via the special `%d` command (<a
href="#debugging">see below for more detail</a>) to dig into what happened:

```python
>>> %d
>>> len(None)
                    Processing 'len(None)'.
                    Not in pipeline.
                    Trying eval 'len(None)'.
                    Could not eval: object of type 'NoneType' has no len().
                    Trying to compile 'len(None)'.
                    Command compiled OK.
                    Could not exec: object of type 'NoneType' has no len().
                    Trying shell 'len(None)' with stdin None.
                    In _shPty, stdin is None
/bin/sh: 1: Syntax error: word unexpected (expecting ")")
                    Shell returned '/bin/sh: 1: Syntax error: word unexpected (expecting ")")\n'
```

<a id="pipeline-python-execution"></a>
## Pipeline Python execution environment

When a Python command is run, it has access to the following:

* `cd` - a function for changing directory.
* `sh` - a function for running a shell command.
* `self` - the instance of `daudinlib.pipeline.Pipeline`. This allows full
  access to the internals of the running `daudin` shell. So you can do
  things like `self.debug = True`, and anything else you can think of.

In addition, the variables or functions you define or `import` in your
`~/.daudin.py` are also present.

<a id="shell-execution"></a>
## Shell execution environment

By default, `daudin` will use your `SHELL` environment variable (with a
`-c` argument) as the shell to execute non-Python commands with. You can
specify another shell on the command line via the `--shell` argument, e.g.,

```sh
$ daudin --shell '/bin/bash -c'
```

or by setting an environment variable, `DAUDIN_SHELL` to a value such as
`/bin/bash -c`.  If you normally use a shell with slow start-up, and invoke
`daudin` from that shell, you will certainly want to use one of these
options to set the shell that `daudin` uses, otherwise shell commands
executed by `daudin` will all be slow.

You can also change the shell in use during a `daudin` session:

```python
>>> self.shell = ['/bin/bash', '-c']
>>> echo $BASH_VERSION
5.0.3(1)-release
>>> echo testing-{1,2,3}
testing-1 testing-2 testing-3
>>> for i in testing-{1,2,3}; do echo $i; done
testing-1
testing-2
testing-3

>>> self.shell = ['/bin/zsh', '-c']
>>> echo $ZSH_VERSION
5.5.1
>>> echo {2015..2019}
2015 2016 2017 2018 2019
>>> foreach i (testing-{1,2,3}); do echo $i; done
testing-1
testing-2
testing-3

>>> self.shell = ['/usr/local/bin/fish', '-c']
>>> # Slow!!
>>> echo $FISH_VERSION
3.0.0
>>> echo testing-{1,2,3}
testing-1 testing-2 testing-3

>>> self.shell = ['/bin/sh', '-c']
>>> echo testing-{1,2,3}
testing-{1,2,3}
```

Note that this shell is only used by `daudin` when it encounters shell
commands on a command line, not when you use the built-in `sh` command.
When using `sh`, you can provide whatever arguments you like, either as a
string or a list of strings, to be passed to `subprocess.run` (or
`subprocess.Pipe` in the case of a pseudotty - see below).

### Pseudottys

When a shell command is the final command on a line, it is run in a
[pseudotty](https://en.wikipedia.org/wiki/Pseudoterminal). So commands that
check to see if they're running with standard output connected to a
terminal will think they are. In that case, a command like `git status` or
`ls --color=auto` will produce colored output that will be correctly
displayed.

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

For more information you can enable printing of tracebacks via the `%t`
special command.

There are `--debug` and `--tracebacks` command-line options that can be
given on `daudin` invocation to immediately enable debugging and traceback
printing.

<a id="special-commands"></a>
## Special commands

All special `%` commands have been described above, but here's list of them
in one place for reference:

* `%cd` - change directory.
* `%d` - toggle debug output.
* `%r` - reload init file.
* `%t` - toggle traceback output (also turns on debugging output).
* `%u` - undo the last change to the `_` pipeline variable.

It's worth pointing out that none of these special commands is actually
needed. They're just syntactic sugar to make some actions easier. Their
effects can all be achieved using regular Python inside `daudin` (usually
via `self`), if you know what you're doing.

<a id="version"></a>
## Version

To get the `daudin` version:

```python
>>> import daudinlib
>>> daudinlib.__version__
0.0.7
```

<a id="background"></a>
## Background & thanks

Daudin is the surname of
[François Marie Daudin](https://en.wikipedia.org/wiki/Fran%C3%A7ois_Marie_Daudin),
a prolific French zoologist who in 1826 gave the name "Python", to a genus
in the [Pythonidae](https://en.wikipedia.org/wiki/Pythonidae) family.
Pythonidae in turn is a member of the wonderfully named superfamily,
[Pythonoidea](https://en.wikipedia.org/wiki/Pythonoidea).

I wrote `daudin` on the evening of Oct 4, 2019 following a discussion about
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
the context of a stack, not the shell.  I also wrote
[pystdin](https://github.com/terrycojones/pystdin) to allow you to easily
process standard input in Python, without having to do so much typing.

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
version was about 280 lines of code and could be written in one evening.
The code is still quite ugly and brittle (only a few tests and various
exceptions are either not handled as well as they could be or may even
cause `daudin` to exit). But it works fine as an initial proof of concept.

I find it interesting to note that it feels like `daudin` generalizes my
RPN calculator and `pystdin` (both mentioned above).

I'm going to try using `daudin` for real and see what kinds of additional
helper functions I end up adding and how things go in general.  It's easy
to imagine some things, like a smart `cd` command (I've written quite a few
shell `cd` commands over the years, including a client-server one :-)). The
prompt could be a function. Many things could be done with history. Etc.

Thanks for reading, and thanks Derek & Nelson.

Terry Jones (@terrycojones)<br>
terry@jon.es

<a id="todo"></a>
## TODO

Here are some concrete things I'd like to (possibly) add

* Just have one sub-shell and send commands to it instead of forking a new
  one for each command. That would allow persistent shell variables. `cd`
  commands could be run simultaneously in both shells.
* Add some way to deal with standard error?
* Some of what might also be wanted in a pipeline with `_` can be done with tee.
* Make it so code can return `IGNORE` to explicitly preserve the pipeline.
* Guess at auto-indent level for incomplete commands.
* Add a specially-named function that (if defined) is used to produce the
  prompt.
* Add a specially-named function that (if defined) run after each command
  (or command-line).
* Add variable export.
