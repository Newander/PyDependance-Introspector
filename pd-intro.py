import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from src.parser import Parser

parser = ArgumentParser()
parser.add_argument('project_path', help='Path to introspected project')
parser.add_argument(
    '-igpath', '--import-graph-path', help='Path to created file with import graph (in html)'
)
parser.add_argument(
    '-gw', '--graph-width', help='Width of the created graph', default=1600, type=int
)
parser.add_argument(
    '-gh', '--graph-height', help='Height of the created graph', default=1000, type=int
)

args: Namespace = parser.parse_args()

if __name__ == '__main__':
    project = Path(args.project_path)
    parser = Parser(project)

    parser.gather_objects()
    parser.build_link_list()

    if args.import_graph_path:
        parser.get_import_graph(
            args.import_graph_path,
            width=args.graph_width,
            height=args.graph_height,
        )

    parser.print_stats()
