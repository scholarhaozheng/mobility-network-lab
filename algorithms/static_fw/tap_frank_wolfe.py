import pandas as pd
import numpy as np
import time
import os
import sys
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import shortest_path


# --- Logger Setup ---
class Logger:
    def __init__(self, filename):
        self.terminal = sys.__stdout__  # Preserve the original stdout stream.
        self.log = open(filename, "w", encoding='utf-8')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

    def close(self):
        self.log.close()
        # Restore stdout after closing the log file.
        sys.stdout = self.terminal


def load_data(data_dir, cap_scale=1.0):
    print(f"Loading data from {data_dir}...")
    link_df = pd.read_csv(os.path.join(data_dir, 'link.csv'))
    demand_df = pd.read_csv(os.path.join(data_dir, 'demand.csv'))

    # 1. Map input columns.
    def get_col(df, candidates):
        for c in candidates:
            if c in df.columns: return c
        return None

    u_col = get_col(link_df, ['from_node_id', 'from_node', 'a_node', 'init_node'])
    v_col = get_col(link_df, ['to_node_id', 'to_node', 'b_node', 'term_node'])

    # 2. Build the node index.
    all_nodes = set(link_df[u_col].unique()) | set(link_df[v_col].unique())
    node_map = {n: i for i, n in enumerate(sorted(all_nodes))}
    n_nodes = len(node_map)
    n_links = len(link_df)

    u_idx = link_df[u_col].map(node_map).values
    v_idx = link_df[v_col].map(node_map).values

    # 3. Read parameters in float64 precision.
    cap_col = get_col(link_df, ['capacity', 'link_capacity', 'cap'])
    cap = link_df[cap_col].values.astype(np.float64)

    # Apply capacity scaling, primarily for all-day capacity inputs.
    cap = cap / cap_scale

    # Avoid division by zero.
    cap = np.maximum(cap, 1.0)

    t0 = link_df[get_col(link_df, ['vdf_fftt', 'free_flow_time', 'fftt'])].values.astype(np.float64)
    alpha = link_df.get('vdf_alpha', np.full(n_links, 0.15)).values.astype(np.float64)
    beta = link_df.get('vdf_beta', np.full(n_links, 4.0)).values.astype(np.float64)

    # 4. Read demand.
    o_col = get_col(demand_df, ['o_zone_id', 'origin'])
    d_col = get_col(demand_df, ['d_zone_id', 'destination'])
    vol_col = get_col(demand_df, ['volume', 'flow', 'demand'])

    od_demand = {}
    total_demand = 0
    for _, row in demand_df.iterrows():
        try:
            o_val = row[o_col]
            d_val = row[d_col]
            if o_val not in node_map or d_val not in node_map:
                continue

            o = node_map[o_val]
            d = node_map[d_val]
            vol = float(row[vol_col])

            if vol > 0:
                if o not in od_demand: od_demand[o] = {}
                od_demand[o][d] = od_demand[o].get(d, 0) + vol
                total_demand += vol
        except:
            continue

    # 5. Index parallel links.
    uv_to_links = {}
    for i in range(n_links):
        pair = (u_idx[i], v_idx[i])
        if pair not in uv_to_links: uv_to_links[pair] = []
        uv_to_links[pair].append(i)

    print(f"  Nodes: {n_nodes}, Links: {n_links}")
    print(f"  Total Demand: {total_demand:,.2f}")
    if cap_scale != 1.0:
        print(f"  [NOTE] Capacity Scaled by factor: {cap_scale} (Peak Hour Simulation)")

    return {
        'u': u_idx, 'v': v_idx, 'cap': cap, 't0': t0,
        'alpha': alpha, 'beta': beta, 'od': od_demand,
        'n_nodes': n_nodes, 'n_links': n_links, 'link_df': link_df,
        'uv_to_links': uv_to_links
    }


def bpr_cost(vol, cap, t0, alpha, beta):
    # Cost = t0 * (1 + alpha * (v/c)^beta)
    vc_ratio = vol / cap
    return t0 * (1.0 + alpha * np.power(vc_ratio, beta))


def bpr_integral(vol, cap, t0, alpha, beta):
    # Integral = t0*v + t0*alpha/(beta+1) * v * (v/c)^beta
    vc_ratio = vol / cap
    term_linear = np.sum(t0 * vol)
    # Guard against a zero beta + 1 denominator.
    term_congestion = np.sum((t0 * alpha / (beta + 1)) * vol * np.power(vc_ratio, beta))
    return term_linear + term_congestion, term_congestion


