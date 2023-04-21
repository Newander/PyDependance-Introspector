import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from src.sql_parser.config import ourTablesSignal
from src.sql_parser.project import SQLProject, is_service_word
from src.sql_parser.utils import variables_extractor


@dataclass
class FieldRow:
    table_schema: str
    table_name: str
    column_name: str

    def schema_table(self):
        return f'{self.table_schema}.{self.table_name}'


class TableStore:
    def __init__(self, ignore_schemas: Sequence = ()):
        self.ignore_schemas = ignore_schemas
        self.engine = create_engine(
            f'postgresql+psycopg2://{os.getenv("USERNAME")}:{os.getenv("PASSWORD")}@'
            f'{os.getenv("HOST")}:{os.getenv("PORT")}/{os.getenv("DB_NAME")}'
        )
        self.engine.connect()
        self.data: list[FieldRow] = []

    def sync(self):
        session = Session(self.engine)
        result = session.execute(
            text('select table_schema, table_name, column_name from information_schema.columns'),
        ).fetchall()
        session.close()

        self.data = [
            FieldRow(table_schema, table_name, table_type)
            for table_schema, table_name, table_type in result
            if not (table_schema in self.ignore_schemas or table_schema.startswith('usr'))
        ]

    def schemas(self) -> list[str]:
        return list({row.table_schema for row in self.data})

    def schema_tables(self) -> Iterable[str]:
        tables = set()
        for row in self.data:
            tables.add(row.schema_table())

        yield from tables

    def table_fields(self, schema: str, table: str):
        for row in self.data:
            if row.table_schema == schema and row.table_name == table:
                yield row.column_name


