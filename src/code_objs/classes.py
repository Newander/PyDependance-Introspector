import typing as t
from functools import partial

from src.code_objs.callables import Obj, object_parser
from src.code_objs.functions import Function
from src.code_objs.line import CodeLine


class Class(Obj):
    """ Representation of the Python Class """

    def __init__(self, name: str, module_import_path: str, body: t.List['CodeLine']):
        super(Class, self).__init__(name, module_import_path, body)

        self.magic_methods: t.List[Function] = []
        self.methods: t.List[Function] = []

        functions: t.List[Function] = []
        i_body = iter(body)
        fun_handler = partial(
            Function.handler, functions=functions, abs_module_import_path=self.path
        )

        while True:
            try:
                object_parser(i_body, fun_handler, Function.condition)
            except StopIteration:
                break

        for fun in functions:
            if fun.name.count('__') > 1:
                self.magic_methods.append(fun)
            else:
                self.methods.append(fun)

        del functions

    @classmethod
    def parse_name(cls, def_line):
        class_name = def_line.split()[1]
        idx = max((class_name.find(':'), class_name.find('(')))
        return class_name[:idx]
