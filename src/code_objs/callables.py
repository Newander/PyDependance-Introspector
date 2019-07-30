import typing as t

from src.code_objs.line import CodeLine


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
