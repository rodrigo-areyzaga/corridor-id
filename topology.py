"""
giltzarri v0.2 — topology model

Format-agnostic representation of a service topology.
Nodes are services. Edges are reachability (which service can reach which).
Exposure is determined by whether a service has ports exposed externally.

The model answers one question:
Which nodes bridge exposure to reach?
"""


class Topology:
    """A directed graph of services and their reachability."""

    def __init__(self):
        self.nodes = {}       # name -> {"exposed": bool, "networks": set}
        self.edges = {}       # name -> set of names it can reach
        self.networks = {}    # network_name -> set of node names

    def add_node(self, name, exposed=False):
        if name not in self.nodes:
            self.nodes[name] = {"exposed": exposed, "networks": set()}
            self.edges[name] = set()

    def add_network(self, network_name, members):
        self.networks[network_name] = set(members)
        for member in members:
            if member in self.nodes:
                self.nodes[member]["networks"].add(network_name)

    def add_edge(self, source, target):
        if source in self.edges:
            self.edges[source].add(target)

    def is_exposed(self, name):
        return self.nodes.get(name, {}).get("exposed", False)

    def can_reach(self, name):
        return self.edges.get(name, set())

    def reachable_from(self, name):
        """Which nodes can reach this node?"""
        return {n for n, targets in self.edges.items() if name in targets}

    def all_nodes(self):
        return list(self.nodes.keys())
