"""
corridor-id v0.2 — Docker Compose parser

Reads a docker-compose.yml and builds a Topology.

Reachability rules:
- Services on the same Docker network can reach each other.
- A service with `ports` exposed is externally reachable (exposed=True).
- Environment variables containing service hostnames indicate
  explicit dependency (directional edge).
"""

import yaml
from topology import Topology


def parse_compose(path):
    """Parse a docker-compose.yml file into a Topology."""

    with open(path, "r") as f:
        compose = yaml.safe_load(f)

    services = compose.get("services", {})
    networks = compose.get("networks", {})
    topo = Topology()

    # Pass 1: register all nodes
    for name, config in services.items():
        exposed = "ports" in config and len(config["ports"]) > 0
        topo.add_node(name, exposed=exposed)

    # Pass 2: build network memberships
    for name, config in services.items():
        service_networks = config.get("networks", [])
        if isinstance(service_networks, dict):
            service_networks = list(service_networks.keys())
        for net in service_networks:
            if net not in topo.networks:
                topo.networks[net] = set()
            topo.networks[net].add(name)
            topo.nodes[name]["networks"].add(net)

    # If no explicit networks, all services share a default network
    if not any(config.get("networks") for config in services.values()):
        all_names = list(services.keys())
        topo.add_network("default", all_names)

    # Pass 3: build edges from shared networks
    for net_name, members in topo.networks.items():
        for member in members:
            for other in members:
                if member != other:
                    topo.add_edge(member, other)

    # Pass 4: refine edges from environment variables
    # Look for env vars that reference other service names
    service_names = set(services.keys())
    for name, config in services.items():
        env = config.get("environment", [])
        if isinstance(env, dict):
            env_values = list(env.values())
        elif isinstance(env, list):
            env_values = []
            for item in env:
                if "=" in item:
                    env_values.append(item.split("=", 1)[1])
        else:
            env_values = []

        for val in env_values:
            if not isinstance(val, str):
                continue
            for svc in service_names:
                if svc != name and svc in val:
                    topo.add_edge(name, svc)

    return topo
