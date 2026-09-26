"""Lossless fixed-demand BPR static UE input contract and TNTP export.

This module does no assignment. It preserves physical directed link IDs and
uses 17 significant digits for all authoritative floating-point input.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _node(value):
    n = int(value)
    if str(n) != str(value).strip():
        raise ValueError(f"noninteger node ID {value!r}")
    return n


def load_problem(link_path, demand_path):
    link_path, demand_path = Path(link_path), Path(demand_path)
    links = []
    ids, pairs, nodes = set(), set(), set()
    for r in _rows(link_path):
        lid = str(r["link_id"])
        u, v = _node(r["from_node_id"]), _node(r["to_node_id"])
        if lid in ids or (u, v) in pairs or u == v:
            raise ValueError(f"duplicate/loop link {lid}: {u}->{v}")
        ids.add(lid); pairs.add((u, v)); nodes.update((u, v))
        vals = [float(r[k]) for k in ("capacity", "vdf_fftt", "vdf_alpha", "vdf_beta")]
        cap, fftt, alpha, beta = vals
        if not all(map(math.isfinite, vals)) or cap <= 0 or fftt <= 0 or alpha < 0 or beta < 1:
            raise ValueError(f"invalid BPR data on {lid}")
        length = float(r.get("length") or fftt)
        links.append(dict(link_id=lid, u=u, v=v, cap=cap, fftt=fftt,
                          alpha=alpha, beta=beta, length=length))
    if not links:
        raise ValueError("empty network")
    od = defaultdict(float)
    for r in _rows(demand_path):
        o = _node(r.get("o_zone_id") or r.get("o_node_id"))
        d = _node(r.get("d_zone_id") or r.get("d_node_id"))
        q = float(r["volume"])
        if not math.isfinite(q) or q < 0:
            raise ValueError("invalid OD demand")
        if o not in nodes or d not in nodes:
            raise ValueError(f"OD node absent from network: {o}->{d}")
        if o != d and q > 0:
            od[o, d] += q
    return dict(links=links, od=dict(od), nodes=sorted(nodes),
                zones=sorted(set(n for pair in od for n in pair)),
                link_source=str(link_path), demand_source=str(demand_path),
                link_sha256=sha256(link_path), demand_sha256=sha256(demand_path))


def export_tntp(problem, work):
    work = Path(work)
    net = work / "net"
    net.mkdir(parents=True, exist_ok=True)
    zones = problem["zones"]
    order = zones + [n for n in problem["nodes"] if n not in set(zones)]
    new = {old: i for i, old in enumerate(order, 1)}
    by_pair = {(l["u"], l["v"]): l["link_id"] for l in problem["links"]}
    lines = ["<NUMBER OF ZONES> " + str(len(zones)),
             "<NUMBER OF NODES> " + str(len(order)),
             "<FIRST THRU NODE> 1",  # OD endpoints are physical nodes.
             "<NUMBER OF LINKS> " + str(len(problem["links"])),
             "<END OF METADATA>", ""]
    for l in sorted(problem["links"], key=lambda x: (new[x["u"]], new[x["v"]])):
        fields = (new[l["u"]], new[l["v"]], l["cap"], l["length"],
                  l["fftt"], l["alpha"], l["beta"], 1, 0, 1)
        lines.append("\t".join(f"{x:.17g}" if isinstance(x, float) else str(x)
                               for x in fields) + "\t;")
    netpath = net / "r2_net.txt"
    netpath.write_text("\n".join(lines) + "\n", encoding="ascii")
    by_o = defaultdict(list)
    for (o, d), q in sorted(problem["od"].items()):
        by_o[new[o]].append((new[d], q))
    trip = [f"<NUMBER OF ZONES> {len(zones)}",
            f"<TOTAL OD FLOW> {sum(problem['od'].values()):.17g}",
            "<END OF METADATA>", ""]
    for o in range(1, len(zones) + 1):
        trip.append(f"Origin {o}")
        trip += [f" {d} : {q:.17g};" for d, q in by_o[o]]
        trip.append("")
    trippath = net / "r2_trips.txt"
    trippath.write_text("\n".join(trip) + "\n", encoding="ascii")
    mapping = dict(old_to_tntp={str(k): v for k, v in new.items()},
                   tntp_to_old={str(v): k for k, v in new.items()},
                   directed_pair_to_link_id={f"{u},{v}": lid for (u, v), lid in by_pair.items()},
                   first_thru_node=1, zone_nodes_are_physical=True,
                   node_count=len(order), zone_count=len(zones),
                   link_count=len(problem["links"]), od_count=len(problem["od"]),
                   total_demand=sum(problem["od"].values()),
                   input_hashes=dict(link=problem["link_sha256"], demand=problem["demand_sha256"]),
                   converted_hashes=dict(net=sha256(netpath), trips=sha256(trippath)))
    (work / "mapping.json").write_text(json.dumps(mapping, indent=2, sort_keys=True), encoding="utf-8")
    return mapping
