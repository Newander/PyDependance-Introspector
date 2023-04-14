from typing import Iterator

from src.code_objs.callables import CodeObject
from src.code_objs.line import FunctionLine
from src.code_objs.line import VariableLine


class Variable(CodeObject):
    """ Represent in-variable line
    """

    @classmethod
    def handler(cls, line: str, iterator: Iterator, abs_module_import_path: str, functions: list):
        fun, end_line = cls.parse(line, iterator, abs_module_import_path)

        if fun:
            functions.append(fun)

        return end_line

    @staticmethod
    def condition(parsed):
        return all(['def' == parsed[0], 'self' not in parsed[1]])

    @classmethod
    def parse_name(cls, def_line: 'VariableLine'):
        name = def_line.code_line.split('=', maxsplit=1)[0].strip()
        return name
