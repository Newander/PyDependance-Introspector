from typing import Collection

import matplotlib as mpl
import matplotlib.pyplot as plt
import networkx as nx
from networkx import add_path


class GraphManager:
    """ Needed to create and draw graphs """

    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def add_nodes(self, node_names: Collection):
        add_path(self.graph, node_names)

        return self

    def create_edges(self, from_node: str, to_nodes: Collection[str]):
        self.graph.add_edges_from(
            ebunch_to_add=zip(([from_node] * len(to_nodes)), to_nodes)
        )

        return self
