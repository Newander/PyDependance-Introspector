import typing as t
from itertools import zip_longest
from pathlib import Path

from src.code_objs.classes import Class
from src.code_objs.functions import Function
from src.code_objs.line import ClassLine, FunctionLine, ImportLine, VariableLine, parse_line_iter
from src.code_objs.variables import Variable


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
    imports: t.List[ImportLine]
    classes: t.List[Class]
    functions: t.List[Function]

    def __init__(self, path: Path, project_root: Path):
        self.path = path
        self.abs_import = make_relative_import(path, project_root)

        # if path == Path('/home/sgavrilov/PycharmProjects/mi-backend-py/scheduled/reports/reports.py'):
        #     print(123)

        # Remove all empty lines
        self.content = []
        i_file = self.path.open(encoding='utf-8')
        while True:
            cline = parse_line_iter(i_file)

            if cline is None:
                break

            self.content.append(cline)

        # Module content
        self.imports = list()
        self.classes = list()
        self.functions = list()
        self.global_variables = list()

    def __hash__(self):
        return hash(str(self.path))

    def __repr__(self):
        return f'Module {self.path}'

    def get_object_by_name(self, obj_name: str):
        """ Extract the object by his name """

        for obj_list in [self.classes, self.functions, self.global_variables]:
            for obj in obj_list:
                if obj.name == obj_name:
                    return obj

        raise KeyError

    def parse_classes(self):
        """ Creates Class objects for all modules from the ClassLines
        """
        line_iter = iter(self.content)
        end_line = None
        while True:
            try:
                cline = next(line_iter) if end_line is None else end_line
            except StopIteration:
                break

            if isinstance(cline, ClassLine):
                # todo: problem with parsing empty(?) class declarations
                cls, end_line = Class.parse(cline, line_iter, self.abs_import)
                self.classes.append(cls)
            else:
                end_line = None

    def parse_functions(self):
        """ Creates Function objects for all modules from the FunctionLines
        """
        line_iter = iter(self.content)
        while True:
            try:
                cline = next(line_iter)
            except StopIteration:
                break

            if isinstance(cline, FunctionLine):
                cls, end_line = Function.parse(cline, line_iter, self.abs_import)
                self.functions.append(cls)

    def parse_global_variables(self):
        """ Extracting global variables
        """
        line_iter = iter(self.content)
        while True:
            try:
                cline = next(line_iter)
            except StopIteration:
                break

            if isinstance(cline, VariableLine):
                cls, end_line = Variable.parse(cline, line_iter, self.abs_import)
                self.global_variables.append(cls)

    def parse_imports(self):
        """ Read all imported objects in the module """

        self.imports = [
            cline for cline in self.content
            if isinstance(cline, ImportLine)
        ]


class Folder:
    """
        Representation of Python models directory
    """
    ignore_list = ('venv', 'versions', 'migrations')

    def __init__(self, dir_path: Path, root_path: Path):
        self.path = dir_path
        self.root_path = root_path

        self.import_range = ''

        self.sub_folders: t.List[Folder] = []
        self.modules: t.List[Module] = []

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
            obj_path = self.path / file
            if (
                    file.is_dir()
                    and not file.name.startswith('venv')
                    and file.name[0] not in ('.', '_')
                    and file.name not in Folder.ignore_list
            ):
                self.sub_folders.append(Folder(dir_path=obj_path, root_path=self.root_path))
            elif file.suffix == '.py':
                self.modules.append(
                    Module(path=obj_path, project_root=self.root_path)
                )

        for folder in self.sub_folders:
            folder.parse_dir()

    def parse_modules(self):
        """ Parse all import definitions """
        for module in self.modules:
            module.parse_imports()
            module.parse_global_variables()
            module.parse_classes()
            module.parse_functions()

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
        """ Caluclates only code lines in modules and sub folders """
        return sum(
            [len(module.content) for module in self.modules] +
            [
                folder_module.calculate_lines()
                for folder_module in self.sub_folders
            ]
        )
