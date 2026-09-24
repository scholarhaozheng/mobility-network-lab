"""AST-isolated mathematical builder from run_diagnostic_levels.py.

Original source SHA-256: 0a054ab078d46a8b74fa257336a65275564c38cc3e60e5c4d8cb9c412a87a22a.
Only the function below is retained; its original AST is unchanged. Never import
the historical all-level driver, whose module body creates output directories.
"""

def build_alm_model_levels(data, comp, level=3, rho=1e4, lambda_od=None, gamma=1e-2):
    n_od, n_links = data['n_od'], data['n_links']
    n_major, r, M, D = comp['n_major'], comp['r'], comp['M'], comp['D']
    if lambda_od is None: lambda_od = np.zeros(n_od)

    B1_coo, A1_csr = comp['B1'].tocoo(), comp['A1']
    major_paths_for_link = defaultdict(list)
    for i in range(len(B1_coo.data)):
        if B1_coo.data[i] != 0: major_paths_for_link[B1_coo.col[i]].append(B1_coo.row[i])
    major_paths_for_od = {w: A1_csr.indices[A1_csr.indptr[w]:A1_csr.indptr[w + 1]].tolist() for w in range(n_od)}

    model = pyo.ConcreteModel()
    model.MAJOR, model.LINKS, model.ODS = pyo.RangeSet(0, n_major - 1), pyo.RangeSet(0, n_links - 1), pyo.RangeSet(0,
                                                                                                                   n_od - 1)
    if r > 0: model.LATENT = pyo.RangeSet(0, r - 1)

    model.x1 = pyo.Var(model.MAJOR, domain=pyo.NonNegativeReals, initialize=lambda m, p: max(comp['x1_ref'][p], 0.01))
    if r > 0: model.theta = pyo.Var(model.LATENT, domain=pyo.Reals, initialize=lambda m, j: comp['theta_ref'][j])
    model.v = pyo.Var(model.LINKS, domain=pyo.NonNegativeReals, bounds=(1e-8, None), initialize=0.1)

    U_r = comp['U_r']

    def obj_rule(m):
        routing_cost = sum(data['t0'][a] * m.v[a] + (data['t0'][a] * data['alpha'][a] / 5.0) * m.v[a] * (
                    (m.v[a] / max(data['capacity'][a], 1e-6)) ** 4) for a in m.LINKS)

        reg_cost = 0
        if gamma > 0:
            reg_x1 = sum((m.x1[p] - comp['x1_ref'][p]) ** 2 for p in model.MAJOR)
            reg_theta = sum((m.theta[j] - comp['theta_ref'][j]) ** 2 for j in range(r)) if r > 0 else 0
            reg_cost = (gamma / 2.0) * (reg_x1 + reg_theta)

        alm_penalty = 0
        if level in [2, 3]:
            alm_penalty = sum(
                lambda_od[w] * (sum(m.x1[p] for p in major_paths_for_od.get(w, [])) + (
                    sum(M[w, j] * m.theta[j] for j in range(r)) if r > 0 else 0) - data['demand'][w]) +
                0.5 * rho * (sum(m.x1[p] for p in major_paths_for_od.get(w, [])) + (
                    sum(M[w, j] * m.theta[j] for j in range(r)) if r > 0 else 0) - data['demand'][w]) ** 2
                for w in range(n_od)
            )

        return routing_cost + reg_cost + alm_penalty

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def link_rule(m, a):
        return m.v[a] == sum(m.x1[p] for p in major_paths_for_link.get(a, [])) + (
            sum(D[a, j] * m.theta[j] for j in range(r)) if r > 0 else 0)

    model.link_con = pyo.Constraint(model.LINKS, rule=link_rule)

    if level in [1, 3] and r > 0 and U_r is not None:
        n_minor_actual = U_r.shape[0]
        model.MINOR = pyo.RangeSet(0, n_minor_actual - 1)

        def minor_nonneg_rule(m, i):
            return sum(U_r[i, j] * m.theta[j] for j in range(r)) >= 0

        model.minor_con = pyo.Constraint(model.MINOR, rule=minor_nonneg_rule)

    return model, {'A1': A1_csr, 'M': M}
