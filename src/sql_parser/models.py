from collections import UserString
from dataclasses import dataclass
from typing import Iterator

from src.sql_parser.utils import extract_between_curves, fill_dot_with_nulls


@dataclass
class SQLImport:
    raw: list[str]
    table: str
    alias: str | None = None


@dataclass
class SQLJoin:
    raw: list[str]
    table: str
    alias: str | None
    join_by: list[str]


class Field:

    def __init__(self, field_misc: list[str]):
        self.raw = field_misc

        if len(self.raw) == 1:
            self.table, self.name = fill_dot_with_nulls(2, self.raw[0])
            self.alias = None
        elif any(isinstance(el, list) for el in self.raw):
            for el in self.raw:
                if isinstance(el, Field):
                    self.table = el.table
                    self.name = el.name
                    self.alias = el.alias
                    break
        else:
            cut = -2 if self.raw[-2] == 'as' else -1
            the_field = ' '.join(self.raw[:cut])
            elements = fill_dot_with_nulls(2, the_field)

            if len(elements) == 2:
                self.table, self.name = elements
            else:
                self.table = None
                self.name = the_field

            self.alias = self.raw[-1]

    def __repr__(self):
        if self.table:
            field_name = f'{self.table}.{self.name}'
        else:
            field_name = str(self.name)

        if self.alias:
            field_name += f' as {self.alias}'

        return f'<Field {field_name}>'


class Distinct:

    def __init__(self, distinct_on: list[str] | None = None):
        self.distinct_on = distinct_on

    @classmethod
    def parse(cls, iter_query: Iterator[str]) -> tuple['Distinct', str]:
        on_fields_or = next(iter_query)
        distinct_on = None

        if on_fields_or == 'on':
            next(iter_query)  # making a step toward to the opening curve
            distinct_on = extract_between_curves(iter_query)
            on_fields_or = ''

        return Distinct(distinct_on=distinct_on), on_fields_or


class CatPathString(UserString):
    def __repr__(self):
        return f'cat {self.data}'
