import typing as t


class Obj:
    def __init__(self, name, path):
        self.path = path
        self.name = name

    @classmethod
    def parse_name(cls, def_line):
        raise NotImplementedError

    @classmethod
    def parse(cls, file_lst: t.List[str], path_to_module: str):
        """ Extracting all info about object into new instance """
        def_line = file_lst[0]
        name = cls.parse_name(def_line)

        for i, sim in enumerate(def_line):
            if sim != ' ':
                break

        start_indent = i

        return cls(name, path_to_module)


class Function(Obj):
    """ Representation of the Python Function """


class Class(Obj):
    """ Representation of the Python Class """

    @classmethod
    def parse_name(cls, def_line):
        class_name = def_line.split()[1]
        idx = max((class_name.find(':'), class_name.find('(')))
        return class_name[:idx]
