from dataclasses import dataclass
from typing import Iterator

from src.sql_parser.config import skips, spaces


@dataclass
class Template:
    raw: str
    regex: str
    variable_names: list[str]

    def __hash__(self):
        return hash(repr(self))


def parser(string: str) -> Iterator[str]:
    """ Correctly parse SQL script into semantic separate objects """
    word = ''
    for s1 in string:
        if s1 in skips:
            # opening the caveats
            if word:
                yield word
                word = ''
            if s1 not in spaces:
                yield s1
        else:
            word += s1

    if word:
        yield word


def variables_extractor(template_str: str) -> Template:
    """ Correctly extract variables [{...}] from table name and return the resulting model """
    var = ''
    variables = []
    regex = '^'
    adding = False
    for s1 in template_str:
        if s1 == '{':
            # opening the caveats
            adding = True
            regex += var
            var = ''
        elif s1 == '}':
            adding = False
            variables.append(var)
            var = ''
            regex += '.*'
        elif adding:
            if s1 == '{':
                raise ValueError(f'Interesting {s1=} {template_str=}')
            var += s1
        else:
            var += s1

    if var:
        if adding:
            variables.append(var)
            regex += '.*'
        else:
            regex += var

    return Template(template_str, regex + '$', variables)


def extract_between_curves(iter_query: Iterator[str]) -> list[str]:
    """ The with condition must start with [select] operand """
    curves_stack = '('
    result = [curves_stack]
    for word in iter_query:
        result.append(word)

        if word == '(':
            curves_stack += '('
        elif word == ')':
            if len(curves_stack) == 1:
                break
            elif curves_stack[-1] == ')':
                raise Exception(result + [word])
            else:
                curves_stack = curves_stack[:-1]

    return result


def fill_dot_with_nulls(args_num: int, field_name: str) -> list[str | None]:
    """ Trying to extract many-parted argument """
    if '(' not in field_name:
        parsed = field_name.split('.')
    else:
        parsed = [field_name]

    return [
        *([None] * (args_num - len(parsed))),
        *parsed
    ]
