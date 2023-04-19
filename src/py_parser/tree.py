from itertools import zip_longest
from pathlib import Path
from typing import Iterable, Type

from src.py_parser.code_objs.classes import Class
from src.py_parser.code_objs.functions import Function
from src.py_parser.code_objs.line import ClassLine, CodeLine, FunctionLine, ImportLine, VariableLine, parse_objects_from_file
from src.py_parser.code_objs.variables import Variable

DefinitiveObjects = Class | Function | Variable


def make_relative_import(local_path, root_path):
    """ Fill `self.import_range` attribute as classic import """
    import_range = []

    for local, root in zip_longest(local_path.parts, root_path.parts):
        if root is None:
            suffix_idx = local.rfind('.')

            if suffix_idx != -1:
                local = local[:suffix_idx]

            import_range.append(local)

    return '.'.join(import_range) if import_range else f'{local_path.name}'


class Module:
    """
        One python module as code
    """
    imports: list[ImportLine]
    classes: list[Class]
    functions: list[Function]

    def __init__(self, path: Path, project_root: Path):
        self.path = path
        self.abs_import = make_relative_import(path, project_root)

        # if path == Path('/home/sgavrilov/PycharmProjects/mi-backend-py/scheduled/executor.py'):
        #     print(123)

        # Remove all empty lines
        self.content = []
        i_file = self.path.open(encoding='utf-8')
        while True:
            code_line: CodeLine = parse_objects_from_file(i_file)

            if code_line is None:
                break

            self.content.append(code_line)

        # Module content
        self.imports = list()
        self.classes = list()
        self.functions = list()
        self.global_variables = list()

    def __hash__(self):
        return hash(str(self.path))

    def __repr__(self):
        return f'Module {self.path}'

    def get_object_by_name(self, obj_name: str) -> DefinitiveObjects:
        """ Extract the object by his name """

        for obj_list in [self.classes, self.functions, self.global_variables]:
            for obj in obj_list:
                if obj.name == obj_name:
                    return obj

        raise KeyError

    def parse_objects(self,
                      container: list,
                      parsing_line_cls: Type[ClassLine | FunctionLine],
                      parsing_cls: Type[Class | Function]):
        """ Parsing loop for Classes or Functions """
        line_iter = iter(self.content)
        end_line = None
        while True:
            try:
                code_line = next(line_iter) if end_line is None else end_line
            except StopIteration:
                break

            if isinstance(code_line, parsing_line_cls):
                # todo: problem with parsing empty(?) class declarations
                cls, end_line = parsing_cls.parse(code_line, line_iter, self.abs_import)
                container.append(cls)
            else:
                end_line = None

    def parse_global_variables(self):
        """ Extracting global variables
        """
        for code_line in self.content:
            if isinstance(code_line, VariableLine) and code_line.indent == 0:
                self.global_variables.append(
                    Variable(
                        name=Variable.parse_name(code_line),
                        module_import_path=self.abs_import,
                        body=[code_line]
                    )
                )

    def parse_imports(self):
        """ Read all imported objects in the module """

        self.imports = [
            code_line for code_line in self.content
            if isinstance(code_line, ImportLine)
        ]

    def list_objects(self) -> list[DefinitiveObjects]:
        """ Returns all valuable objects in a list (functions, classes and globals) """
        # todo: here must be also imports, but the functionality is not ready yet
        return self.classes + self.functions + self.global_variables


class Folder:
    """
        Representation of Python models directory
    """
    ignore_list = ('venv', 'versions', 'migrations')

    def __init__(self, dir_path: Path, root_path: Path):
        self.path = dir_path
        self.root_path = root_path

        self.import_range = ''

        self.sub_folders: list[Folder] = []
        self.modules: list[Module] = []

    def __repr__(self):
        return f'Folder {self.path}'

    def calculate_dirs(self):
        sum_dirs = 0
        for folder in self.sub_folders:
            sum_dirs += folder.calculate_dirs()

        return sum_dirs + len(self.sub_folders)

    def calculate_modules(self):
        sum_modules = 0
        for folder in self.sub_folders:
            sum_modules += folder.calculate_modules()

        return sum_modules + len(self.modules)

    def parse_dir(self):
        """ Extract all sub dirs into objects """
        for file in self.path.iterdir():
            if (
                    file.is_dir()
                    and not file.name.startswith('venv')
                    and file.name[0] not in ('.', '_')
                    and file.name not in Folder.ignore_list
            ):
                self.sub_folders.append(Folder(dir_path=file, root_path=self.root_path))
            elif file.suffix == '.py':
                self.modules.append(
                    Module(path=file, project_root=self.root_path)
                )

        for folder in self.sub_folders:
            folder.parse_dir()

    def parse_modules(self):
        """ Parse all import definitions """
        for module in self.modules:
            module.parse_imports()
            module.parse_global_variables()
            module.parse_objects(module.classes, ClassLine, Class)
            module.parse_objects(module.functions, FunctionLine, Function)

        for folder in self.sub_folders:
            folder.parse_modules()

    def calculate_import_range(self):
        """ Recursive import range definition through the tree """
        self.import_range = make_relative_import(self.path, self.root_path)

        for folder in self.sub_folders:
            folder.calculate_import_range()

    def get_folder_names(self):
        yield self.import_range

        for folder_module in self.sub_folders:
            yield from folder_module.get_folder_names()

    def get_module_names(self):
        yield from (module.abs_import for module in self.modules)

        for folder_module in self.sub_folders:
            yield from folder_module.get_module_names()

    def calculate_lines(self):
        """ Calculates only code lines in modules and sub folders """
        return sum(
            [len(module.content) for module in self.modules] +
            [
                folder_module.calculate_lines()
                for folder_module in self.sub_folders
            ]
        )

    def list_modules(self) -> Iterable[Module]:
        """ Yielding all modules in this folder and sub folders """
        yield from self.modules

        for folder in self.sub_folders:
            yield from folder.list_modules()
