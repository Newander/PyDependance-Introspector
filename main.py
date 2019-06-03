from pathlib import Path

from tree import Parser

if __name__ == '__main__':
    mac_dir = '/Users/sergeygavrilov/PycharmProjects/ids_fssp'
    venv_dir = '/home/newander/PycharmProjects/etl_scheduler/dags'

    project = Path(mac_dir)
    report_dest = Path.cwd()

    parser = Parser(project)

    parser.extract_tree()
    parser.gather_objects()
    parser.build_link_list()
    parser.create_report(report_dest)

    # parser.root.modules[7].get_imports()
    print(parser)

