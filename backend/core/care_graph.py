"""CareGraph: turn a dossier into a small deterministic relationship graph."""
from __future__ import annotations

import re
import json
import hashlib

from backend.models.schemas import CareGraph, CareGraphEdge, CareGraphNode, PatientProfile, RiskReport


def _slug(prefix: str, text: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:40] or "item"
    return f"{prefix}_{token}_{hashlib.sha256(text.encode()).hexdigest()[:8]}"


def build_care_graph(profile: PatientProfile, report: RiskReport) -> CareGraph:
    nodes: dict[str, CareGraphNode] = {}
    edges: list[CareGraphEdge] = []

    root = "profile"
    nodes[root] = CareGraphNode(id=root, label="Your Health Context", kind="profile")

    for condition in profile.chronic_conditions:
        cid = _slug("condition", condition)
        nodes[cid] = CareGraphNode(id=cid, label=condition, kind="condition")
        edges.append(CareGraphEdge(source=root, target=cid, relation="includes", severity="info"))

    for medication in profile.current_medications:
        mid = _slug("med", medication)
        nodes[mid] = CareGraphNode(id=mid, label=medication, kind="medication")
        edges.append(CareGraphEdge(source=root, target=mid, relation="medication", severity="info"))

    for idx, flag in enumerate(report.flags):
        fid = _slug(f"finding{idx}", flag.item)
        nodes[fid] = CareGraphNode(id=fid, label=flag.item, kind="finding")

        linked = False
        for restriction in flag.restrictions:
            cid = _slug("condition", restriction.condition)
            if cid not in nodes:
                nodes[cid] = CareGraphNode(id=cid, label=restriction.condition, kind="condition")
                edges.append(CareGraphEdge(source=root, target=cid, relation="relevant condition", severity="info"))
            label = "avoid" if restriction.classification == "fully_restricted" else "dose-sensitive"
            edges.append(CareGraphEdge(source=cid, target=fid, relation=label, severity=flag.severity))
            linked = True

        mechanism_lower = flag.mechanism.lower()
        for medication in profile.current_medications:
            if medication.lower() in mechanism_lower:
                mid = _slug("med", medication)
                edges.append(CareGraphEdge(source=mid, target=fid, relation="interaction context", severity=flag.severity))
                linked = True

        if not linked:
            edges.append(CareGraphEdge(source=root, target=fid, relation="finding", severity=flag.severity))

    return CareGraph(nodes=list(nodes.values()), edges=edges)


def care_graph_to_dot(graph: CareGraph) -> str:
    """Return Graphviz DOT without fixed colors; Streamlit/theme decides presentation."""
    lines = ['digraph CareGraph {', 'rankdir="LR";', 'node [shape="box", style="rounded"];']
    for node in graph.nodes:
        lines.append(f'"{node.id}" [label={json.dumps(node.label)}];')
    for edge in graph.edges:
        relation = edge.relation.replace('"', "'")
        lines.append(f'"{edge.source}" -> "{edge.target}" [label="{relation}"];')
    lines.append("}")
    return "\n".join(lines)
