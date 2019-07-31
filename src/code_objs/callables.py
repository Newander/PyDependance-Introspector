import typing as t

from src.code_objs.line import ClassLine, EmptyLine
from src.code_objs.line import CodeLine
from src.code_objs.line import FunctionLine


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


class CodeObject:
    def __init__(
            self, name: str, module_import_path: str, body: t.List['CodeLine']
    ):
        self.path = '.'.join([module_import_path, name])
        self.name = name
        self.body = body

    def __repr__(self):
        return f'{self.__class__.__name__} {self.name} at {self.path}'

    @classmethod
    def parse_name(cls, def_line):
        raise NotImplementedError

    @classmethod
    def parse(cls,
              def_line: 't.Union[ClassLine, FunctionLine, CodeLine]',
              file_lst: 't.Iterable[t.Union[ClassLine, FunctionLine, CodeLine]]',
              abs_module_import_path: str):
        """ Extracting all info about object into new instance """
        body = []
        name = cls.parse_name(def_line)

        mline = None
        for mline in file_lst:
            if not isinstance(mline, EmptyLine) and \
                    mline.indent == def_line.indent:
                break

            body.append(mline)

        return cls(name, abs_module_import_path, body), mline
