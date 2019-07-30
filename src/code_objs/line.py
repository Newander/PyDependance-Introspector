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
    def parse_line_iter(
            cls, iter_lines: t.Iterator[str]
    ) -> t.Union['CodeLine', 'ImportLine', None]:
        """ Concatenates many-lines into one line and returning the right management object for this new CodeLine

        :param iter_lines: the iterable over the python module
        """

        try:
            line = next(iter_lines)
        except StopIteration:
            return None

        line_stack = [line]

        while not check_many_liners(line, prev_pars):
            pars = count_pars(line)
            try:
                line = next(iter_lines)
            except StopIteration:
                break

        instance = cls(
            (' '.join(line_stack)).replace('\n', '')
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
