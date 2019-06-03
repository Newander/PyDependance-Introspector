from copy import deepcopy
from itertools import zip_longest
from pathlib import Path
from typing import List, Dict

import pandas as pd


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


def fit_lists_one_size(dict_with_lists: Dict[str, List]):
    new_dict = deepcopy(dict_with_lists)

    max_size = max(len(lst) for lst in new_dict.values())

    for lst_key in new_dict:
        new_dict[lst_key].extend(
            [''] * (max_size - len(new_dict[lst_key]))
        )

    return new_dict


class Module:
    """
        One python module
    """
    magic_methods = ('__init__', '__call__', )

    def __init__(self, path: Path, project_root: Path):
        self.path = path
        self.abs_import = make_relative_import(path, project_root)
        self.content = self.path.open('r', encoding='utf-8').readlines()

        # Module content
        self.imports = list()
        self.classes = list()
        self.functions = list()

    def __repr__(self):
        return f'Module {self.path}'

    @staticmethod
    def extract_imports(import_line):
        iter_import = iter(import_line.split())
        from_ = ''

        try:
            while True:
                part = next(iter_import)

                if part == 'from':
                    from_ = next(iter_import) + '.'

                elif part == 'import':
                    while True:
                        imported_obj = next(iter_import).replace(',', '').replace('\\', '')
                        yield from_ + imported_obj
        except StopIteration:
            ...

    def parse_classes(self):
        for line in self.content:
            parsed = list(line.split())

            if not parsed:
                continue

            if 'class' == parsed[0]:
                class_name = parsed[1]
                idx = max((class_name.find(':'), class_name.find('(')))
                self.classes.append(class_name[:idx])

    def parse_functions(self):
        for line in self.content:
            parsed = list(line.split())

            if not parsed:
                continue

            if 'def' == parsed[0] and 'self' not in line:
                fun_name = parsed[1]
                fun_name = fun_name[:fun_name.find('(')]

                if fun_name not in self.magic_methods:
                    self.functions.append(fun_name)

    def parse_imports(self):
        """ Read all imported objects in the module """

        iter_lines = iter(self.content)
        import_stack = []

        try:
            while True:
                line = next(iter_lines)
                parsed = set(line.split())

                if 'import' in parsed:
                    import_stack.append(line)

                    if '\\' in parsed or '(' in parsed:
                        while '\\' in parsed or ')' in parsed:
                            line = next(iter_lines)
                            parsed = set(line.split())
                            import_stack[-1] += line
        except StopIteration:
            ...

        self.imports = [
            configured_import
            for import_line in import_stack
            for configured_import in self.extract_imports(import_line)
        ]

    def get_imports(self):
        return self.imports


class Folder:
    """
        Representation of Python models directory
    """
    ignore_list = ('venv', 'versions', 'migrations')

    def __init__(self, dir_path: Path, root_path: Path):
        self.path = dir_path
        self.root_path = root_path

        self.import_range = ''

        self.sub_folders: List[Folder] = []
        self.modules: List[Module] = []

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
            if file.is_dir() and \
                    file.name[0] not in ('.', '_') and \
                    file.name not in Folder.ignore_list:
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
            module.parse_classes()
            module.parse_functions()

        for folder in self.sub_folders:
            folder.parse_modules()

    def calculate_import_range(self):
        """ Recursive import range definition through the tree """
        self.import_range = make_relative_import(self.path, self.root_path)

        for folder in self.sub_folders:
            folder.calculate_import_range()


class Linker:
    """ Consists links between modules in the project:
        Imports, classes and functions
    """

    def __init__(self, root: Folder):
        self.root = root
        self.relations = dict(
            imports={},
            classes={},
            functions={}
        )

    def __repr__(self):
        return f'Linker for {len(self.relations)} modules in {self.root} project'

    def link_module(self, module: Module):
        if module.abs_import in self.relations['imports']:
            raise Exception('Duplicated module in the relations!')

        self.relations['imports'][module.abs_import] = module.imports

    def link_folder(self, folder: Folder):
        for module in folder.modules:
            self.link_module(module)

        for sub_folder in folder.sub_folders:
            self.link_folder(sub_folder)

    def build_import_tree(self):
        self.link_folder(self.root)


class Parser:
    def __init__(self, project: Path):
        self.project = project
        self.root = Folder(dir_path=self.project, root_path=self.project)
        self.linker = Linker(self.root)

    def __repr__(self):
        return f'Parser on {self.project} with {self.root.calculate_dirs()} dirs ' \
            f'and {self.root.calculate_modules()} modules'

    def extract_tree(self):
        self.root.parse_dir()

    def gather_objects(self):
        self.root.calculate_import_range()
        self.root.parse_modules()

    def build_link_list(self):
        self.linker.build_import_tree()

    def create_report(self, result_dir: Path):
        pd.DataFrame(
            fit_lists_one_size(self.linker.relations['imports'])
        ).to_csv(
            result_dir / 'imports.csv', index=False
        )
