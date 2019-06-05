from src.tree import Folder, Module


class Linker:
    """ Consists links between modules in the project:
        Imports, classes and functions
    """

    def __init__(self, root: Folder):
        self.root = root
        self.relations = dict(
            imports={'library': dict(), 'project': dict()},
            classes={},
            functions={}
        )

    def __repr__(self):
        return f'Linker for {len(self.relations)} modules in {self.root} project'

    @staticmethod
    def link_module(relations: dict, module: Module):
        if module.abs_import in relations:
            raise Exception('Duplicated module in the relations!')

        relations[module.abs_import] = module.imports

        return relations

    def link_folder(self, folder: Folder, relations: dict):
        """ Probably unsafe operations over the `relations` dict, but...

        :param folder:
        :param relations:
        :return:
        """
        folders = [folder.import_range]
        for module in folder.modules:
            self.link_module(relations, module)

        for sub_folder in folder.sub_folders:
            folders.extend(
                self.link_folder(sub_folder, relations)
            )

        return folders

    def build_import_tree(self):
        raw_imports = {}
        folder_imports = self.link_folder(self.root, raw_imports)
        self.relations['imports']['library'] = {
            dest: imports for dest, imports in raw_imports.items()
            if dest not in folder_imports
        }
        self.relations['imports']['project'] = {
            dest: imports for dest, imports in raw_imports.items()
            if dest in folder_imports
        }
