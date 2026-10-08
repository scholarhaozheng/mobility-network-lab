"""Plot Berkeley S72 frozen endpoints only. No solver imports or executions."""
from pathlib import Path
import inspect, json, math
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import PowerNorm, TwoSlopeNorm
from matplotlib.ticker import FuncFormatter
from shapely import wkt
import plot_common as pc

HERE = Path(__file__).resolve().parent
METHODS = ['FW', 'Finite', 'Native 26', 'Native 52']
COLORS = [pc.INK, pc.BLUE, pc.TEAL, '#527f92']
MAP_ORIGIN = (-122.27, 37.87)


def geometry():
    rows = pc.read_csv('physical_geometry.csv')
    assert len(rows) == len({r['link_id'] for r in rows}) == 2150
    segments = []
    for r in rows:
        g = wkt.loads(r['geometry_wkt'])
        assert g.geom_type == 'LineString'
        xy = np.asarray(g.coords)
        xy[:, 0] = (xy[:, 0] - MAP_ORIGIN[0]) * 111.320 * math.cos(math.radians(MAP_ORIGIN[1]))
        xy[:, 1] = (xy[:, 1] - MAP_ORIGIN[1]) * 110.574
        segments.append(xy)
    return rows, segments


def title(ax, letter, text):
    ax.set_title(letter + '  ' + text, loc='left', fontsize=10, fontweight='bold', pad=9)
    pc.format_axes(ax)


def physical_map(ax, segments, flows, norm, cmap=pc.FLOW_CMAP, signed=False):
    ax.add_collection(LineCollection(segments, colors=pc.ROAD, linewidths=.38, zorder=1))
    vmax = max(abs(float(norm.vmin)), abs(float(norm.vmax)), 1e-30)
    # All positive saved values are retained; no scientific support threshold filters the map.
    keep = np.flatnonzero(np.abs(flows) > 0)
    widths = .4 + 1.35 * np.sqrt(np.abs(flows[keep]) / vmax)
    lc = LineCollection([segments[i] for i in keep], array=flows[keep], cmap=cmap,
                        norm=norm, linewidths=widths, zorder=2)
    ax.add_collection(lc)
    vertices = np.concatenate(segments)
    pad = np.ptp(vertices, axis=0) * .025
    ax.set_xlim(vertices[:, 0].min() - pad[0], vertices[:, 0].max() + pad[0])
    ax.set_ylim(vertices[:, 1].min() - pad[1], vertices[:, 1].max() + pad[1])
    pc.format_axes(ax, map_axis=True)
    ax.set_xlabel('East of display origin (km)')
    ax.set_ylabel('North of display origin (km)')
    return lc


def save(fig, stem, figure_title, caption, panels, sources, data, function):
    record = pc.save(fig, stem, figure_title, 'S72 / bounded static assignment', caption,
                     panels, sources, plot_data=data)
    lines, start = inspect.getsourcelines(function)
    record['renderer'] = {'path': 'render_static.py', 'sha256': pc.sha(__file__),
                          'function': function.__name__, 'line_start': start,
                          'line_end': start + len(lines) - 1}
    record['coordinate_transform'] = {
        'purpose': 'Display only, same local-linear-kilometre convention as the Boston atlas',
        'origin_lon_lat': list(MAP_ORIGIN),
        'x_km': '(longitude + 122.27) * 111.320 * cos(37.87 degrees)',
        'y_km': '(latitude - 37.87) * 110.574',
        'scientific_geometry_altered': False}
    record['scope'] = 'One saved S72 engineering scenario, 72 positive vehicle OD pairs, 953.049842713612 PCE in one declared hour; no observed-traffic calibration, uncertainty sample, or new solver run.'
    (pc.OUT / (stem + '.source.json')).write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    return record


