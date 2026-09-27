# Tsim Sha Tsui–Jordan bounded mobility case

This case continues the read-only Hong Kong R1 baseline. R1 identity and source-derived structure were reproduced before R2 compilation. The vehicle graph has directed physical IDs preserved through turn-aware link states. All 95 fine zones connect to the accepted strongly connected core; the straight zone-access proxies are explicitly unverified for barriers/water. Source turn prohibitions are enforced and mixed-elevation transitions require source intersections.

Phase A and B passed their saved gates. [Four-stage details](hong-kong-four-stage.md), [static assignment](hong-kong-static-assignment.md), [finite transfer](hong-kong-space-time.md), and [dataset contract](../datasets/hong-kong-gmns.md) contain the evidence and limits.

The first non-circumvented algorithm gate is frozen CG Phase I: nine ODs hit the fixed 50,000-state enumeration limit, leaving 4.3502187198 artificial PCE. ADMM R2 also failed its first local QP conservation gate. LP and Lagrangian R3 passed. The full four-method case is therefore **gated**, with no change to frozen numerical policies or selected ODs.
