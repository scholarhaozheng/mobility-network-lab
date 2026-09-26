# Hong Kong GMNS pilot R1 public candidate

This is a bounded Tsim Sha Tsui–Jordan instance built from official Hong Kong sources, with 95 fine zones, 10 parent zones, 1,239 directed physical road links, 190 nonphysical access arcs, 183 GTFS stops and one detector observation snapshot. It is a portability and relationship test, not a calibrated forecast. See `ATTRIBUTION.md` and `RIGHTS_AND_REDISTRIBUTION_REPORT.md` before reuse.

Offline review:

```text
python -B validate_pilot.py --instance instance
python -B trace_pilot.py --instance instance --zone 1 --detector AID05111 --stop 193
```

The first command checks saved-object relationships. `visuals/index.html` links five self-contained SVG views. No network access is needed. The assignment gate is false because speed, lanes, capacity and turn-enforced directed reachability are unresolved. The optional UrbanNav ground-truth points are private and absent from this candidate.
