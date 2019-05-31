from pathlib import Path
from typing import List


class Module:
    def __init__(self, path: Path):
        self.path = path

    def __repr__(self):
        return f'Module {self.path}'

    def parse_imports(self):
        ...


class Folder:
    ignore_list = (
        'venv',
    )

    def __init__(self, dir_path: Path, root_path: Path):
        self.path = dir_path
        self.root_path = root_path

        self.sub_folders: List[Folder] = []
        self.modules: List[Module] = []

    def __repr__(self):
        return f'Folder {self.path}'

    def parse_dir(self):
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
        for module in self.modules:
            module.parse_imports()


class Parser:
    def __init__(self, project: Path):
        self.project = project
        self.root = Folder(dir_path=self.project, root_path=self.project)

    def __repr__(self):
        return f'Parser on {self.project}'

    def extract_tree(self):
        self.root.parse_dir()

    def build_tree(self):
        self.root.calculate_import_range()
        self.root.parse_modules()
