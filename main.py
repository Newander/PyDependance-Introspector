from pathlib import Path

import sys

from src.parser import Parser

if __name__ == '__main__':
    mac_dir = '/Users/sergeygavrilov/PycharmProjects/ids_fssp'
    scheduler_dir = '/home/newander/PycharmProjects/etl_scheduler/dags'
    matcher_dir = '/home/newander/PycharmProjects/profiler_matcher'

    project = Path(sys.argv[1])
    report_dest = Path.cwd()

    parser = Parser(project)

    parser.extract_tree()
    parser.gather_objects()

    parser.build_link_list()
    # parser.create_report(report_dest)

    # import_graph = parser.create_import_graph()

    # parser.root.modules[7].get_imports()
    print(parser)

