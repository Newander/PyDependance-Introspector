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
        return 'import' in self.parsed

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

    def __repr__(self):
        return repr(self.cline)


class ImportLine(LineType):
    """ Manging lines with imports """


class EmptyLine(LineType):
    """ Managing empty lines """


class CommentLine(LineType):
    """ Managing comment lines """


class ClassLine(LineType):
    """ Managing comment lines """


class FunctionLine(LineType):
    """ Managing comment lines """
