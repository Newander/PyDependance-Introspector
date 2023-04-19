from typing import Callable, Iterable, Iterator

from src.py_parser.code_objs.line import CodeLine, EmptyLine, LineType, ObjectLines


def object_parser(
        iterator: Iterator[CodeLine],
        handler: Callable,
        condition: Callable
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
            self, name: str, module_import_path: str, body: list[CodeLine | LineType]
    ):
        self.path = '.'.join([module_import_path, name])
        self.name = name
        self.body = body

    def __repr__(self):
        return f'{self.__class__.__name__} <{self.name}> in {self.path}'

    @classmethod
    def parse_name(cls, def_line):
        raise NotImplementedError

    @classmethod
    def parse(cls,
              code_line: ObjectLines,
              file_lst: Iterable[ObjectLines],
              abs_module_import_path: str):
        """ Extracting all info about object into new instance """
        body = []
        name = cls.parse_name(code_line)

        obj_line = None
        for obj_line in file_lst:
            if not isinstance(obj_line, EmptyLine) and \
                    obj_line.indent == code_line.indent:
                break

            body.append(obj_line)

        return cls(name, abs_module_import_path, body), obj_line
