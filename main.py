from pathlib import Path

import sys

from src.parser import Parser

if __name__ == '__main__':
    project = Path(sys.argv[1])
    parser = Parser(project)

    parser.extract_tree()
    parser.gather_objects()
    parser.build_link_list()

    # parser.create_report(report_dest)

    # import_graph = parser.create_import_graph()

    # parser.root.modules[7].get_imports()
    print(parser)

