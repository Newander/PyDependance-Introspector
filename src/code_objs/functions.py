import typing as t

from src.code_objs.callables import CodeObject
from src.code_objs.line import FunctionLine


class Function(CodeObject):
    """ Representation of the Python Function
    todo: define is this a function or method
    """

    @staticmethod
    def handler(line: str, iterator: t.Iterator, abs_module_import_path: str, functions: t.List):
        fun, end_line = Function.parse(line, iterator, abs_module_import_path)

        if fun:
            functions.append(fun)

        return end_line

    @staticmethod
    def condition(parsed):
        return all(['def' == parsed[0], 'self' not in parsed[1]])

    @classmethod
    def parse_name(cls, def_line: 'FunctionLine'):
        fun_name = def_line.cline.split()[1]
        idx = fun_name.find('(')
        return fun_name[:idx]