def build_min_graph(data, current_costs):
    """Build a graph using the lowest-cost link for each parallel pair."""
    n_nodes = data['n_nodes']
    u_list, v_list, w_list = [], [], []
    best_link_map = {}

    for (u, v), link_indices in data['uv_to_links'].items():
        best_idx = -1
        min_c = float('inf')
        for idx in link_indices:
            c = current_costs[idx]
            if c < min_c:
                min_c = c
                best_idx = idx
        u_list.append(u)
        v_list.append(v)
        w_list.append(min_c)
        best_link_map[(u, v)] = best_idx

    graph = coo_matrix((w_list, (u_list, v_list)), shape=(n_nodes, n_nodes)).tocsr()
    return graph, best_link_map


def get_aon_flow(data, cost):
    n_nodes = data['n_nodes']
    n_links = data['n_links']
    graph, best_link_map = build_min_graph(data, cost)
    aux_vol = np.zeros(n_links)

    # Compute distances and predecessors from each origin to all nodes.
    # This avoids a separate shortest-path call for every OD pair.
    for o, dests in data['od'].items():
        if not dests: continue

        dist, preds = shortest_path(graph, directed=True, indices=o, return_predecessors=True)

        # Backtrack only reachable destinations with demand.
        # Accumulate node flow from destinations toward the origin.
        node_load = np.zeros(n_nodes)

        # Sort reachable nodes from farthest to nearest so downstream flow
        # is accumulated before processing its predecessor.
        target_nodes = [d for d in dests.keys() if dist[d] != np.inf]

        if not target_nodes: continue

        # The predecessor structure is a shortest-path tree, even if the
        # underlying graph has cycles.
        active_nodes = np.where(dist != np.inf)[0]
        sorted_indices = np.argsort(dist[active_nodes])[::-1]
        sorted_nodes = active_nodes[sorted_indices]

        # Load OD demand at destination nodes.
        for d, f in dests.items():
            if dist[d] != np.inf:
                node_load[d] += f

        # Backtrack flow onto links.
        for n in sorted_nodes:
            if n == o: continue
            load = node_load[n]
            if load <= 1e-12: continue

            p = preds[n]
            if p >= 0:  # A predecessor exists.
                # Use the lowest-cost link from p to n.
                if (p, n) in best_link_map:
                    link_idx = best_link_map[(p, n)]
                    aux_vol[link_idx] += load

                # Propagate flow to the upstream node.
                node_load[p] += load

    return aux_vol


def golden_section_search(vol, target_vol, data):
    a, b = 0.0, 1.0
    gr = (np.sqrt(5) - 1) / 2
    tol = 1e-5
    d_vol = target_vol - vol

    # Precompute the invariant search direction.
    def func(lam):
        v_new = vol + lam * d_vol
        # Evaluate only the objective value.
        obj, _ = bpr_integral(v_new, data['cap'], data['t0'], data['alpha'], data['beta'])
        return obj

    c = b - gr * (b - a)
    d = a + gr * (b - a)
    fc, fd = func(c), func(d)

    while abs(c - d) > tol:
        if fc < fd:
            b = d
            d = c
            fd = fc
            c = b - gr * (b - a)
            fc = func(c)
        else:
            a = c
            c = d
            fc = fd
            d = a + gr * (b - a)
            fd = func(d)
    return (b + a) / 2


