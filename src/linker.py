from collections import UserDict

from src.tree import Folder, Module


class Linker(UserDict):
    """ Consists links between modules in the project:
        Imports, classes and functions
    """
    root: Folder

    def __init__(self, root, *args, **kwargs):
        super(Linker, self).__init__(*args, **kwargs)

        self.root = root
        self.libraries = set()

    def __repr__(self):
        return \
            f'Project {self.root}'

    def get_module_by_import(self, abs_import) -> Module:
        return self[abs_import]['module']

    def gather_modules(self, folder: Folder = None):
        """ Extract all the modules into self dict object """
        folder = folder or self.root

        for module in folder.modules:
            self[module.abs_import] = {
                'module': module,
                'imports': []
            }

        for sub_folder in folder.sub_folders:
            self.gather_modules(sub_folder)

    def build_import_tree(self):
        for module_data in self.values():
            module = module_data['module']  # type: Module
            for import_ in module.imports:
                abs_import = import_.import_from

                try:
                    imported_module = self.get_module_by_import(abs_import)
                except KeyError:
                    # todo: check 'src.code_objs.line' module (bug)
                    self.libraries.add(abs_import)

                    new_import = dict(module=import_.import_from, objects=import_.import_what)
                else:
                    new_import = dict(
                        module=imported_module,
                        object=[imported_module.get_object_by_name(name) for name in import_.import_what]
                    )
                finally:
                    self[module.abs_import]['imports'].append(new_import)
