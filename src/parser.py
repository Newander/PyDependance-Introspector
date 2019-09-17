from copy import deepcopy
from pathlib import Path
from typing import Dict, List

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
    """ High level object to composite all the objects in code.
        Gather:
         - `Linker` -- object which links all valuable code lines
        todo: continue
    """

    def __init__(self, project: Path):
        self.project = project
        self.root = Folder(dir_path=self.project, root_path=self.project)
        self.linker = Linker(self.root)
        self.import_graph = GraphManager(self.linker)

    def __repr__(self):
        return f'Parser on {self.project} with {self.root.calculate_dirs()} dirs ' \
               f'and {self.root.calculate_modules()} modules'

    def gather_objects(self):
        """ Going through all modules and submodules from the gotten project root and
            creating program model of all the code.
        """
        self.root.parse_dir()
        self.root.calculate_import_range()
        self.root.parse_modules()

    def build_link_list(self):
        """ Create links between
                - imports (realized)
                - todo: functions
                - todo: classes
                - todo: variables
        """
        self.linker.gather_modules()
        self.linker.build_import_tree()

    def get_import_graph(self, path: str):
        graph = self.import_graph.create_import_graph()
        self.import_graph.save(graph, path)

    def print_stats(self):
        print(
            self, f'The project have {self.root.calculate_lines()} code lines', sep='\n'
        )
