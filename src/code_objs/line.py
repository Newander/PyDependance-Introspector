from collections import UserString


class CodeLine(UserString):
    """ Object representation of the code essentials """
    @classmethod
    def parse_line_iter(cls, iter_lines):
        line = next(iter_lines)
        parsed = set(line.split())
        import_stack = [line]

        if '\\' in parsed or '(' in parsed:
            while '\\' in parsed or ')' in parsed:
                line = next(iter_lines)
                parsed = set(line.split())
                import_stack.append(line)

        instance = cls(
            (''.join(import_stack)).replace('\n', '')
        )

        if instance.has_import():
            return ImportLine(instance)

        return instance

    def __init__(self, line: str):
        super(CodeLine, self).__init__(line)

        self.parsed = set(line.split())
        self.indent = len(line) - len(line.lstrip(' '))

    def has_import(self):
        """ Check is this line is import """
        if 'import' in self.parsed:
            return True

        return False


class ImportLine:
    def __init__(self, cline: 'CodeLine'):
        self.cline = cline

