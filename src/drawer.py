from collections import namedtuple

from pyvis import network as net

from src.linker import Linker


class GraphManager:
    """ Needed to create and draw graphs """

    def __init__(self, linker: Linker):
        self.linker = linker

    def create_import_graph(self):
        Edge = namedtuple('Edge', 'from_ to_')
        graph = net.Network(notebook=True)

        for lib, descr in self.linker.items():
            edges_lst = []
            edges_new = {lib}
            for import_ in descr['imports']:
                to_module = str(import_['module'])
                edges_lst.append(Edge(lib, to_module))
                edges_new.add(to_module)

            graph.add_nodes(edges_new)
            graph.add_edges(edges_lst)

        return graph

    def save(self, graph: net.Network, path: str):
        graph.save_graph(path)
