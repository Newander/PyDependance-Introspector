from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

from src.sql_parser.config import joinWords, separators, specificWords
from src.sql_parser.models import CatPathString, Field
from src.sql_parser.utils import extract_between_curves


class Logger:
    def __init__(self, query_iter: Iterator[str]):
        self.query_iter = query_iter
        self.instructions: list[tuple[str, Any]] = []

    def __iter__(self) -> Iterator[str]:
        for next_value in self.query_iter:
            self.instructions.append(
                ('get', next_value)
            )
            yield next_value


class Parser:
    def __init__(self, path: Path, query_source: str, query_iter: Iterator[str]):
        # Debug info
        self.path = CatPathString(path)
        self.name = path.name

        self.source = query_source
        self.operands = []
        self.logger = Logger(query_iter)

        self.with_error = False

    def __repr__(self):
        return f'<Parser {self.name}>'

    def parsing(self):
        """ Main parsing loop for a script """
        query_iter = iter(self.logger)
        last_word_with = next(query_iter)
        if last_word_with == 'with':
            withers, last_word_with = self.withs_parse(query_iter)
            self.operands.append(withers)

        select, last_word_select = self.parse_select_with_iterator(query_iter, last_word_with)
        self.operands.append(select)

        try:
            assert last_word_select in (';', None)
        except AssertionError:
            try:
                if next(query_iter) not in (';', None):
                    self.with_error = True
            except StopIteration:
                # everything is fine
                return

    def parse_select_with_iterator(self, query_iter: Iterator[str], first_word: str) -> tuple[dict, str]:
        result, last_word = self._parse_selects(query_iter, first_word)
        return result, last_word

    def parse_select_with_string(self, query: list[str]) -> dict:
        """ Caution: the first word mustn't be 'select' """
        result, _ = self._parse_selects(iter(query), 'select')
        return result

    def _parse_selects(self, query_iter: Iterator[str], first_word: str) -> tuple[dict, str]:
        """ Parsing the most common select as possible """
        assert first_word == 'select'

        select = {
            'type': 'select',
            'fields': {},
            'table_name': None,
            'sub_query': {},
            'alias': None,
            'joins': None,
            'whereas': {},
            'group_by': {},
            'having': {},
            'unions': [],
            'order_by': {},
            'limits': {},
            'offsets': {},
        }

        try:
            select['fields'], _ = self.fields(query_iter, finalizing_words=('from',))
            # Table name extracting
            last_word = next(query_iter)
            if last_word == '(':
                # select from subquery
                select_sub_query = extract_between_curves(query_iter)
                if select_sub_query[1] == 'select':
                    sub_query = self.parse_select_with_string(select_sub_query[2:-1])
                    select['sub_query'] = sub_query
                else:
                    raise Exception
            elif last_word == 'as':
                select['table_name'] = next(query_iter)
            else:
                select['table_name'] = last_word

            try:
                next_word = next(query_iter)
            except StopIteration:
                next_word = None

            # Defining table alias
            if next_word == 'as':
                select['alias'] = next(query_iter)
                next_word = next(query_iter)
            elif next_word is None:
                ...
            elif next_word not in specificWords:
                select['alias'] = next_word
                next_word = next(query_iter)

            select['table_name'] = select['table_name'] or select['alias']

            select['joins'], last_word_join = self.joins(query_iter, next_word)

            select['whereas'], last_word_whereas = self.whereas(query_iter, last_word_join)
            select['group_by'], last_word_group_by = self.group_by(query_iter, last_word_whereas)
            select['having'], last_word_having = self.having(query_iter, last_word_group_by)

            last_word_union = last_word_having
            while last_word_union == 'union':
                union = last_word_having
                last_word_union = next(query_iter)

                if last_word_union in ('all', 'distinct'):
                    union = f'{union} {last_word_union}'
                    last_word_union = next(query_iter)

                select['unions'].append(union)

                if last_word_union == '(':
                    in_curves_select = extract_between_curves(query_iter)
                    inner_select = self.parse_select_with_string(in_curves_select[2:-1])
                    try:
                        last_word_union = next(query_iter)
                    except StopIteration:
                        last_word_union = None
                elif last_word_union == 'select':
                    inner_select, last_word_union = self.parse_select_with_iterator(query_iter, last_word_union)
                else:
                    raise ValueError(last_word_union)

                select['unions'].append(inner_select)

            select['order_by'], last_word_order_by = self.order_by(query_iter, last_word_union)
            select['limits'], last_word_limits = self.limits(query_iter, last_word_order_by)
            select['offsets'], last_word_offsets = self.offsets(query_iter, last_word_limits)
        except StopIteration:
            last_word_offsets = None  # The destiny is so

        return select, last_word_offsets

    def withs_parse(self, query_iter: Iterator[str]) -> tuple[list[dict], str]:
        """ Parsing dedicated with operands """

        def with_parser(with_iter: Iterator[str]) -> tuple[Any, str]:
            alias = next(with_iter)
            for next_word in with_iter:
                if next_word == '(':
                    break

            with_body = extract_between_curves(with_iter)
            select = self.parse_select_with_string(with_body[2:-1])

            return {'type': 'with', 'alias': alias, 'select': select}, next(with_iter)

        wither, last_word_with = with_parser(query_iter)
        result = [wither]
        while last_word_with == ',':
            wither, last_word_with = with_parser(query_iter)
            result.append(wither)

        return result, last_word_with

    def fields(self, query_iter: Iterator[str], finalizing_words: Sequence[str]) -> tuple[dict, str]:
        """ Fields Parser """

        def distinct_parser(field_iter: Iterator[str]) -> tuple[dict, str]:
            """ Distinct Parser """
            on_fields_or = next(field_iter)
            distinct_on = None

            if on_fields_or == 'on':
                next(field_iter)  # making a step toward to the opening curve
                distinct_on = extract_between_curves(field_iter)
                on_fields_or = ''

            return dict(type='distinct', distinct_on=distinct_on), on_fields_or

        fields_list = []
        distinct = None

        current_field = []
        # Fields parsing
        last_word = None
        for last_word in query_iter:

            if last_word == 'distinct':
                distinct, last_word = distinct_parser(query_iter)
                if not last_word:
                    continue

            if last_word == ',':
                fields_list.append(Field(current_field))
                current_field = []

            elif last_word == '(':
                current_field.extend(extract_between_curves(query_iter))

            elif last_word in finalizing_words:
                break

            else:
                current_field.append(last_word)

        fields_list.append(Field(current_field))
        return {
            'type': 'fields', 'distinct': distinct, 'fields_list': fields_list
        }, last_word

    def joins(self, query_iter: Iterator[str], first_word: str) -> tuple[dict, str]:
        """ Parsing all possible joins in the query """

        def parse_join(join_iter: Iterator[str]) -> tuple[dict, str]:
            """ Extract exactly one join """
            first_join_word = next(query_iter)
            join_descr = {'type': 'join'}
            if first_join_word == '(':
                inner_select_body = extract_between_curves(join_iter)
                join_descr['from'] = self.parse_select_with_string(inner_select_body[2:-1])
            else:
                join_descr['from'] = first_join_word

            maybe_alias = next(join_iter)
            if maybe_alias in ('using', 'on'):
                join_descr['alias'] = None
            elif maybe_alias == 'as':
                join_descr['alias'] = next(join_iter)
            else:
                join_descr['alias'] = maybe_alias

            join_descr['join_by'] = []
            word = None
            for word in join_iter:
                if word in joinWords or word in specificWords:
                    break
                join_descr['join_by'].append(word)

            return join_descr, word

        result = {'type': 'joins', 'joins': []}
        last_word = first_word
        while last_word in joinWords:
            if last_word != 'join':
                next(query_iter)  # skip other joinWords

            current_join, last_word = parse_join(query_iter)
            result['joins'].append(current_join)

        return result, last_word

    def whereas(self, query_iter: Iterator[str], first_word: str) -> tuple[dict, str]:
        """ Parsing where conditions """

        def parse_where(where_iter: Iterator[str], where_word: str) -> tuple[dict, str]:
            ...  # todo: in development

        result = {'type': 'whereas', 'conditions': []}
        if first_word != 'where':
            return result, first_word

        where_raw = []
        word = first_word
        for word in query_iter:
            if word == '(':
                where_cause = extract_between_curves(query_iter)
                where_raw.append(where_cause)

            elif word in specificWords or word in separators:
                break
            else:
                where_raw.append(word)

        result['conditions'].extend(where_raw)
        return result, word

    def group_by(self, query_iter: Iterator[str], first_word: str) -> tuple[dict, str]:
        """ Parsing GROUP BY conditions """

        def parse_group_by(group_by_iter: Iterator[str], group_by_word: str) -> tuple[dict, str]:
            ...  # todo: in development

        result = {'type': 'group_by', 'fields': {}}

        if first_word != 'group':
            return result, first_word

        next_word = next(query_iter)
        if next_word != 'by':
            raise Exception(self)

        group_by_fields, last_word_fields = self.fields(
            query_iter, finalizing_words=('limit', 'offset', 'having', 'order', ')', 'union')
        )
        result['fields'].update(group_by_fields)

        return result, last_word_fields

    def having(self, query_iter: Iterator[str], first_word: str) -> tuple[dict, str]:
        """ Parsing HAVING conditions """

        def parse_having(having_iter: Iterator[str], having_word: str) -> tuple[dict, str]:
            ...  # todo: in development

        result = {'type': 'having', 'fields': {}}

        if first_word != 'having':
            return result, first_word

        having_fields, last_word_fields = self.fields(
            query_iter, finalizing_words=('limit', 'offset', 'order', ')', 'union')
        )
        result['fields'].update(having_fields)

        return result, last_word_fields

    def order_by(self, query_iter: Iterator[str], first_word: str) -> tuple[dict, str]:
        """ Parsing order conditions """

        def parse_order(order_iter: Iterator[str], order_word: str) -> tuple[dict, str]:
            ...  # todo: in development

        result = {'type': 'order', 'fields': {}}

        if first_word != 'order':
            return result, first_word

        next_word = next(query_iter)
        if next_word != 'by':
            raise Exception(self)

        order_fields, last_word_fields = self.fields(query_iter, finalizing_words=('limit', 'offset', ')', 'union'))
        result['fields'].update(order_fields)

        return result, last_word_fields

    def limits(self, query_iter: Iterator[str], first_word: str) -> tuple[dict, str]:
        """ Parsing limit conditions """

        def parse_limit(limit_iter: Iterator[str], limit_word: str) -> tuple[dict, str]:
            ...  # todo: in development

        result = {'type': 'limits', 'fields': {}}

        if first_word != 'limit':
            return result, first_word

        limit_fields, last_word_fields = self.fields(query_iter, finalizing_words=('offset', ')', 'union'))
        result['fields'].update(limit_fields)

        if last_word_fields.isdigit():
            result['fields']['fields_list'].append(Field([last_word_fields]))

        return result, last_word_fields

    def offsets(self, query_iter: Iterator[str], first_word: str) -> tuple[dict, str]:
        """ Parsing offset conditions """

        def parse_offset(offset_iter: Iterator[str], offset_word: str) -> tuple[dict, str]:
            ...  # todo: in development

        result = {'type': 'offsets', 'fields': {}}

        if first_word != 'offset':
            return result, first_word

        offset_fields, last_word_fields = self.fields(query_iter, finalizing_words=(')', 'union'))
        result['fields'].update(offset_fields)

        return result, last_word_fields

    def extract_field_from_select(self, operand: dict, arg_name: str, exact_type: type = None) -> Iterable[Any]:
        for k, value in operand.items():
            if k == arg_name and (exact_type is None or isinstance(value, exact_type)):
                yield value

            elif isinstance(value, list):
                for element in value:
                    if isinstance(element, dict):
                        yield from self.extract_field_from_select(element, arg_name, exact_type)

            elif isinstance(value, dict):
                yield from self.extract_field_from_select(value, arg_name, exact_type)

    def tables(self, len_filter: int = None) -> list[str]:
        """ Gathering all table names and excluding aliases """

        def handle_select_for_tables(select_op: dict) -> Iterable[str]:
            for table in self.extract_field_from_select(select_op, 'table_name', exact_type=str):
                yield table

            for from_table in self.extract_field_from_select(select_op, 'from', exact_type=str):
                yield from_table

        def handle_select_for_aliases(select_op: dict) -> Iterable[str]:
            for alias in self.extract_field_from_select(select_op, 'alias', exact_type=str):
                yield alias

        aliases = set()
        all_tables = set()
        for op in self.operands:
            # Select
            if isinstance(op, dict):
                try:
                    all_tables.update(handle_select_for_tables(op))
                except Exception as err:
                    all_tables.update(handle_select_for_tables(op))
                aliases.update(handle_select_for_aliases(op))
            # With
            elif isinstance(op, list):
                for with_select in op:
                    all_tables.update(handle_select_for_tables(with_select))
                    aliases.update(handle_select_for_aliases(with_select))

        return [
            table for table in all_tables
            if table not in aliases and (not len_filter or len(table) > len_filter)
        ]

    def list_objects_with(self, with_key: str, filter_type: str = None) -> Iterable[dict]:
        """ Yielding all possible objects having `with_key` inside """
        for operand_group in self.operands:
            for operand in ([operand_group] if isinstance(operand_group, dict) else operand_group):
                for grouping_key in ('select', 'group_by', 'having', 'order_by', 'limits', 'offsets'):
                    if (
                            operand['type'] == grouping_key
                            and with_key in operand
                            and (not filter_type or operand['type'] == filter_type)
                    ):
                        yield operand

                    for obj in self.extract_field_from_select(operand, grouping_key):
                        if with_key in obj and (not filter_type or obj['type'] == filter_type):
                            yield obj
