from typing import Iterator

from src.py_parser.utils import FilePath, FolderPath, iter_through_files
from src.sql_parser.parser import Parser
from src.sql_parser.utils import parser


class SQLSource:
    """ Container for a SQL path and parser """

    def __init__(self, path: FilePath):
        self.path = path
        self.name = self.path.name
        self.query_text = self.path.read_text().replace('--', ' ')

        self.parser = Parser(
            self.path,
            self.query_text,
            parser(self.query_text.lower())
        )

    def __repr__(self):
        return f'<SQLSource [{self.path}]>'

    def parse_query(self):
        self.parser.parsing()


class SQLProject:
    """ Contains and manage a whole folder of SQL records """

    def __init__(self, path: FolderPath):
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
            print(f'Progress: {i + 1}/{len(self)}')
            print(f'Observing: {src.name}')
            try:
                src.parser.parsing()
                good += 1
            except Exception as err:
                bad += 1

        print(f'The overall result:\n\t- Overall:{len(self)}\n\t\t- {bad=}\n\t\t- {good=}')
