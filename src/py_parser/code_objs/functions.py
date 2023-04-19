from typing import Iterator

from src.py_parser.code_objs.callables import CodeObject
from src.py_parser.code_objs.line import FunctionLine


class Function(CodeObject):
    """ Representation of the Python Function
    todo: define is this a function or method
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
    def parse_name(cls, def_line: 'FunctionLine'):
        fun_name = def_line.code_line.split()[1]
        idx = fun_name.find('(')
        return fun_name[:idx]
