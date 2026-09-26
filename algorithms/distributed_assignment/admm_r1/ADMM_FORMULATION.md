# ADMM formulation, frozen before implementation

Let commodity `k` have nonnegative arc flow `x[k,a]`, incidence balance `B x[k] = b[k]`, and allowed-arc mask `M[k,a]`. Shared arc capacity is `sum_k z[k,a] <= u[a]`. Each commodity has a consensus copy `z[k,a]` and equality `x[k,a] = z[k,a]`.

The scaled augmented Lagrangian is `sum_k c^T x[k] + (rho/2) sum_(k,a) (x[k,a]-z[k,a]+w[k,a])^2` minus the constant squared-dual term. The local update minimizes this expression over `x[k]>=0`, `B x[k]=b[k]`, and forbidden connectors fixed at zero. This is a convex separable quadratic minimum-cost flow on the full allowed DAG. The global update projects `x+w` arc by arc onto `z[k,a]>=0, sum_k z[k,a]<=u[a]`, with forbidden connectors fixed at zero. The scaled dual update is `w <- w+x-z`.

Primal residual: `||x-z||_2`. Dual residual: `rho ||z-z_previous||_2`. The independently checked feasibility metrics are maximum commodity balance residual, maximum capacity excess, minimum flow, and forbidden connector flow. The objective is `sum c[a] x[k,a]`; it is reported as a feasible primal objective only if local conservation, consensus, and capacity tests pass. Fixed `rho=0.001`, no adaptation, 100 outer iterations, and the absolute/relative thresholds in `GATES.json` apply across Sioux cases. No reference optimum or reference path enters updates or stopping.

The local QP's Lagrange multipliers are node potentials. For potential `p`, the minimizing arc flow is `x = max(0, q-(c+B^T p)/rho)`, with `q=z-w`. A smooth convex dual in node potentials is minimized with L-BFGS-B; final conservation is checked separately. Local nonconvergence is a hard numerical gate, never silently projected into a feasible flow.
