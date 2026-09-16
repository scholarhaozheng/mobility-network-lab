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
        self.terminal = sys.__stdout__  # 保存原始 stdout
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
        # 恢复原始 stdout，防止日志文件没关掉
        sys.stdout = self.terminal


def load_data(data_dir, cap_scale=1.0):
    print(f"Loading data from {data_dir}...")
    link_df = pd.read_csv(os.path.join(data_dir, 'link.csv'))
    demand_df = pd.read_csv(os.path.join(data_dir, 'demand.csv'))

    # 1. 字段映射
    def get_col(df, candidates):
        for c in candidates:
            if c in df.columns: return c
        return None

    u_col = get_col(link_df, ['from_node_id', 'from_node', 'a_node', 'init_node'])
    v_col = get_col(link_df, ['to_node_id', 'to_node', 'b_node', 'term_node'])

    # 2. 构建节点映射
    all_nodes = set(link_df[u_col].unique()) | set(link_df[v_col].unique())
    node_map = {n: i for i, n in enumerate(sorted(all_nodes))}
    n_nodes = len(node_map)
    n_links = len(link_df)

    u_idx = link_df[u_col].map(node_map).values
    v_idx = link_df[v_col].map(node_map).values

    # 3. 参数读取
    # 强制 float64 精度
    cap_col = get_col(link_df, ['capacity', 'link_capacity', 'cap'])
    cap = link_df[cap_col].values.astype(np.float64)

    # [关键修改] 这里应用容量缩放，主要针对 Chicago 这种全天容量
    cap = cap / cap_scale

    # 避免除以 0
    cap = np.maximum(cap, 1.0)

    t0 = link_df[get_col(link_df, ['vdf_fftt', 'free_flow_time', 'fftt'])].values.astype(np.float64)
    alpha = link_df.get('vdf_alpha', np.full(n_links, 0.15)).values.astype(np.float64)
    beta = link_df.get('vdf_beta', np.full(n_links, 4.0)).values.astype(np.float64)

    # 4. 需求读取
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

    # 5. 平行路段预处理
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
    # 避免 beta+1 为 0 (虽然通常不会)
    term_congestion = np.sum((t0 * alpha / (beta + 1)) * vol * np.power(vc_ratio, beta))
    return term_linear + term_congestion, term_congestion


def build_min_graph(data, current_costs):
    """只取当前 Cost 最小的平行路段构建图"""
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

    # Scipy shortest_path 计算从 origin 到所有节点的距离和前驱
    # 这种方式比对每个 OD 对单独算 Dijkstra 要快得多
    for o, dests in data['od'].items():
        if not dests: continue

        dist, preds = shortest_path(graph, directed=True, indices=o, return_predecessors=True)

        # 优化：只对可达且有需求的目的地进行回溯
        # 1. 计算每个节点的累积流量 (从目的地倒推回 O)
        node_load = np.zeros(n_nodes)

        # 找出该 Origin 下所有的目的地，按距离从远到近排序 (拓扑逆序)
        # 这样可以保证我们处理一个节点时，它的下游流量已经累积完毕
        target_nodes = [d for d in dests.keys() if dist[d] != np.inf]

        if not target_nodes: continue

        # 这里的排序是为了确保拓扑顺序，对于有环图 Dijkstra 处理的是最短路树，也是无环的
        active_nodes = np.where(dist != np.inf)[0]
        sorted_indices = np.argsort(dist[active_nodes])[::-1]
        sorted_nodes = active_nodes[sorted_indices]

        # 加载 OD 需求到目的地节点
        for d, f in dests.items():
            if dist[d] != np.inf:
                node_load[d] += f

        # 回溯加载流量到链路
        for n in sorted_nodes:
            if n == o: continue
            load = node_load[n]
            if load <= 1e-12: continue

            p = preds[n]
            if p >= 0:  # 有前驱
                # 找到 (p, n) 之间最短的那条路段
                if (p, n) in best_link_map:
                    link_idx = best_link_map[(p, n)]
                    aux_vol[link_idx] += load

                # 将流量推给上游节点
                node_load[p] += load

    return aux_vol


