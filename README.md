# giltzarri

> **Note:** This project was renamed from `corridor-id` to `giltzarri` as part of the Haritzarri tool family. The GitHub repository redirects automatically from the old name. No functional changes � this is a naming-only update.

**Given a topology, identify which nodes are corridor nodes.**

A corridor node is a node that expands forward reach from an exposed surface into deeper parts of the topology. It does not measure asset value. It measures reach expansion.

---

## The Premise

A node's risk is not determined only by what it stores. It is determined by where it sits in the path.

A low-value or no-data node can become important if it enables movement toward deeper, less-exposed parts of the environment.

## The Promise

Point the tool at a service topology. It identifies the corridor nodes. No human input beyond the topology file itself.

Currently ships with a Docker Compose parser. The core topology model is format-agnostic and has been validated against hand-built topologies with no parser involved.

## How It Works

The tool reads a Docker Compose file and builds a directed graph from:

- Service definitions (nodes)
- Network memberships (reachability)
- Port mappings (exposure)

It then computes depth from the exposed surface using BFS and identifies nodes that expand forward reach — nodes that provide access to strictly deeper parts of the topology that the exposed surface cannot reach directly.

The output is a ranked list of corridor nodes with two metrics:

- **Exposure distance** — how many hops from the nearest exposed node
- **Forward reach gain** — how many deeper nodes become reachable through this node

No asset-value labels. No human classification. Reach and graph position only.

---

## Usage

```bash
python giltzarri.py <docker-compose.yml>
```

Requires Python 3 and PyYAML:

```bash
pip install pyyaml
```

---

## Validation

The tool has been tested against four architecturally different Docker Compose topologies. Two produce corridor nodes. Two correctly produce none.

### corridor-lab — segmented topology with depth

Our own lab, designed to demonstrate path-indexed triage mismatch. Five services across five segmented networks.

```
Exposed: public-web

Corridor nodes found: 3

  → status-api
    Exposure distance: 1
    Forward reach gain: 1

  → log-monitor
    Exposure distance: 1
    Forward reach gain: 1

  → internal-admin-api
    Exposure distance: 2
    Forward reach gain: 1
```

The tool independently identified `status-api` as a corridor node — the same finding the lab was built to prove.

### OWASP crAPI — flat topology, no segmentation

Ten services on one default network. No explicit network segmentation.

```
Exposed: crapi-web, mailhog

Corridor nodes found: 0
```

Correct. Every service is directly reachable from the exposed surface in one hop. No node creates forward depth. No corridors exist because there are no walls.

### Sock Shop — segmented multi-service topology

Weaveworks microservices demo with production-reasonable network segmentation applied. Fifteen services across seven networks. The segmentation was applied for testing — it is not part of Sock Shop's original Compose file.

```
Exposed: edge-router

Corridor nodes found: 6

  → front-end
    Exposure distance: 1
    Forward reach gain: 6

  → orders
    Exposure distance: 2
    Forward reach gain: 3

  → shipping
    Exposure distance: 2
    Forward reach gain: 2

  → carts
    Exposure distance: 2
    Forward reach gain: 1

  → user
    Exposure distance: 2
    Forward reach gain: 1

  → catalogue
    Exposure distance: 2
    Forward reach gain: 1
```

`front-end` ranks first — it bridges the edge tier into six application services. `orders` ranks second — it bridges the app tier into both the data tier and the queue tier. The tool found these findings without any human input about service function or data sensitivity.

### Docker Example Voting App — segmented-looking but flat in practice

Five services with two networks (`front-tier` and `back-tier`). Both exposed services sit on both networks.

```
Exposed: vote, result

Corridor nodes found: 0
```

Correct. The segmentation does not create depth. Both exposed nodes bridge directly into the back tier. Every back-tier service is depth 1. No node expands forward reach because the exposed surface already touches everything.

This result proves the tool is not merely counting networks. It is measuring whether segmentation creates forward depth from the exposed surface.

### Summary

| Target | Services | Networks | Depth | Corridor nodes | Why |
|---|---|---|---|---|---|
| corridor-lab | 5 | 5 | 3 | 3 | Real segmentation, real depth |
| crAPI | 10 | 1 | 1 | 0 | Flat network, no depth |
| Sock Shop | 15 | 7 | 3 | 6 | Segmented, real depth |
| Voting App | 5 | 2 | 1 | 0 | Segmentation without depth |

---

## Architecture

Five files:

- `giltzarri.py` — entry point, reads Compose file, prints results
- `compose_parser.py` — Docker Compose parser, builds a Topology from YAML
- `topology.py` — format-agnostic graph model (nodes, edges, networks, exposure)
- `identifier.py` — corridor node identification logic (depth map, forward reach, ranking)
- `test_manual_topology.py` — proves the core logic works without any parser

The parser is a layer on top of the core logic. Today it reads Docker Compose. The topology model is format-agnostic — a Kubernetes or Terraform parser could produce the same Topology structure. `test_manual_topology.py` validates this claim by building a Topology by hand and running the identifier against it with no parser involved.

---

## What This Tool Does Not Do

- It does not assign value labels to services
- It does not use heuristics to guess service function
- It does not scan networks or probe running services
- It does not test whether corridor nodes have detection triggers
- It does not reconstruct attack paths or perform forensic analysis
- It does not require any human input beyond the Compose file

---

## Known Limitations

**Multiple exposed surfaces share a global depth map.** The tool computes depth from all exposed nodes simultaneously. If two exposed services exist and one of them directly reaches a target, that target's depth is set globally — which can suppress corridor findings from the other exposed service's perspective.

Example: if `public-a` reaches `target` only through `corridor-a`, but `public-b` reaches `target` directly, the tool may not flag `corridor-a` because `target` is already depth 1 globally.

This means the current model answers: *which nodes expand reach from the combined exposed surface?* It does not yet answer: *which nodes expand reach from each exposed surface individually?*

Per-exposed-surface analysis is planned for a future version.

**Localhost-bound ports are treated as exposed.** The tool treats any service with a `ports` mapping as exposed, including `127.0.0.1`-bound ports. A localhost-bound service is reachable from the Docker host but not from external networks. The tool does not currently distinguish between `0.0.0.0:8080:80` (externally exposed) and `127.0.0.1:8080:80` (host-only). Both are treated as exposed surfaces. This is a reasonable default — an attacker on the host can reach localhost-bound services — but it may overstate exposure in environments where host access is not part of the threat model.

**Compose profiles are not filtered.** Services declared under a `profiles` key may not run in the default deployment, but giltzarri includes them in the topology because they are part of the declared architecture. This can produce corridor findings for services that are defined but not active. The tool reads the Compose file as declared, not as deployed.

---

## Relationship to corridor-lab

[corridor-lab](https://github.com/rodrigo-areyzaga/corridor-lab) proves the premise: a service with no sensitive data can become high-priority because of where it sits in the path.

giltzarri delivers the promise: given a topology, identify which nodes are corridor nodes — automatically, from graph position alone.

corridor-lab is the proof. giltzarri is the tool.

---

## Development Note

This project was developed with AI assistance. Claude and ChatGPT were used as pair-programming and review tools. The concept, security framing, testing direction, and final implementation decisions were human-directed.
