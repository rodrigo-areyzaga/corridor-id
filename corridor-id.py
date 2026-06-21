#!/usr/bin/env python3
"""
corridor-id v0.2

Point it at a Docker Compose file.
It discovers the topology.
It identifies the corridor nodes.

Usage:
    python corridor-id.py <docker-compose.yml>
"""

import sys
from compose_parser import parse_compose
from identifier import identify_corridor_nodes


def main():
    if len(sys.argv) < 2:
        print("Usage: python corridor-id.py <docker-compose.yml>")
        sys.exit(1)

    path = sys.argv[1]
    print("corridor-id v0.2")
    print()

    # Parse
    topo = parse_compose(path)

    # Report topology
    print(f"Services found: {len(topo.all_nodes())}")
    print(f"Networks found: {len(topo.networks)}")
    print()

    print("Topology:")
    for node in topo.all_nodes():
        exposed = " [EXPOSED]" if topo.is_exposed(node) else ""
        reach = sorted(topo.can_reach(node))
        nets = sorted(topo.nodes[node]["networks"])
        print(f"  {node}{exposed}")
        print(f"    networks: {', '.join(nets) if nets else 'default'}")
        print(f"    can reach: {', '.join(reach) if reach else 'none'}")
    print()

    # Identify
    exposed_nodes, depth_map, corridor_nodes = identify_corridor_nodes(topo)

    if not exposed_nodes:
        print("No exposed services found.")
        print("corridor-id requires at least one service with exposed ports")
        print("to compute reach from an exposed surface.")
        print()
        return

    print(f"Exposed nodes: {', '.join(exposed_nodes)}")
    print()

    print("Depth map (hops from exposed surface):")
    for node in sorted(depth_map, key=lambda n: depth_map[n]):
        marker = " [EXPOSED]" if node in exposed_nodes else ""
        print(f"  {node}: depth {depth_map[node]}{marker}")
    print()

    if corridor_nodes:
        print(f"Corridor nodes found: {len(corridor_nodes)}")
        print()
        for cn in corridor_nodes:
            print(f"  → {cn['name']}")
            print(f"    Exposure distance: {cn['exposure_distance']}")
            print(f"    Forward reach gain: {cn['forward_reach_gain']}")
            print(f"    Reaches deeper nodes:")
            for target in cn["forward_reach_nodes"]:
                print(f"      - {target} (depth {depth_map[target]})")
            print()
    else:
        print("No corridor nodes found.")
        print("No non-exposed node expands forward reach from the exposed surface.")
    print()


if __name__ == "__main__":
    main()
