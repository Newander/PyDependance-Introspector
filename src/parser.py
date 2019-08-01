from copy import deepcopy
from pathlib import Path
from typing import Dict, List

import pandas as pd

from src.drawer import GraphManager
from src.linker import Linker
from src.tree import Folder


def fit_lists_one_size(dict_with_lists: Dict[str, List]):
    new_dict = deepcopy(dict_with_lists)

    max_size = max(len(lst) for lst in new_dict.values())

    for lst_key in new_dict:
        new_dict[lst_key].extend(
            [''] * (max_size - len(new_dict[lst_key]))
        )

    return new_dict


class Parser:
    """ High level object to composite all the objects in code """

    def __init__(self, project: Path):
        self.project = project
        self.root = Folder(dir_path=self.project, root_path=self.project)
        self.linker = Linker(self.root)
        self.objects_graph = GraphManager()

    def __repr__(self):
        return f'Parser on {self.project} with {self.root.calculate_dirs()} dirs ' \
            f'and {self.root.calculate_modules()} modules'

    def extract_tree(self):
        self.root.parse_dir()

    def gather_objects(self):
        self.root.calculate_import_range()
        self.root.parse_modules()

    def build_link_list(self):
        self.linker.gather_modules()
        self.linker.build_import_tree()
        self.linker.build_function_tree()

    def create_report(self, result_dir: Path):
        pd.DataFrame(
            fit_lists_one_size(self.linker.relations['imports'])
        ).to_csv(
            result_dir / 'imports.csv', index=False
        )

    def create_import_graph(self):
        import_graph = GraphManager()

        import_graph\
            .add_nodes(self.root.get_folder_names())\
            .add_nodes(self.root.get_module_names())

        # import_graph.create_edges(self.root)

        return import_graph
