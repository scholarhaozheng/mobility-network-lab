# Capability coverage and evidence scope

| Capability / evidence | Boston | Sioux Falls |
|---|---|---|
| GMNS network, zones and access | **Demonstrated:** H3 hierarchy, centroid/access and source-ID round-trip | **Benchmark network:** supplied topology and demand; not a present-day H3 city dataset |
| Population, households and activity preparation | **Demonstrated, limited:** ACS 2024 five-year block-group → H3 aggregate allocation; separate MassGIS activity proxy | **Not estimated:** supplied benchmark vehicle OD, no demographic build |
| Trip generation | **Demonstrated, limited:** ACS households + transferred purpose rates; activity attraction prior | **Not modeled:** benchmark demand is supplied |
| Trip distribution | **Demonstrated, limited:** saved gravity/IPF and PA-to-OD | **Not estimated:** given OD and selected subsets |
| Mode choice | **Demonstrated, conditional:** regional-share feedback and absolute DA/S2/S3/TW research branch | **Not modeled:** fixed vehicle demand |
| GPS / service evidence | **Demonstrated, exploratory:** network linkage and default-off interval feedback; no independent AM validation | **Not included** in the classic benchmark |
| Static Frank–Wolfe | **Demonstrated:** small controls and three expanded tiers, up to 17,522 loaded node ODs | **Demonstrated:** historical static benchmark; input-identity caveat retained |
| Finite full-path reference | **Solved:** 26-OD / 130-path control; **resource-gated** at expanded tiers | Used within the method/source framework; no equivalent solved full-path reference claimed by these supplied records |
| Native Diagnostic L3 / compression | **Accepted numerical controls:** ranks 26/52; new-input fixture; **not solved at expanded tiers** | **Executed numerical candidates:** rank 50; full-network gaps remain 8.17% / 4.38%, not exact UE |
| Space–time network construction | **Demonstrated, bounded:** 90-node / 125-directed-link / 10-OD accepted pilot, 3-second steps, 100-step horizon | **Demonstrated:** finite time-expanded 200 / 250-OD selected subsets |
| Phase I / Phase II / pricing | **Accepted bounded pilot:** same-graph reference-optimal and independently full-DAG pricing-closed for all ten demands at 1e−6; receiver check pending | **Historical 200 / 250 OD:** feasible and same-subset arc-LP objective matched; independent pricing closure **not established** |
| New-input preparation and solving | **Generic vehicle/person routes implemented**, with declared profiles and optional dependencies | Existing benchmark and external-network interfaces; case-specific scope is explicit |
| Saved checks and visualization | Tables, GMNS tracing, static original-space checks, bounded CG figure parity and R4 closure evidence | Static checks, space–time traces, phase and capacity evidence |

## Reading the matrix

**Demonstrated** means supplied executed records for the named instance, not every possible configuration. **Resource-gated** means the saved workflow stopped before the relevant solve under a stated resource budget; it is not a numerical success or proof of inherent impossibility. **Not modeled / no supplied run** is a case-coverage statement, not absence of reusable code. Numerical acceptance does not establish empirical validity.

The Boston all-tier FW, 26-OD compression control and 10-OD finite space–time CG pilot are different instances. Sioux static and time-expanded objectives differ. A generic new-input fixture does not turn the expanded native L3 tiers into accepted results. Boston's independent pricing certificate cannot be transferred to Sioux 200/250-OD records.

[Boston](cases/boston.md) · [Boston bounded CG evidence](cases/boston-space-time.md) · [Sioux Falls](cases/sioux-falls.md) · [Generic commands](RUN_YOUR_OWN_GMNS.md)