def s01_geography_pool():
    rows, segments = geometry()
    source = pc.read_json('s01_geography_pool.plot_data.json')
    sparse = {str(r['link_id']): float(r['flow_pce']) for r in source['positive_links']}
    assert len(sparse) == 670 and set(sparse).issubset({r['link_id'] for r in rows})
    flows = np.array([sparse.get(r['link_id'], 0.0) for r in rows])
    geometry_flow = np.array([float(r['flow_pce_per_hour']) for r in rows])
    assert np.allclose(flows, geometry_flow, atol=1e-12, rtol=0)
    assert source['path_count'] == 360 and source['od_count'] == 72
    origin = list(source['origin_q_pce'].items())
    pool = pc.read_json('s72_pool_structure.json')
    assert pool['total'] == 360 and pool['major_rank_in_od_0'] == 72 and pool['minor_other_ranks'] == 288
    assert math.isclose(sum(v for _, v in origin), 953.049842713612, abs_tol=1e-9)
    fig = pc.new_figure('berkeley', 'S72 flow support and frozen path pool',
                        'S72 / SAVED FW ENDPOINT', figsize=(11.1, 8.5))
    ax = fig.add_axes([.075, .51, .54, .285]); title(ax, 'a', 'Full physical graph')
    lc = physical_map(ax, segments, flows, PowerNorm(gamma=.5, vmin=0, vmax=flows.max()))
    cax = fig.add_axes([.64, .515, .013, .275])
    cb = fig.colorbar(lc, cax=cax, orientation='vertical')
    cb.set_label('Saved FW physical-link flow (PCE/h)')
    cb.set_ticks([0, 25, 100, 225, float(flows.max())])
    cb.set_ticklabels(['0', '25', '100', '225', '390.3'])
    ax = fig.add_axes([.80, .515, .175, .275]); title(ax, 'b', 'Frozen K = 5 pool')
    ranks = list(range(5)); rank_counts = [pool['rank_counts'][str(k)] for k in ranks]
    ax.barh(ranks, rank_counts, height=.64, color=[pc.BLUE] + [pc.TEAL]*4)
    ax.set_yticks(ranks, ['Major', 'Minor 1', 'Minor 2', 'Minor 3', 'Minor 4'])
    ax.invert_yaxis(); ax.set_xlim(0, 88); ax.set_xlabel('Path count')
    for y, count in zip(ranks, rank_counts): ax.text(count+2, y, str(count), va='center', fontsize=8)
    ax = fig.add_axes([.075, .105, .395, .25]); title(ax, 'c', 'All 2,150 link flows')
    bins = np.linspace(0, 400, 21)
    counts, _, _ = ax.hist(flows, bins=bins, color=pc.TEAL, edgecolor='white', linewidth=.45)
    ax.set_yscale('log'); ax.set_ylim(.8, 4000)
    ax.set_xlabel('Physical-link flow (PCE/h)'); ax.set_ylabel('Link count (log scale)')
    ax.text(.98, .93, '670 links > 10⁻⁸ PCE/h\n1,480 exact zeros', transform=ax.transAxes,
            ha='right', va='top', fontsize=8)
    ax = fig.add_axes([.58, .105, .395, .25]); title(ax, 'd', 'Demand at the 9 active origins')
    labels = [k.rsplit(':', 1)[-1][5:] for k, v in origin]
    values = [v for k, v in origin]
    ax.bar(np.arange(len(values)), values, width=.72, color=pc.BLUE)
    ax.set_xticks(np.arange(len(values)), labels, rotation=55, ha='right')
    ax.set_xlabel('Origin tract suffix (full ID in plot data)')
    ax.set_ylabel('Origin demand (PCE/h)'); ax.set_ylim(0, 405)
    ax.text(.02, .96, '72 OD pairs · K = 5 · 360 paths', transform=ax.transAxes,
            ha='left', va='top', fontsize=8, color=pc.INK)
    caption = ('Saved Berkeley S72 FW endpoint on all 2,150 frozen directed physical road links. '
               'The 670 positive entries are left-joined by persistent link ID; the other 1,480 links are exactly zero, '
               'verified against the complete saved physical-link table. The flow map uses all original road vertices, '
               'square-root colour normalization and widths, and local display kilometres; its gray background retains the full graph. '
               'The histogram includes all 2,150 links, including exact zeros in the first bin, with logarithmic count only. '
               'The nine positive origin totals sum to 953.049842713612 PCE in the one-hour model. '
               'The frozen K=5 pool has 360 paths for 72 OD pairs: one designated major and four minor paths per OD, '
               '72 major and 288 minor in total. The candidate paths and access points are not drawn in this new map. '
               'This is an uncalibrated engineering scenario, not surveyed traffic. © OpenStreetMap contributors, ODbL 1.0. '
               'Saved-result derivative; the original accepted source figure remains available.')
    panels = [
        {'id': 'a', 'metric': 'FW physical-link flow', 'unit': 'PCE/h', 'rows': 2150,
         'transform': 'PowerNorm(gamma=0.5); line width=0.4+1.35*sqrt(flow/maxflow); all nonzero values retained',
         'join': 'positive_links left-joined to physical_geometry.link_id; absent values independently verified zero'},
        {'id': 'b', 'metric': 'path count by rank_in_od', 'unit': 'path count', 'rows': 360,
         'transform': 'groupby rank_in_od; 0 designated major; ranks 1..4 minor'},
        {'id': 'c', 'metric': 'all-link flow histogram', 'x_unit': 'PCE/h', 'y_unit': 'physical-link count',
         'transform': '20 equal bins over [0,400]; logarithmic count axis; zero-flow rows remain in first bin', 'rows': 2150},
        {'id': 'd', 'metric': 'origin_q_pce', 'unit': 'PCE/h in one declared hour', 'rows': 9,
         'transform': 'none; tract label suffix after five-character state/county prefix'}]
    data = {'input_saved_plot_data': source, 'path_pool_structure': pool, 'full_graph_flow_by_link': [
        {'link_id': r['link_id'], 'fw_pce_per_hour': float(f)} for r, f in zip(rows, flows)],
        'histogram': {'edges_pce_per_hour': bins.tolist(), 'counts': counts.astype(int).tolist()},
        'checks': {'full_graph_rows': len(rows), 'positive_gt_1e_8': int(np.count_nonzero(flows > 1e-8)),
                   'exact_zero': int(np.count_nonzero(flows == 0)),
                   'max_difference_from_full_geometry_flow': float(np.max(np.abs(flows-geometry_flow)))}}
    return save(fig, 's01_geography_pool', 'S72 flow support and frozen path pool', caption, panels,
                ['s01_geography_pool.plot_data.json', 'physical_geometry.csv', 's72_pool_structure.json'], data, s01_geography_pool)


