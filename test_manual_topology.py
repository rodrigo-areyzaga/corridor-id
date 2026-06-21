#!/usr/bin/env python3
"""
test_manual_topology.py

Proves that corridor-id's core logic works without any parser.
The Topology is built by hand — no Compose file, no YAML, no parser.

If this produces correct results, the topology model is format-agnostic.
"""

from topology import Topology
from identifier import identify_corridor_nodes

# Build a topology by hand — same structure as corridor-lab
topo = Topology()

topo.add_node("web-server", exposed=True)
topo.add_node("api-gateway")
topo.add_node("auth-service")
topo.add_node("database")

# web-server can reach api-gateway
topo.add_edge("web-server", "api-gateway")
topo.add_edge("api-gateway", "web-server")

# api-gateway can reach auth-service
topo.add_edge("api-gateway", "auth-service")
topo.add_edge("auth-service", "api-gateway")

# auth-service can reach database
topo.add_edge("auth-service", "database")
topo.add_edge("database", "auth-service")

# Run identifier
exposed, depth_map, corridors = identify_corridor_nodes(topo)

print("Manual topology test")
print()
print(f"Exposed: {exposed}")
print()
print("Depth map:")
for node in sorted(depth_map, key=lambda n: depth_map[n]):
    print(f"  {node}: depth {depth_map[node]}")
print()

if corridors:
    print(f"Corridor nodes found: {len(corridors)}")
    for cn in corridors:
        print(f"  → {cn['name']}")
        print(f"    Exposure distance: {cn['exposure_distance']}")
        print(f"    Forward reach gain: {cn['forward_reach_gain']}")
        print(f"    Reaches: {cn['forward_reach_nodes']}")
    print()
else:
    print("No corridor nodes found.")

# Verify expected results
assert exposed == ["web-server"], f"Expected web-server exposed, got {exposed}"
assert len(corridors) == 2, f"Expected 2 corridor nodes, got {len(corridors)}"
assert corridors[0]["name"] == "api-gateway", f"Expected api-gateway first, got {corridors[0]['name']}"
assert corridors[1]["name"] == "auth-service", f"Expected auth-service second, got {corridors[1]['name']}"

print("All assertions passed.")
print("The topology model is parser-independent.")
