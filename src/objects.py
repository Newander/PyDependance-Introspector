import typing as t
from collections import UserString
from functools import partial


def object_parser(
        iterator: t.Iterator['CodeLine'],
        handler: t.Callable,
        condition: t.Callable
):
    end_line = None
    while True:
        try:
            if end_line is not None:
                line = end_line
                end_line = None
            else:
                line = next(iterator)

            parsed = list(line.split())

            if not parsed:
                continue  # skip empty lines

            if condition(parsed):
                end_line = handler(line, iterator)

        except StopIteration:
            break


class CodeLine(UserString):
    def __init__(self, string: str):
        super(CodeLine, self).__init__(string)

        self.indent = len(string) - len(string.lstrip(' '))


class Obj:
    def __init__(
            self, name: str, module_import_path: str, body: t.List['CodeLine']
    ):
        self.path = '.'.join([module_import_path, name])
        self.name = name
        self.body = body

    @classmethod
    def parse_name(cls, def_line):
        raise NotImplementedError

    @classmethod
    def parse(cls,
              def_line: 'CodeLine',
              file_lst: t.Iterable['CodeLine'],
              abs_module_import_path: str):
        """ Extracting all info about object into new instance """
        body = []
        name = cls.parse_name(def_line)

        line = None
        for line in file_lst:
            if line.indent == def_line.indent:
                break

            body.append(line)

        return cls(name, abs_module_import_path, body), line


class Function(Obj):
    """ Representation of the Python Function """

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
    def parse_name(cls, def_line):
        fun_name = def_line.split()[1]
        idx = fun_name.find('(')
        return fun_name[:idx]


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
