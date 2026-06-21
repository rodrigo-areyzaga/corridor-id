"""
corridor-id v0.2 — corridor node identifier

Given a Topology, identify corridor nodes.

A corridor node is a node that:
1. Is not itself exposed
2. Is reachable from an exposed node
3. Expands reach FORWARD — toward strictly greater depth from the exposed surface

Backward reach (toward shallower nodes) is not corridor movement.
No heuristics. No value labels. Graph position only.

Output is ranked by two metrics:
- exposure_distance: how close to the exposed surface
- forward_reach_gain: how many deeper nodes become reachable through this node
"""

from topology import Topology


def compute_depth_map(topo):
    """BFS from all exposed nodes. Each node gets minimum hop distance."""
    exposed = [n for n in topo.all_nodes() if topo.is_exposed(n)]
    depth = {}

    for exp in exposed:
        depth[exp] = 0

    queue = []
    for exp in exposed:
        for neighbor in topo.can_reach(exp):
            if neighbor not in depth:
                queue.append((neighbor, 1))

    while queue:
        node, d = queue.pop(0)
        if node in depth and depth[node] <= d:
            continue
        depth[node] = d
        for neighbor in topo.can_reach(node):
            if neighbor not in depth or d + 1 < depth[neighbor]:
                queue.append((neighbor, d + 1))

    return exposed, depth


def identify_corridor_nodes(topo):
    """
    Identify corridor nodes ranked by reach expansion from exposed surface.

    A corridor node expands forward reach — it provides access to nodes
    at strictly greater depth that are not directly reachable from
    exposed nodes.
    """
    exposed_nodes, depth_map = compute_depth_map(topo)
    corridor_nodes = []

    # What can exposed nodes reach directly (one hop)?
    exposed_direct_reach = set()
    for exp in exposed_nodes:
        exposed_direct_reach.update(topo.can_reach(exp))

    for node in depth_map:
        if topo.is_exposed(node):
            continue

        node_depth = depth_map[node]

        # Forward reach: nodes this node can reach at equal or greater depth
        forward_reach = []
        for target in topo.can_reach(node):
            if target in depth_map and depth_map[target] > node_depth and target != node:
                forward_reach.append(target)

        # Forward reach gain: forward-reachable nodes not directly reachable from exposed
        forward_reach_gain = [
            t for t in forward_reach if t not in exposed_direct_reach
        ]

        if not forward_reach_gain:
            continue

        corridor_nodes.append({
            "name": node,
            "exposure_distance": node_depth,
            "forward_reach_gain": len(forward_reach_gain),
            "forward_reach_nodes": sorted(forward_reach_gain),
            "reachable_from": sorted(topo.reachable_from(node)),
        })

    # Rank: closest to surface first, then by most forward reach gain
    corridor_nodes.sort(key=lambda x: (x["exposure_distance"], -x["forward_reach_gain"]))

    return exposed_nodes, depth_map, corridor_nodes