def s02_same_instance_methods():
    source = pc.read_json('s02_same_instance_methods.plot_data.json')
    definitions = pc.read_json('s72_diagnostic_definition.json')
    methods = source['methods']
    assert len(methods) == 4
    gaps = np.array([m['full_relative_gap'] for m in methods])
    assert gaps[2] < 0 and all(m['status'] == 'ACCEPTED_FULL_GRAPH' for m in methods)
    delta = np.array(source['objective_difference_to_FW_micro_pce_min'])
    assert np.allclose(delta, [(m['objective_pce_minutes'] - methods[0]['objective_pce_minutes'])*1e6 for m in methods], rtol=0, atol=1e-12)
    rows, _ = geometry(); links = len(rows)
    representation = [360, methods[2]['coordinate_count'], methods[3]['coordinate_count']]
    assert representation == [360, 98, 124]
    fig = pc.new_figure('berkeley', 'S72 same-instance method diagnostics',
                        'S72 / FOUR SAVED TERMINAL RESULTS', figsize=(11.4, 8.3))
    gs = fig.add_gridspec(2, 2, left=.075, right=.97, bottom=.09, top=.8, hspace=.68, wspace=.33)
    xs = np.arange(4)
    ax = fig.add_subplot(gs[0, 0]); title(ax, 'a', 'Objective difference from FW')
    ax.axhline(0, color='#9ba4a8', linewidth=.6)
    ax.bar(xs, delta, color=COLORS, width=.57, zorder=2)
    ax.scatter(xs, delta, color=COLORS, s=21, zorder=3)
    for x, y, label in zip(xs, delta, ['0', '0', '−0.0001933', '+0.4838403']):
        ax.annotate(label, (x, y), xytext=(0, 8 if y >= 0 else -15), textcoords='offset points', ha='center', fontsize=8)
    ax.set_xticks(xs, METHODS); ax.set_ylim(-.065, .61)
    ax.set_ylabel('Objective − FW (10⁻⁶ PCE·min)')
    ax.text(.02, .94, 'FW = 2,746.0944149794555 PCE·min', transform=ax.transAxes, fontsize=7.7, va='top')
    ax = fig.add_subplot(gs[0, 1]); title(ax, 'b', 'Signed full-graph relative gap')
    ax.axhline(0, color='#9ba4a8', linewidth=.6)
    ax.axhline(1e-5, color='#bb6749', linestyle='--', linewidth=.9)
    ax.axhline(-1e-5, color='#bb6749', linestyle='--', linewidth=.9)
    ax.text(.02, .90, 'Accepted gate: |gap| ≤ 10⁻⁵', transform=ax.transAxes, fontsize=8, va='top', color='#985134')
    ax.scatter(xs, gaps, c=COLORS, s=32, zorder=3)
    ax.set_ylim(-2e-4, 2e-4)
    ax.set_yscale('symlog', linthresh=1e-14, linscale=1)
    for x, y, label in zip(xs, gaps, ['4.97 × 10⁻¹⁶', '4.97 × 10⁻¹⁶', '−7.00 × 10⁻¹⁴', '1.76 × 10⁻¹⁰']):
        ax.annotate(label, (x, y), xytext=(0, -14 if y < 0 else 10), textcoords='offset points', ha='center', fontsize=7.8)
    ax.set_xticks(xs, METHODS); ax.set_xlim(-.45, 3.45)
    ax.set_yticks([-1e-5, -1e-10, -1e-13, 0, 1e-13, 1e-10, 1e-5])
    ax.set_yticklabels(['−10⁻⁵', '−10⁻¹⁰', '−10⁻¹³', '0', '10⁻¹³', '10⁻¹⁰', '10⁻⁵'])
    ax.set_ylabel('Signed relative gap (symmetric log)')
    ax = fig.add_subplot(gs[1, 0]); title(ax, 'c', 'Original-coordinate residuals')
    od = np.array([m['max_od_residual'] for m in methods]) * 1e10
    recon = np.array([m['max_link_reconstruction'] for m in methods]) * 1e10
    ax.barh(xs+.12, od, height=.22, color=pc.TEAL, label='Maximum OD mass residual')
    ax.barh(xs-.12, recon, height=.22, color=pc.BLUE, label='Maximum link reconstruction residual')
    for y, o, r in zip(xs, od, recon):
        ax.scatter([o, r], [y+.12, y-.12], marker='|', s=25, color=[pc.TEAL, pc.BLUE], zorder=3)
        ax.annotate(f'{o:.4g}', (o, y+.12), xytext=(5, -3), textcoords='offset points', fontsize=7.6)
        ax.annotate(f'{r:.4g}', (r, y-.12), xytext=(5, -3), textcoords='offset points', fontsize=7.6)
    ax.set_yticks(xs, METHODS); ax.invert_yaxis(); ax.set_xlim(-.015, 1.42)
    ax.set_xlabel('Maximum absolute residual (10⁻¹⁰ PCE)')
    ax.legend(loc='lower left', bbox_to_anchor=(0, -.47), fontsize=7.5)
    ax = fig.add_subplot(gs[1, 1]); title(ax, 'd', 'Representation and explicit variables')
    ys = np.arange(3)
    explicit = [0, links, links]
    ax.barh(ys, representation, color=pc.TEAL, height=.54, label='Path representation coordinates')
    ax.barh(ys, explicit, left=representation, color=pc.BLUE, alpha=.78, height=.54, label='Native explicit physical-link variables')
    for y, coord, extra in zip(ys, representation, explicit):
        ax.text(coord+extra+35, y, f'{coord+extra:,}', va='center', fontsize=8)
        ax.text(12, y, str(coord), color='white', weight='bold', va='center', fontsize=7.3)
        if extra: ax.text(coord+extra/2, y, '2,150 links', ha='center', va='center', color='white', fontsize=8)
    ax.set_yticks(ys, ['Finite path', 'Native 26', 'Native 52']); ax.invert_yaxis()
    ax.set_xlim(0, 2670); ax.set_xlabel('Variable / coordinate count')
    ax.legend(loc='lower left', bbox_to_anchor=(0, -.47), fontsize=7.5)
    caption = ('Four saved terminal checks of the same S72 graph, demand, BPR coefficients and K=5 pool; '
               'all four have ACCEPTED_FULL_GRAPH status. (a) The saved objective minus the FW objective is shown in micro PCE·minutes; '
               'the tiny rank-26 negative difference is retained. (b) The signed full-graph relative gaps use a symmetric-log display with '
               'a linear interval of ±10⁻¹⁴. Both bounds of the accepted |full-graph relative gap| ≤ 10⁻⁵ gate are shown; no positive value is clipped, '
               'and the negative rank-26 numerical gap is not converted to an absolute value. (c) Maximum OD mass and '
               'physical-link reconstruction residuals are shown on a linear axis in 10⁻¹⁰ PCE; exact zeros remain zero. '
               '(d) The finite pool has 360 path coordinates. Native ranks 26 and 52 use 98 and 124 representation coordinates '
               '(72 major plus rank), but each also contains 2,150 explicit physical-link variables, for raw totals of 2,248 and 2,274. '
               'Thus the compact path representation is not a claim of fewer total variables or faster computation. '
               'Native records contain three outer iterations per rank; this terminal comparison is not a convergence trace. '
               'Only one engineering scenario is shown, with no uncertainty interval or measured-traffic validation.')
    panels = [
        {'id': 'a', 'metric': '(saved_objective - saved_FW_objective) * 1e6', 'unit': 'micro PCE·min', 'rows': 4, 'transform': 'linear; signed'},
        {'id': 'b', 'metric': 'full_relative_gap', 'unit': 'dimensionless', 'rows': 4,
         'transform': 'symlog(linthresh=1e-14,linscale=1)', 'scientific_gate': '|full_relative_gap| <= 1e-5',
         'formula': definitions['full_relative_gap_formula'], 'negative_signed_value_retained': True},
        {'id': 'c', 'metric': ['max_od_residual', 'max_link_reconstruction'], 'unit': 'PCE', 'rows': 4,
         'transform': 'multiply by 1e10 for linear display; exact zeros preserved'},
        {'id': 'd', 'metric': 'finite path coordinates; Native major-plus-rank coordinates and explicit physical-link variables',
         'unit': 'count', 'rows': 3, 'transform': 'stacked counts; no speed or total-dimension advantage claim'}]
    data = {'saved_terminal_results': source, 'diagnostic_definitions': definitions, 'dimensions': [
        {'method': 'finite_SLSQP', 'path_coordinates': 360, 'native_explicit_link_variables': 0, 'display_total': 360},
        {'method': 'Native_L3_rank26', 'path_coordinates': 98, 'native_explicit_link_variables': links, 'display_total': 98+links},
        {'method': 'Native_L3_rank52', 'path_coordinates': 124, 'native_explicit_link_variables': links, 'display_total': 124+links}],
        'diagnostic_display_scale': 1e10, 'signed_gap_display_linear_threshold': 1e-14}
    return save(fig, 's02_same_instance_methods', 'S72 same-instance method diagnostics', caption, panels,
                ['s02_same_instance_methods.plot_data.json', 'physical_geometry.csv', 's72_diagnostic_definition.json'], data, s02_same_instance_methods)


