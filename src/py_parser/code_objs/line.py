from abc import ABC
from collections import UserString
from dataclasses import dataclass
from typing import Iterator, Self, Union

pars = {
    '(': ')', '[': ']', '{': '}', '"""': '"""'
}


def count_pars(line: str):
    """ Counts the closed and opened parentheses in gotten line
    """
    pars_count = 0
    skip = ''

    for sym in line:
        if sym in ('"', "'"):
            if skip and skip[-1] == sym:
                skip = skip[:-1]
            else:
                skip += sym

        elif not skip:
            if sym == '(':
                pars_count += 1
            elif sym == ')':
                pars_count -= 1

    return pars_count


def extract_one_object(iter_str_lines: Iterator[str]) -> list[str] | None:
    """ Extracting one object: from definition till the end through several lines """

    try:
        str_line = next(iter_str_lines)
    except StopIteration:
        return None

    line_stack = [str_line.rstrip('\\')]
    are_pars_opened = []
    while True:
        if not str_line.strip():
            break

        last_symbol = str_line.rstrip()[-1]

        if are_pars_opened:
            if (
                    (last_symbol in pars.values() and pars[are_pars_opened[-1]] == last_symbol)
                    or ('"""' in str_line and pars[are_pars_opened[-1]] == '"""')
            ):
                try:
                    are_pars_opened.pop(-1)
                    if not are_pars_opened:
                        break
                except IndexError:
                    break
        else:
            if last_symbol in pars:
                are_pars_opened.append(last_symbol)
            elif '"""' in str_line:
                are_pars_opened.append('"""')
            elif last_symbol not in ',\\':
                break

        try:
            str_line = next(iter_str_lines)
        except StopIteration:
            break

        line_stack.append(str_line.rstrip('\\'))

    return line_stack


def parse_objects_from_file(iter_str_lines: Iterator[str]) -> Union['LineType', 'CodeLine', None]:
    """ Concatenates many-lines into one line and returning the right management object for this new CodeLine

    :param iter_str_lines: the iterable over the python module
    """
    line_stack = extract_one_object(iter_str_lines)

    if line_stack is None:
        return

    instance = CodeLine(
        (' '.join(line_stack)).replace('\n', '')
    )

    if instance.has_import():
        return ImportLine(instance)

    if instance.is_empty():
        return EmptyLine(instance)

    if instance.is_comment():
        return CommentLine(instance)

    if instance.have_def():
        return FunctionLine(instance)

    if instance.is_class():
        return ClassLine(instance)

    if instance.is_a_variable():
        return VariableLine(instance)

    return instance


class CodeLine(UserString):
    """ Object representation of the code essentials """

    def __init__(self, str_line: str):
        self.indent = len(str_line) - len(str_line.lstrip(' '))

        str_line = str_line.rstrip(' \t\n')

        super(CodeLine, self).__init__(str_line)

        self.parsed = set(str_line.split())

    def has_import(self):
        if 'import' not in self.parsed:
            return False

        ordered_parsed = self.data.split()

        if 'import' == ordered_parsed[0] or ('import' == ordered_parsed[2] and 'from' == ordered_parsed[0]):
            return True

        return False

    def have_def(self):
        return 'def' in self.parsed

    def is_class(self):
        return 'class' in self.parsed

    def is_empty(self):
        return not bool(self)

    def is_a_variable(self):
        maybe_var = self.split('=', maxsplit=1)
        return len(maybe_var) == 2 and ' ' not in maybe_var[0].strip()

    def is_comment(self):
        try:
            return self.data.lstrip(' \t')[0] == '#'
        except IndexError:
            return False


class LineType(ABC):
    def __init__(self, code_line: 'CodeLine'):
        self.code_line = code_line
        self.indent = code_line.indent

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.code_line}>'

    def __bool__(self):
        return bool(self.code_line)


@dataclass
class ImportModel:
    """ Represent  """
    raw: str
    as_list: list[str]
    module: str
    alias: str | None
    source: str

    @classmethod
    def from_imports_list(cls, import_str: str, import_from: str) -> Self:
        clear_import_str = import_str.strip(' ,()')
        as_list = clear_import_str.split()

        return ImportModel(
            raw=clear_import_str,
            as_list=as_list,
            module=as_list[0],
            alias=as_list[-1] if 'as' in clear_import_str else None,
            source=import_from
        )

    @classmethod
    def from_import_single(cls, import_str: str) -> Self:
        clear_import_str = import_str.strip(' ,()')
        as_list = clear_import_str.split()
        module_path = as_list[0]
        if '.' in module_path:
            source, module = module_path.rsplit('.', maxsplit=1)
        else:
            source = module = module_path

        return ImportModel(
            raw=clear_import_str,
            as_list=as_list,
            module=module,
            alias=as_list[-1] if 'as' in clear_import_str else None,
            source=source
        )


class ImportLine(LineType):
    """ Manging lines with imports """
    import_from: str
    import_what: list[ImportModel]

    def __init__(self, code_line: 'CodeLine'):
        super(ImportLine, self).__init__(code_line)

        if code_line.startswith('from'):
            # 1+ objects from module
            _, source, _, imports = code_line.split(maxsplit=3)
            self.import_from = source
            self.import_what = []

            for import_str in imports.strip('()').replace('\\', '').split(','):
                clear_import_str = import_str.strip()
                if not clear_import_str:
                    continue
                if ',' in clear_import_str:
                    raise Exception(code_line)
                self.import_what.append(ImportModel.from_imports_list(import_str, self.import_from))
        else:
            # 1 module or object
            import_model = ImportModel.from_import_single(code_line.split(maxsplit=1)[-1])
            self.import_from = import_model.source
            self.import_what = [import_model]


class EmptyLine(LineType):
    """ Managing empty lines """

    __name__ = 'EmptyLine'


class CommentLine(LineType):
    """ Managing comment lines """


class ClassLine(LineType):
    """ todo: """

    def __init__(self, code_line: 'CodeLine'):
        super(ClassLine, self).__init__(code_line)


class FunctionLine(LineType):
    """ todo: """


class VariableLine(LineType):
    """ todo: """


ObjectLines = ClassLine | FunctionLine | VariableLine
