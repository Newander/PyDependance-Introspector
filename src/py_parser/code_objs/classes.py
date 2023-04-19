import typing as t

from src.py_parser.code_objs.callables import CodeObject
from src.py_parser.code_objs.functions import Function
from src.py_parser.code_objs.line import ClassLine, CodeLine, FunctionLine


class Class(CodeObject):
    """ Representation of the Python Class """
    magic_method_names = [meth for meth in dir(type) if meth.count('__') > 1]

    def __init__(self, name: str, module_import_path: str, body: t.List['CodeLine']):
        super(Class, self).__init__(name, module_import_path, body)

        self.magic_methods: t.List[Function] = []
        self.methods: t.List[Function] = []

        functions: t.List[Function] = []

        line_iter = iter(body)
        while True:
            try:
                cline = next(line_iter)
            except StopIteration:
                break

            if isinstance(cline, FunctionLine):
                cls, end_line = Function.parse(cline, line_iter, self.path)
                functions.append(cls)

        for fun in functions:
            if fun.name in self.magic_method_names:
                self.magic_methods.append(fun)
            else:
                self.methods.append(fun)

        del functions

    @classmethod
    def parse_name(cls, def_line: 'ClassLine'):
        try:
            _, class_name = def_line.code_line.split(maxsplit=1)
        except IndexError as err:
            raise err

        if not isinstance(class_name, str):
            raise ValueError(def_line.code_line)

        idx = min((class_name.find(':'), class_name.find('(')))
        return class_name[:idx]