def golden_section_search(vol, target_vol, data):
    a, b = 0.0, 1.0
    gr = (np.sqrt(5) - 1) / 2
    tol = 1e-5
    d_vol = target_vol - vol

    # 预计算不变的部分以加速
    def func(lam):
        v_new = vol + lam * d_vol
        # 我们只关心目标函数值
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
    # 配置特定运行的日志
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

    # 1. 初始解 (Free Flow AON)
    current_cost = data['t0']
    vol = get_aon_flow(data, current_cost)
    init_obj, init_cong = bpr_integral(vol, data['cap'], data['t0'], data['alpha'], data['beta'])
    print(f"{0:<5} {init_obj:<15.4e} {'-':<15} {'-':<12} {'(init)':<8} {init_cong:<12.2e} {0.00:<6.2f}")

    # 初始化变量，防止 max_iter=0 时报错
    new_obj = init_obj
    rel_gap = 1.0
    it = 0

    for it in range(1, max_iter + 1):
        iter_start = time.time()

        # 2. 更新阻抗
        current_cost = bpr_cost(vol, data['cap'], data['t0'], data['alpha'], data['beta'])

        # 3. 寻找方向 (All-or-Nothing assignment based on current cost)
        target_vol = get_aon_flow(data, current_cost)

        # 4. 计算 Lower Bound & Gap
        # LB = Z(x) + grad(x) * (y - x)
        current_obj, _ = bpr_integral(vol, data['cap'], data['t0'], data['alpha'], data['beta'])
        direction = target_vol - vol
        directional_deriv = np.sum(current_cost * direction)
        lower_bound = current_obj + directional_deriv

        # 避免分母为0
        gap_denom = current_obj if current_obj > 1e-10 else 1.0
        rel_gap = abs(lower_bound - current_obj) / gap_denom

        # 5. 线搜索
        step = golden_section_search(vol, target_vol, data)

        # 6. 更新流量
        vol = vol + step * direction
        new_obj, new_cong = bpr_integral(vol, data['cap'], data['t0'], data['alpha'], data['beta'])

        print(
            f"{it:<5} {new_obj:<15.4e} {lower_bound:<15.4e} {rel_gap * 100:<12.4f} {step:<8.4f} {new_cong:<12.2e} {time.time() - iter_start:<6.2f}")

        # 收敛判定
        if rel_gap < 1e-4:
            print(f"\n*** Converged (Gap < 0.01%) ***")
            break

    total_time = time.time() - start_total
    print(f"\nTotal Time: {total_time:.2f}s")
    print(f"Log saved to {log_filename}")

    # 保存结果
    df = data['link_df'].copy()
    df['volume'] = vol
    df['travel_time'] = bpr_cost(vol, data['cap'], data['t0'], data['alpha'], data['beta'])
    df['vc_ratio'] = df['volume'] / df['capacity']  # 这里的 capacity 是原始 CSV 里的，保持原样以便对比

    out_csv = f"{run_name}_solution.csv"
    df.to_csv(out_csv, index=False)
    print(f"Results saved to {out_csv}")

    # --- [新增] 自动生成 Baseline 报告 ---
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

    # 恢复控制台输出，关闭文件
    sys.stdout.close()

if __name__ == "__main__":
    # 1. 运行 Chicago (当前目录)
    # cap_scale=1.0 保持原样，展示"不堵"的情况
    # 如果你想看 Chicago 堵车，可以把 cap_scale 改成 10.0 或 24.0
    print(">>> Running Chicago Sketch ...")
    solve_fw_refined('.', run_name="chicago", max_iter=30, cap_scale=1.0)

    # 2. 运行 Sioux Falls (data/SiouxFalls)
    # Sioux Falls 不需要缩放，天生就堵
    print("\n>>> Running Sioux Falls ...")
    solve_fw_refined('data/SiouxFalls', run_name="siouxfalls", max_iter=100, cap_scale=1.0)