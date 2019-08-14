import typing as t

from collections import UserString


def count_pars(line: str):
    """ Counts the closed and opened parentheses in gotten line
    """
    pars_count = 0
    skip = ''

    for sym in line:
        if sym in ('"', "'"):
            if skip and skip[-1] == sym:
                skip = skip[:-1]
            else:
                skip += sym

        elif not skip:
            if sym == '(':
                pars_count += 1
            elif sym == ')':
                pars_count -= 1

    return pars_count


def check_many_liners(mline: str, prev_pars=0):
    """

    :param mline:
    :param prev_pars:
    :return:
    """
    if not mline.strip():
        return False

    if mline.rstrip()[-1] == '\\':
        return True

    if count_pars(mline) > 0:
        return True

    return False


class CodeLine(UserString):
    """ Object representation of the code essentials """

    @classmethod
    def parse_line_iter(cls, iter_lines: t.Iterator[str]):
        """ Concatenates many-lines into one line and returning the right management object for this new CodeLine

        :param iter_lines: the iterable over the python module
        """

        try:
            line = next(iter_lines)
        except StopIteration:
            return None

        line_stack = [line]
        pars = count_pars(line)
        while check_many_liners(line, pars):
            try:
                line = next(iter_lines)
            except StopIteration:
                break

            pars += count_pars(line)
            line_stack.append(line)

        instance = cls(
            (' '.join(line_stack)).replace('\n', '')
        )

        if instance.has_import():
            return ImportLine(instance)

        if instance.is_empty():
            return EmptyLine(instance)

        if instance.is_comment():
            return CommentLine(instance)

        if instance.have_def():
            return FunctionLine(instance)

        if instance.is_class():
            return ClassLine(instance)

        return instance

    def __init__(self, line: str):
        self.indent = len(line) - len(line.lstrip(' '))

        line = line.rstrip(' \t\n')

        super(CodeLine, self).__init__(line)

        self.parsed = set(line.split())

    def has_import(self):
        if 'import' not in self.parsed:
            return False

        ordered_parsed = self.data.split()

        if 'import' == ordered_parsed[0] or ('import' == ordered_parsed[2] and 'from' == ordered_parsed[0]):
            return True

        return False

    def have_def(self):
        return 'def' in self.parsed

    def is_class(self):
        return 'class' in self.parsed

    def is_empty(self):
        return not bool(self)

    def is_comment(self):
        try:
            return self.data.lstrip(' \t')[0] == '#'
        except IndexError:
            return False


class LineType:
    def __init__(self, cline: 'CodeLine'):
        self.cline = cline
        self.indent = cline.indent

    def __repr__(self):
        return ' ' * self.indent + repr(self.cline)

    def __bool__(self):
        return bool(self.cline)


class ImportLine(LineType):
    """ Manging lines with imports """

    def __init__(self, cline: 'CodeLine'):
        super(ImportLine, self).__init__(cline)

        import_list = self.cline.split()

        try:
            as_idx = import_list.index('as') + 1
        except ValueError:
            self.alias = None
        else:
            self.alias = import_list[as_idx]
            import_list = import_list[:as_idx]

        import_list = [word.strip(',') for word in import_list]
        from_clause = import_list[0] == 'from'

        if from_clause:
            self.import_from = import_list[1]
            self.import_what = import_list[3:]
        else:
            import_obj = import_list[1]

            if '.' not in import_obj:
                self.import_from = import_obj
                self.import_what = '__all__'
            else:
                self.import_from = '.'.join(import_obj.split('.')[:-1])
                self.import_what = import_obj.split('.')[-1]


class EmptyLine(LineType):
    """ Managing empty lines """

    __name__ = 'EmptLine'


class CommentLine(LineType):
    """ Managing comment lines """


class ClassLine(LineType):
    """ Managing comment lines """

    def __init__(self, cline: 'CodeLine'):
        super(ClassLine, self).__init__(cline)


class FunctionLine(LineType):
    """ Managing comment lines """
