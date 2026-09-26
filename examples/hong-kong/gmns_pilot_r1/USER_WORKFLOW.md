# Offline workflow

With Python 3.12+ from this public example directory:

```text
python -B validate_pilot.py --instance instance
python -B trace_pilot.py --instance instance --zone 1 --detector AID05111 --stop 193
```

`visuals/index.html` links the five self-contained public SVG figures. `validate_pilot.py --fixture duplicate_link` must exit 1; the other fixtures are `bad_connector` and `bad_demand`. No network request is needed to inspect the saved result. Rebuilding the original scientific extraction requires source snapshots and preparation scripts that are not in this public candidate; the public reproduction scope is offline validation and relationship tracing. UrbanNav point-level data remain excluded.
