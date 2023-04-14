from copy import deepcopy
from pathlib import Path
from typing import Dict, List

from src.code_objs.line import VariableLine
from src.code_objs.variables import Variable
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

    def get_import_graph(self, path: str, width: int, height: int):
        graph = self.import_graph.create_import_graph(width, height)
        self.import_graph.save(graph, path)

    def print_stats(self):
        print(
            self, f'The project have {self.root.calculate_lines()} code lines', sep='\n'
        )

    def all_variables(self) -> List[Variable]:
        """ Gather all variables in the project """
        result = []
        for module in self.root.list_modules():
            result.extend(module.global_variables)
            result.extend(
                code_line
                for function in module.functions
                for code_line in function.body
                if isinstance(code_line, Variable)
            )
            result.extend(
                code_line
                for _class_ in module.classes
                for code_line in _class_.body
                if isinstance(code_line, Variable)
            )

        for module in self.root.list_modules():
            for object_list in (module.classes, module.functions):
                for code_block in object_list:
                    for code_line in code_block.body:
                        if isinstance(code_line, VariableLine):
                            result.append(
                                Variable(
                                    name=Variable.parse_name(code_line),
                                    module_import_path=module.abs_import,
                                    body=[code_line]
                                )
                            )

        return result
