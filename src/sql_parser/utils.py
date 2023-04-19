from typing import Iterator

from src.sql_parser.config import skips, spaces


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
