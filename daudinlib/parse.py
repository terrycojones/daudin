import re

_unescapedPipeRegex = re.compile(r'(?<!\\)\|')


def lineSplitter(line):
    start = 0
    for match in _unescapedPipeRegex.finditer(line):
        yield line[start:match.start()].replace(r'\|', '|')
        start = match.end()

    yield line[start:].replace(r'\|', '|')
