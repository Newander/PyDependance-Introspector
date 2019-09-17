from collections import namedtuple

from pyvis import network as net

from src.linker import Linker
from src.tree import Module


class GraphManager:
    """ Needed to create and draw graphs """
    height = 1000  # pixels
    width = 1000  # pixels

    def __init__(self, linker: Linker):
        self.linker = linker

    def create_import_graph(self):
        """ Creates graph from import objects in Linker """
        Edge = namedtuple('Edge', 'from_ to_')
        graph = net.Network(
            height=f'{self.height}px',
            width=f'{self.width}px',
        )

        for lib, descr in self.linker.items():
            edges_lst = []
            new_libs = set()
            new_modules = {lib}
            for import_ in descr['imports']:
                module = import_['module']

                if isinstance(module, Module):
                    to_edge = module.abs_import
                    new_modules.add(to_edge)
                else:
                    to_edge = str(module)
                    new_libs.add(to_edge)

                edges_lst.append(Edge(lib, to_edge))

            graph.add_nodes(
                list(new_libs),
                color=['#DBE129'] * len(new_libs)
            )
            graph.add_nodes(
                list(new_modules),
                color=['blue'] * len(new_modules)
            )
            graph.add_edges(edges_lst)

        return graph

    def save(self, graph: net.Network, path: str):
        """ Save any graph (with possible options) """
        # For debugging graph view
        graph.show_buttons(filter_=['nodes'])
        graph.save_graph(path)
