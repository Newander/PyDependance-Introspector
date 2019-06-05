from copy import deepcopy
from pathlib import Path
from typing import Dict, List

import pandas as pd

from src.tree import Folder, Linker


def fit_lists_one_size(dict_with_lists: Dict[str, List]):
    new_dict = deepcopy(dict_with_lists)

    max_size = max(len(lst) for lst in new_dict.values())

    for lst_key in new_dict:
        new_dict[lst_key].extend(
            [''] * (max_size - len(new_dict[lst_key]))
        )

    return new_dict


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
