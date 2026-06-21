"""
corridor-id v0.2 — Docker Compose parser

Reads a docker-compose.yml and builds a Topology.

Reachability rules:
- Services on the same Docker network can reach each other.
- A service with `ports` exposed is externally reachable (exposed=True).

No environment variable parsing. Reach is determined by network
membership only. This avoids false edges from substring matching.
"""

import yaml
from topology import Topology


def parse_compose(path):
    """Parse a docker-compose.yml file into a Topology."""

    with open(path, "r") as f:
        compose = yaml.safe_load(f)

    services = compose.get("services", {})
    topo = Topology()

    # Pass 1: register all nodes
    for name, config in services.items():
        exposed = "ports" in config and len(config["ports"]) > 0
        topo.add_node(name, exposed=exposed)

    # Pass 2: build network memberships
    # Track which services have explicit network declarations
    has_explicit_networks = set()

    for name, config in services.items():
        service_networks = config.get("networks", [])
        if isinstance(service_networks, dict):
            service_networks = list(service_networks.keys())
        if service_networks:
            has_explicit_networks.add(name)
            for net in service_networks:
                if net not in topo.networks:
                    topo.networks[net] = set()
                topo.networks[net].add(name)
                topo.nodes[name]["networks"].add(net)

    # Services without explicit networks join the default network
    # This applies even when other services use custom networks
    default_members = [
        name for name in services if name not in has_explicit_networks
    ]
    if default_members:
        topo.add_network("default", default_members)

    # Pass 3: build edges from shared networks
    for net_name, members in topo.networks.items():
        for member in members:
            for other in members:
                if member != other:
                    topo.add_edge(member, other)

    return topo
