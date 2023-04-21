from typing import Callable, Iterable, Iterator

from src.py_parser.utils import FilePath, FolderPath, iter_through_files
from src.sql_parser.config import skips, specificWords
from src.sql_parser.models import Field
from src.sql_parser.parser import Parser
from src.sql_parser.utils import parser


def is_service_word(word: str) -> bool:
    return (
            word in specificWords
            or word in skips
            or set(word) & set('><()[]{}-+*!\'')
            or word in ('from', 'now', 'on', 'and', 'or', 'in', 'epoch', 'interval', 'not', 'count', 'sum', 'max',
                        'distinct', 'trim', 'both', 'as', 'cast', 'last_value', 'over', 'partition', 'by', 'rows',
                        'between', 'unbounded', 'preceding', 'following', 'case', 'when', 'then', 'coalesce', 'end',
                        'like', 'extract')
            or len(word) == 1
    )


class SQLSource:
    """ Container for a SQL path and parser """

    def __init__(self, path: FilePath):
        self.path = path
        self.name = self.path.name
        self.query_text = self.path.read_text().replace('--', ' ')
        self.parsed_text = list(parser(self.query_text.lower()))

        self.parser = Parser(
            self.path,
            self.query_text,
            iter(self.parsed_text)
        )

    def __repr__(self):
        return f'<SQLSource [{self.path}]>'

    def parse_query(self):
        self.parser.parsing()

    def extract_templated_names(self, ignore_strings: bool) -> list[str]:
        result = []
        for unit in self.parsed_text:
            if unit.count('{') and unit.count('}'):
                if not ignore_strings or (ignore_strings and not {unit[0], unit[-1]} & {'"', "'"}):
                    result.append(unit)
        return result

    def all_tables(self) -> list[str]:
        return list(self.parser.tables())

    def gather_aliases(self, select: dict, table_name: str) -> list[str]:
        """ Gathering all aliases from the provided `select` object """
        has_joins = bool(select['joins'] and select['joins']['joins'])

        aliases = []

        if has_joins:
            for join in select['joins']['joins']:
                if join['from'] == table_name:
                    aliases.append(join['alias'])
                elif isinstance(join['from'], dict):
                    aliases.extend(self.gather_aliases(join['from'], table_name))

        if select['table_name'] == table_name:
            aliases.append(select['alias'])

        if select['sub_query']:
            aliases.extend(self.gather_aliases(select['sub_query'], table_name))

        if select['unions']:
            for union in select['unions']:
                if isinstance(union, dict):
                    aliases.extend(self.gather_aliases(union, table_name))

        return sorted(set(filter(None, aliases)))

    def grab_fields(
            self,
            table_name: str,
            get_fields_from_select: Callable[[dict], Iterable[Field | str]],
            outer_aliases: list[str]
    ) -> list[str]:
        """ Gathering fields by provided conditions """

        def check_join(select: dict, join: dict, aliases: list[str]):
            return not {table_name, *aliases} & set(filter(
                lambda obj: isinstance(obj, str),
                [join['from'], select['table_name'], select['alias'], join['alias']]
            ))

        def check_field_with_table(field_name: str, inner_aliases: list[str]) -> bool:
            alias_values = [table_name, *inner_aliases]
            return any(field_name.startswith(f'{table}.') for table in alias_values)

        def gather_fields(select: dict, aliases: list[str]) -> list[str]:
            has_joins = bool(select['joins'] and select['joins']['joins'])
            fields = []

            if has_joins:

                for join in select['joins']['joins']:
                    if isinstance(join['from'], dict):
                        fields.extend(gather_fields(join['from'], aliases))

                    if check_join(select, join, aliases):
                        continue

                    for word in join['join_by']:
                        if is_service_word(word):
                            continue

                        if '=' in word:
                            for little_field in word.split('='):
                                if check_field_with_table(little_field, aliases):
                                    fields.append(word.split('.')[1])
                        elif check_field_with_table(word, aliases):
                            fields.append(word.split('.')[1])
                        elif '.' not in word:
                            fields.append(word)

            if select['sub_query']:
                fields.extend(gather_fields(select['sub_query'], aliases))

            if select['unions']:
                for union in select['unions']:
                    if isinstance(union, dict):
                        fields.extend(gather_fields(union, aliases))

            for field in get_fields_from_select(select):
                if isinstance(field, Field):
                    if field.table is None or field.table in (table_name, *aliases):
                        fields.append(field.name)
                elif check_field_with_table(field, aliases):
                    fields.append(field.split('.')[1])
                elif '.' not in field:
                    fields.append(field)

            return sorted(set(fields))

        outer_result = []
        for outer_select in self.parser.list_objects_with(with_key='fields', filter_type='select'):
            outer_aliases = self.gather_aliases(outer_select, table_name)
            outer_result.extend(gather_fields(outer_select, outer_aliases))

        return outer_result

    def grab_fields_select(self, table_name: str, aliases: list[str]) -> list[str]:
        return self.grab_fields(table_name, lambda select: select['fields']['fields_list'], aliases)

    def grab_fields_where(self, table_name: str, aliases: list[str]) -> list[str]:
        def filtering_whereas(select: dict) -> Iterable[str]:
            if not select['whereas']:
                return

            for condition in select['whereas']['conditions']:
                if isinstance(condition, str) and not is_service_word(condition):
                    yield condition
                else:
                    for sub_condition in condition:
                        if not is_service_word(sub_condition):
                            yield sub_condition

        return self.grab_fields(table_name, filtering_whereas, aliases)

    @staticmethod
    def parameterised_filter(main_key: str) -> Callable[[dict], list[Field]]:
        def filter_(select: dict) -> list[Field]:
            return (
                    select[main_key]
                    and select[main_key]['fields']
                    and select[main_key]['fields']['fields_list']
            ) or []

        return filter_

    def replace_numbers_fields_filter(self, main_key: str) -> Callable[[dict], list[Field]]:
        main_key_fields = self.parameterised_filter(main_key)

        def filter_(select: dict) -> list[Field]:
            under_the_key_fields = main_key_fields(select)
            select_fields = select['fields']['field_list']

            result = []
            for field in under_the_key_fields:
                if field.name.isdigit():
                    field_num = int(field.name)
                    result.append(select_fields[field_num])
                else:
                    result.append(field)

            return result

        return filter_

    def grab_fields_order_by(self, table_name: str, aliases: list[str]) -> list[str]:
        return self.grab_fields(table_name, self.parameterised_filter('order_by'), aliases)

    def grab_fields_group_by(self, table_name: str, aliases: list[str]) -> list[str]:
        result = self.grab_fields(table_name, self.parameterised_filter('group_by'), aliases)
        return result

    def grab_fields_limit_offset(self, table_name: str, aliases: list[str]) -> list[str]:
        return (
                self.grab_fields(table_name, self.parameterised_filter('limits'), aliases)
                +
                self.grab_fields(table_name, self.parameterised_filter('offsets'), aliases)
        )

    def grab_all_aliases(self, table_name: str) -> list[str]:
        """ Gathering all aliases for the provided table """
        all_aliases = []
        for outer_select in self.parser.list_objects_with(with_key='fields', filter_type='select'):
            all_aliases.extend(self.gather_aliases(outer_select, table_name))

        return sorted(set(all_aliases))


