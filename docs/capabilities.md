# Capability coverage and evidence scope

| Capability / evidence | Boston | Sioux Falls |
|---|---|---|
| GMNS network, zones and access | **Demonstrated:** H3 hierarchy, centroid/access and source-ID round-trip | **Benchmark network:** supplied topology and demand; not a present-day H3 city dataset |
| Trip generation | **Demonstrated, limited:** ACS households + transferred purpose rates; activity attraction prior | **Not modeled:** benchmark demand is supplied |
| Trip distribution | **Demonstrated, limited:** saved gravity/IPF and PA-to-OD | **Not estimated:** given OD and selected subsets |
| Mode choice | **Demonstrated, conditional:** regional-share feedback and absolute DA/S2/S3/TW research branch | **Not modeled:** fixed vehicle demand |
| GPS / service evidence | **Demonstrated, exploratory:** network linkage and default-off interval feedback; no independent AM validation | **Not included** in the classic benchmark |
| Static Frank–Wolfe | **Demonstrated:** small controls and three expanded tiers, up to 17,522 loaded node ODs | **Demonstrated:** historical static benchmark; input-identity caveat retained |
| Finite full-path reference | **Solved:** 26-OD / 130-path control; **resource-gated** at expanded tiers | Used within the method/source framework; no equivalent solved full-path reference claimed by these supplied records |
| Native Diagnostic L3 / compression | **Accepted numerical controls:** ranks 26/52; new-input fixture; **not solved at expanded tiers** | **Executed numerical candidates:** rank 50; full-network gaps remain 8.17% / 4.38%, not exact UE |
| Space–time network construction | **No Boston run supplied**; reusable code availability is not case execution | **Demonstrated:** finite time-expanded selected-OD instances |
| Phase I / Phase II / pricing | **No Boston CG result supplied** | **Historical runs:** 200 / 250 OD, objective-level arc-LP agreement |
| New-input preparation and solving | **Generic vehicle/person routes implemented**, with declared profiles and optional dependencies | Existing benchmark and external-network interfaces; case-specific scope is explicit |
| Saved checks and visualization | Tables, GMNS tracing, figures, original-space checks | Static checks, space–time traces, phase and capacity evidence |

## Reading the matrix

**Demonstrated** means supplied executed records for the named instance, not every possible configuration. **Resource-gated** means the saved workflow stopped before the relevant solve under a stated resource budget; it is not a numerical success or proof of inherent impossibility. **Not modeled / no supplied run** is a case-coverage statement, not absence of reusable code. Numerical acceptance does not establish empirical validity.

The Boston all-tier FW and 26-OD compression control are different instances. Sioux static and time-expanded objectives differ. A generic new-input fixture does not turn the expanded native L3 tiers into accepted results.

[Boston](cases/boston.md) · [Sioux Falls](cases/sioux-falls.md) · [Generic commands](RUN_YOUR_OWN_GMNS.md)
