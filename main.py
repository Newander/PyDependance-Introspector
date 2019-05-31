from pathlib import Path

from cla import Parser

if __name__ == '__main__':
    project = Path('/Users/sergeygavrilov/PycharmProjects/ids_fssp')
    report_dest = Path.cwd() / 'ids_fssp_tree.csv'

    parser = Parser(project)
    parser.extract_tree()

    print(parser)
    # parser.build_tree()
    # parser.create_report(report_dest)