class SQLProject:
    """ Contains and manage a whole folder of SQL records """

    def __init__(self, path: FolderPath, debug_logging: bool = False):
        self.debug_logging = debug_logging
        self.path = path
        self.variables: list[SQLSource] = []
        self.files: list[SQLSource] = []

    def __repr__(self):
        return f'<SQLProject [{self.path.name}] {len(self.variables)=} {len(self.files)=}>'

    def __iter__(self) -> Iterator['SQLSource']:
        yield from self.variables
        yield from self.files

    def __len__(self):
        return len(self.variables) + len(self.files)

    def parse_files(self, ignore_commands: tuple | None = None):
        self.files.extend(self.parse_folder('files', ignore_commands))

    def parse_variables(self, ignore_commands: tuple | None = None):
        self.variables.extend(self.parse_folder('variables', ignore_commands))

    def parse_folder(self, folder_name: str, ignore_commands: tuple | None):
        for sql_file in iter_through_files(
                self.path / folder_name,
                lambda folder: True,
                lambda file: file.suffix == '.sql'
        ):
            src = SQLSource(sql_file)
            if ignore_commands:
                operands = {
                    op.strip(' (),') for op in src.query_text.lower().split()
                }
                if not operands & set(ignore_commands):
                    yield src

            else:
                yield src

    def extract_tables(self):
        good = 0
        bad = 0
        for i, src in enumerate(self):
            if self.debug_logging:
                print(f'Progress: {i + 1}/{len(self)}')
                print(f'Observing: {src.name}')

            try:
                src.parser.parsing()
                good += 1
            except Exception as err:
                bad += 1

        print(f'The overall result:\n\t- Overall:{len(self)}\n\t\t- {bad=}\n\t\t- {good=}')

    def templated_scripts(self, ignore_strings: bool = False) -> Iterable[SQLSource]:
        for var_source in self:
            if var_source.extract_templated_names(ignore_strings=ignore_strings):
                yield var_source
