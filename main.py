import sys
from pathlib import Path

from src.parser import Parser

if __name__ == '__main__':
    project = Path(sys.argv[1])
    parser = Parser(project)

    parser.gather_objects()
    parser.build_link_list()

    parser.get_import_graph(
        '/home/newander/PycharmProjects/project_dependance_introspector/import_graph.html'
    )

    parser.print_stats()