def s03_native_flows():
    rows, segments = geometry()
    saved = pc.read_csv('s72_physical_flow.csv')
    by_id = {r['link_id']: r for r in saved}
    assert len(saved) == len(by_id) == 2150 and set(by_id) == {r['link_id'] for r in rows}
    columns = ['FW_flow_pce_per_hour', 'Native26_flow_pce_per_hour', 'Native52_flow_pce_per_hour']
    flows = [np.array([float(by_id[r['link_id']][col]) for r in rows]) for col in columns]
    finite = np.array([float(by_id[r['link_id']]['finite_flow_pce_per_hour']) for r in rows])
    assert np.allclose(flows[0], finite, atol=1e-12, rtol=0)
    difference = [flows[1]-flows[0], flows[2]-flows[0]]
    for d, col in zip(difference, ['Native26_minus_FW', 'Native52_minus_FW']):
        assert np.allclose(d, [float(by_id[r['link_id']][col]) for r in rows], rtol=0, atol=0)
    top = max(float(v.max()) for v in flows)
    low = min(float(v.min()) for v in flows)
    absolute_norm = PowerNorm(gamma=.5, vmin=low, vmax=top)
    diff_micro = [d*1e6 for d in difference]
    limit = max(float(np.max(np.abs(d))) for d in diff_micro)
    difference_norm = TwoSlopeNorm(vmin=-limit, vcenter=0, vmax=limit)
    fig = pc.new_figure('berkeley', 'Native and FW physical-link flow',
                        'S72 / ACTUAL SAVED EXPLICIT NATIVE VECTORS', figsize=(14.2, 7.2))
    gs = fig.add_gridspec(2, 3, left=.06, right=.975, bottom=.125, top=.8,
                         hspace=.71, wspace=.32)
    for i, (flow, label) in enumerate(zip(flows, ['FW', 'Native rank 26', 'Native rank 52'])):
        ax = fig.add_subplot(gs[0, i]); title(ax, 'abc'[i], label)
        lc = physical_map(ax, segments, flow, absolute_norm)
        ax.set_xlabel('East (km)'); ax.set_ylabel('North (km)')
        cb = fig.colorbar(lc, ax=ax, orientation='horizontal', fraction=.055, pad=.27, aspect=28)
        cb.set_label('Physical-link flow (PCE/h)', fontsize=8)
        cb.set_ticks([0, 25, 100, 225, top]); cb.set_ticklabels(['0', '25', '100', '225', '390.3'])
    for i, (d, rank) in enumerate(zip(diff_micro, [26, 52])):
        ax = fig.add_subplot(gs[1, i]); title(ax, 'de'[i], f'Native {rank} − FW')
        lc = physical_map(ax, segments, d, difference_norm, cmap=pc.DIFF_CMAP, signed=True)
        ax.set_xlabel('East (km)'); ax.set_ylabel('North (km)')
        cb = fig.colorbar(lc, ax=ax, orientation='horizontal', fraction=.055, pad=.27, aspect=28)
        cb.set_label('Signed difference (10⁻⁶ PCE/h)', fontsize=8)
        cb.set_ticks([-limit, 0, limit]); cb.set_ticklabels(['−1.5854', '0', '1.5854'])
    ax = fig.add_subplot(gs[1, 2]); title(ax, 'f', 'Every link, at numerical scale')
    for d, color, label in zip(diff_micro, [pc.TEAL, pc.BLUE], ['Native 26 − FW', 'Native 52 − FW']):
        ax.scatter(flows[0], d, s=7, color=color, alpha=.5, edgecolor='none', label=label)
    ax.axhline(0, color='#9ba4a8', linewidth=.65)
    ax.set_xlabel('FW physical-link flow (PCE/h)')
    ax.set_ylabel('Signed difference (10⁻⁶ PCE/h)')
    ax.set_xlim(-10, 410); ax.set_ylim(-1.75, 1.75)
    ax.legend(fontsize=7.5, loc='upper left')
    maxdiff = [float(np.max(np.abs(d))) for d in difference]
    caption = ('Actual saved FW and Native rank-26/rank-52 explicit physical-link vectors, each joined one-to-one to all '
               '2,150 frozen S72 link geometries. Finite-path flow is not used as a Native substitute. The three absolute maps '
               'share a square-root colour scale and the same geographic bounds; the two signed Native−FW maps share a '
               'symmetric zero-centred scale. Differences are magnified into 10⁻⁶ PCE/h and retain their signs. '
               f'Maximum absolute differences are {maxdiff[0]:.10g} PCE/h for rank 26 and {maxdiff[1]:.10g} PCE/h for rank 52. '
               'Panel f includes every physical link, including overlapping points at zero. These are tiny numerical endpoint '
               'differences, not traffic improvement, diversion sensitivity or measured accuracy. Rank-52 raw flow includes '
               'numerical negatives down to −4.380487468063516×10⁻⁴⁷ PCE/h; they remain in the source and the common colour '
               'normalization lower bound, without clipping. Line widths use absolute magnitude with the same maximum '
               'within each comparison family. Local display kilometres '
               'preserve the original road vertices. © OpenStreetMap contributors, ODbL 1.0. '
               'One bounded uncalibrated one-hour engineering scenario; no new solver run.')
    panels = [
        {'id': 'abc'[i], 'metric': columns[i], 'rows': 2150, 'unit': 'PCE/h',
         'transform': 'shared PowerNorm(gamma=0.5); width=0.4+1.35*sqrt(abs(flow)/shared absolute maximum)',
         'shared_colour_min': low, 'shared_colour_max': top} for i in range(3)] + [
        {'id': 'de'[i], 'metric': f'Native{rank}_minus_FW', 'rows': 2150, 'unit': 'micro PCE/h',
         'transform': 'actual saved Native explicit v minus actual FW flow; multiply 1e6; shared symmetric linear colour and shared sqrt width maximum',
         'colour_bounds_micro': [-limit, limit], 'max_abs_difference_pce_per_hour': maxdiff[i]}
        for i, rank in enumerate([26, 52])] + [
        {'id': 'f', 'metric': 'Native minus FW against FW physical-link flow', 'rows_per_method': 2150,
         'x_unit': 'PCE/h', 'y_unit': 'micro PCE/h', 'transform': 'linear axes; all points including exact overlap'}]
    data = {'link_flow_rows': saved, 'checks': {'rows': 2150, 'unique_link_ids': len(by_id),
        'source_native_is_explicit_saved_v': True, 'max_abs_difference_pce_per_hour': dict(zip(['Native26', 'Native52'], maxdiff)),
        'min_native_flow_pce_per_hour': {'Native26': float(flows[1].min()), 'Native52': float(flows[2].min())},
        'negative_native_rows': {'Native26': int(np.count_nonzero(flows[1]<0)), 'Native52': int(np.count_nonzero(flows[2]<0))}},
        'colour': {'absolute_min': low, 'absolute_max': top, 'difference_min_micro': -limit, 'difference_max_micro': limit}}
    return save(fig, 's03_native_flows', 'Native and FW physical-link flow', caption, panels,
                ['s72_physical_flow.csv', 'physical_geometry.csv'], data, s03_native_flows)


if __name__ == '__main__':
    s01_geography_pool()
    s02_same_instance_methods()
    s03_native_flows()
