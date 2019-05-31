from itertools import zip_longest
from pathlib import Path
from typing import List


class Module:
    """
        One python module
    """
    def __init__(self, path: Path):
        self.path = path
        self.content = self.path.open('r', encoding='utf-8').readlines()

        # Module content
        self.imports = list()

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
        return [i for i in self.imports]


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
                self.modules.append(Module(path=obj_path))

        for folder in self.sub_folders:
            folder.parse_dir()

    def parse_modules(self):
        """ Parse all import definitions """
        for module in self.modules:
            module.parse_imports()
            # module.parse_classes()
            # module.parse_functions()

        for folder in self.sub_folders:
            folder.parse_modules()

    def fill_import_range(self):
        """ Fill `self.import_range` attribute as classic import """
        for local, root in zip_longest(self.path.parts, self.root_path.parts):
            if root is None:
                self.import_range += f'.{local}'

        self.import_range = self.import_range or f'{self.path.name}'

    def calculate_import_range(self):
        """ Recursive import range definition through the tree """
        self.fill_import_range()

        for folder in self.sub_folders:
            folder.calculate_import_range()


class Parser:
    def __init__(self, project: Path):
        self.project = project
        self.root = Folder(dir_path=self.project, root_path=self.project)

    def __repr__(self):
        return f'Parser on {self.project} with {self.root.calculate_dirs()} dirs ' \
            f'and {self.root.calculate_modules()} modules'

    def extract_tree(self):
        self.root.parse_dir()

    def build_tree(self):
        self.root.calculate_import_range()
        self.root.parse_modules()
