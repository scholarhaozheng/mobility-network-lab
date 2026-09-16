# Input specification

The executable profile is `gmns_external_finite_network_v1`. It is a project-specific, GMNS-compatible profile, not a claim to implement every table in the full GMNS specification.

## Files and identifiers

| File | Required meaning | Example fields |
|---|---|---|
| `node.csv` | Nodes used by the allowed graph | `node_id` |
| `link.csv` | Directed physical links, travel time, fixed cost and capacity | `link_id,from_node_id,to_node_id,travel_time,cost,capacity` |
| `demand.csv` | OD identity, endpoints, departure and injected volume | `demand_id,origin_zone_id,destination_zone_id,departure_time,volume` |
| `zone_access.csv` | One access node per zone, when zone endpoints are used | `zone_id,node_id` |
| `case.json` | File mappings, model settings, units, seeds, CG and size limits | See the complete bundled configuration |

Identifiers are strings. Leading zeros and parallel links are retained. Node and zone IDs need not be equal. Blank IDs and reserved delimiters are rejected; demand IDs containing underscores are excluded by the retained engine's arc-ID parser. All file paths in the configuration are relative to the input directory.

Use [`app/cases/capacity_zone_probe/case.json`](../app/cases/capacity_zone_probe/case.json) as a complete executable configuration. A renamed field is not a unit conversion.

## Model profile

The current run interface uses a one-minute time step, positive integer link travel times, a common departure time, a fixed horizon, nonnegative fixed generalized costs and continuous path flows. Capacity is **vehicles per time-indexed movement arc**. Demand is **vehicles injected once at the declared departure time**.

Hourly traffic counts or capacity rates cannot be substituted without a documented conversion. A zero-time connector is not supported by this profile. Multiple access nodes per zone, mixed departure times and implicit unit conversion are also outside this version.

Automatic routes are ordered by travel time and then by link-ID sequence, not by generalized optimization cost. Initial routes do not define the allowed graph. Shared capacities may require Phase-I to add a route before the initial pool becomes feasible.

## Spatial metadata

Coordinates, geometric centerlines, area boundaries and TAZ polygons may be stored alongside solver inputs. The current solver profile does not require or invent them. A centroid point is not a zone polygon, and a straight-line network sketch is not surveyed road geometry.

## Demand and evidence

Record whether demand is observed, inferred, synthetic, or inherited from a benchmark. Keep observation time, units and mode separate from solver settings. GPS, traffic observations and GTFS should retain their source schema; future adapters must provide explicit mappings to this network's identifiers. These evidence adapters are not implemented by the present run command.

## Validation scope

The input command checks the declared file contract, attributes and identifiers. The solver performs graph/time feasibility checks. The result verifier recomputes checks from final outputs. These are distinct stages; consult [output semantics](outputs.md).
