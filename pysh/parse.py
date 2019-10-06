import re

_unescapedPipeRegex = re.compile(r'(?<!\\)\|')


def lineSplitter(line):
    start = 0
    for match in _unescapedPipeRegex.finditer(line):
        command = line[start:match.start()].replace(r'\|', '|')
        if command:
            yield command
        start = match.end()

    command = line[start:].replace(r'\|', '|')
    if command:
        yield command