def solve_fw_refined(data_dir='.', run_name="default", max_iter=50, cap_scale=1.0):
    # Configure a log for this run.
    log_filename = f"{run_name}_fw_log.txt"
    sys.stdout = Logger(log_filename)

    start_total = time.time()

    try:
        data = load_data(data_dir, cap_scale=cap_scale)
    except FileNotFoundError:
        print(f"Error: Could not find data in {data_dir}")
        sys.stdout.close()
        return

    print(f"\n{'=' * 100}")
    print(f"Starting Refined Frank-Wolfe (Max Iter: {max_iter}) | Run: {run_name}")
    print(f"{'=' * 100}")
    print(
        f"{'Iter':<5} {'Objective':<15} {'LowerBound':<15} {'RelGap(%)':<12} {'Step':<8} {'CongestTerm':<12} {'Time':<6}")
    print("-" * 100)

    # 1. Initialize with free-flow all-or-nothing assignment.
    current_cost = data['t0']
    vol = get_aon_flow(data, current_cost)
    init_obj, init_cong = bpr_integral(vol, data['cap'], data['t0'], data['alpha'], data['beta'])
    print(f"{0:<5} {init_obj:<15.4e} {'-':<15} {'-':<12} {'(init)':<8} {init_cong:<12.2e} {0.00:<6.2f}")

    # Initialize values so max_iter=0 remains defined.
    new_obj = init_obj
    rel_gap = 1.0
    it = 0

    for it in range(1, max_iter + 1):
        iter_start = time.time()

        # 2. Update link costs.
        current_cost = bpr_cost(vol, data['cap'], data['t0'], data['alpha'], data['beta'])

        # 3. Find the all-or-nothing direction at current costs.
        target_vol = get_aon_flow(data, current_cost)

        # 4. Compute the lower bound and relative gap.
        # LB = Z(x) + grad(x) * (y - x)
        current_obj, _ = bpr_integral(vol, data['cap'], data['t0'], data['alpha'], data['beta'])
        direction = target_vol - vol
        directional_deriv = np.sum(current_cost * direction)
        lower_bound = current_obj + directional_deriv

        # Avoid a zero denominator.
        gap_denom = current_obj if current_obj > 1e-10 else 1.0
        rel_gap = abs(lower_bound - current_obj) / gap_denom

        # 5. Perform line search.
        step = golden_section_search(vol, target_vol, data)

        # 6. Update flows.
        vol = vol + step * direction
        new_obj, new_cong = bpr_integral(vol, data['cap'], data['t0'], data['alpha'], data['beta'])

        print(
            f"{it:<5} {new_obj:<15.4e} {lower_bound:<15.4e} {rel_gap * 100:<12.4f} {step:<8.4f} {new_cong:<12.2e} {time.time() - iter_start:<6.2f}")

        # Check convergence.
        if rel_gap < 1e-4:
            print(f"\n*** Converged (Gap < 0.01%) ***")
            break

    total_time = time.time() - start_total
    print(f"\nTotal Time: {total_time:.2f}s")
    print(f"Log saved to {log_filename}")

    # Save results.
    df = data['link_df'].copy()
    df['volume'] = vol
    df['travel_time'] = bpr_cost(vol, data['cap'], data['t0'], data['alpha'], data['beta'])
    df['vc_ratio'] = df['volume'] / df['capacity']  # Retain the source CSV capacity for comparison.

    out_csv = f"{run_name}_solution.csv"
    df.to_csv(out_csv, index=False)
    print(f"Results saved to {out_csv}")

    # Generate the baseline summary.
    avg_vc = df['vc_ratio'].mean()
    max_vc = df['vc_ratio'].max()

    print("\n" + "="*70)
    print("Baseline: Link-based Frank-Wolfe (User Equilibrium Ground Truth)")
    print("="*70)
    print(f"* Network:              {run_name.capitalize()}")
    print(f"* Solver:               Link-based FW (SciPy Shortest Path)")
    print(f"* Iterations:           {it}")
    print(f"* Total Objective:      {new_obj:,.4f}")
    print(f"* Relative Gap:         {rel_gap * 100:.4f}%")
    print(f"* Computational Time:   {total_time:.2f}s")
    print(f"* Average V/C Ratio:    {avg_vc:.4f}")
    print(f"* Max V/C Ratio:        {max_vc:.4f}")
    print("="*70 + "\n")
    # ------------------------------------

    # Close the log and restore console output.
    sys.stdout.close()

if __name__ == "__main__":
    # 1. Run the Chicago sketch in the current directory.
    # cap_scale=1.0 retains the original capacities.
    # A larger cap_scale (for example, 10.0 or 24.0) tests tighter capacities.
    print(">>> Running Chicago Sketch ...")
    solve_fw_refined('.', run_name="chicago", max_iter=30, cap_scale=1.0)

    # 2. Run Sioux Falls from data/SiouxFalls without capacity scaling.
    print("\n>>> Running Sioux Falls ...")
    solve_fw_refined('data/SiouxFalls', run_name="siouxfalls", max_iter=100, cap_scale=1.0)