def print_selected_indexed_fields(folder_with_sql_files: Path):
    """ Example how to select and print valuable fields for used project """
    # Select all engaged tables
    storage = TableStore(ignore_schemas=('pg_catalog',))
    storage.sync()

    # Gather all files into projects
    projects = []
    for project_path in folder_with_sql_files.iterdir():
        if project_path.name.startswith('.'):
            continue

        project = SQLProject(project_path)
        project.parse_variables(ignore_commands=ourTablesSignal)
        project.parse_files(ignore_commands=ourTablesSignal)
        projects.append(project)
        print(project)

    # Parse SQL files
    templated_scripts = []
    for project in projects:
        project.extract_tables()
        templated_scripts.extend(project.templated_scripts(ignore_strings=True))

    # Sync tables
    actual_tables = list(storage.schema_tables())
    existed_tables = []
    for project in projects:
        for query_src in project:
            tables = query_src.all_tables()
            existed_tables.extend([
                # Excluding non-schema tables
                table for table in tables if '.' in table
            ])

    templated_tables = [
        table for table in existed_tables
        if table.count('{') and table.count('}')
    ]
    just_tables = [
        table for table in existed_tables
        if table not in templated_tables
    ]
    print(f'Exactly correct tables: {len(set(just_tables) & set(actual_tables))}')
    suitable_tables = {}
    for templated_table in templated_tables:
        template = variables_extractor(templated_table)

        suitable_tables[template] = [
            table
            for table in actual_tables
            if re.match(template.regex, table)
        ]

    appr_tables = {table for tables in suitable_tables.values() for table in tables}
    print(f'Approximate tables: {len(appr_tables & set(actual_tables))}')
    work_tables = (appr_tables | set(just_tables)) & set(actual_tables)
    ready_tables = sorted(
        [w for w in work_tables if not w.startswith('mi.')] + ['mi.ns_push_firebase', 'mi.ts_position']
    )
    print(f'Overall tables: {len(work_tables)}')
    print(f'`Ready to work with` tables: {len(ready_tables)}')

    # Extract all used fields
    # Group fields by next chapters: [group by], [order by], [where], [limit-offset]
    table_name_statistics = {}
    for z, selected_table in enumerate(ready_tables):
        print(f'Processing: {z}/{len(ready_tables)} - {selected_table}')

        table_name_statistics[selected_table] = []
        try:
            template, template_tables = next(
                (template, tables) for template, tables in suitable_tables.items() if selected_table in tables
            )
            table_variants = [selected_table, template.raw, *template_tables]
        except StopIteration:
            table_variants = [selected_table]

        for i, actual_table in enumerate(table_variants):
            for j, project in enumerate(projects):
                for k, src in enumerate(project):
                    if actual_table in src.all_tables():
                        aliases = src.grab_all_aliases(table_name=actual_table)

                        if not src.grab_fields_select(table_name=actual_table, aliases=aliases):
                            raise ValueError('interesting')

                        table_record = {'path': src.path,
                                        'table': actual_table,
                                        'file_name': src.name,
                                        'aliases': aliases,
                                        'fields_select': src.grab_fields_select(table_name=actual_table,
                                                                                aliases=aliases),
                                        'fields_where': src.grab_fields_where(table_name=actual_table, aliases=aliases),
                                        'fields_ordered_by': src.grab_fields_order_by(table_name=actual_table,
                                                                                      aliases=aliases),
                                        'fields_grouped_by': src.grab_fields_group_by(table_name=actual_table,
                                                                                      aliases=aliases),
                                        'fields_limited': src.grab_fields_limit_offset(table_name=actual_table,
                                                                                       aliases=aliases)}
                        table_name_statistics[selected_table].append(table_record)

    final_result = {}
    for table, fields_group in table_name_statistics.items():
        fields_conditions = {}
        final_result[table] = fields_conditions

        for fields in fields_group:
            just_select = []
            calculated_fields = set()

            for f in fields['fields_select']:
                if ' ' not in f:
                    just_select.append(f)
                else:
                    suitable_fields = []
                    for word in f.split():
                        if is_service_word(word):
                            continue

                        if '::' in word:
                            word = word.split('::')[0]

                        if not word:
                            continue

                        parsed = word.split('.')

                        if len(parsed) > 1:
                            if parsed[0] in fields['aliases'] or parsed[0] == fields['table']:
                                suitable_fields.append(word[1])
                                calculated_fields.add(word[1])
                        else:
                            suitable_fields.append(word)
                            calculated_fields.add(word)

                    just_select.append(suitable_fields)

            conditionals = [
                *[
                    just_select[idx] if f.isdigit() else f
                    for f in fields['fields_where']
                    if not f.isdigit() or (idx := int(f)) < len(just_select)
                ],
                *[
                    just_select[idx] if f.isdigit() else f
                    for f in fields['fields_ordered_by']
                    if not f.isdigit() or (idx := int(f)) < len(just_select)
                ],
                *[
                    just_select[idx] if f.isdigit() else f
                    for f in fields['fields_grouped_by']
                    if not f.isdigit() or (idx := int(f)) < len(just_select)
                ],
                *[
                    just_select[idx] if f.isdigit() else f
                    for f in fields['fields_limited']
                    if not f.isdigit() or (idx := int(f)) < len(just_select)
                ],
            ]

            fields_conditions['conditionals'] = list(filter(None, conditionals + list(calculated_fields)))
            fields_conditions['just_select'] = list(filter(None, just_select + conditionals))

    for table, calculations in final_result.items():
        db_fields = list(storage.table_fields(*table.split('.')))
        select_fields = sorted({
            field
            for raw_field in calculations['just_select']
            for field in (raw_field if isinstance(raw_field, list) else [raw_field])
            if field in db_fields
        })
        index_fields = sorted({
            field
            for raw_field in calculations['conditionals']
            for field in (raw_field if isinstance(raw_field, list) else [raw_field])
            if field in db_fields
        })

        print(
            f'Table name: {table} | Fields: {len(db_fields)}',
            f'    Fields to select: [{" ".join(select_fields)}]',
            f'    Fields for indexing: [{" ".join(index_fields)}]',
            sep='\n'
        )
