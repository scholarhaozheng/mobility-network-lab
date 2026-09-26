<!-- Homepage content derived from the root README by tools/build_case_presentation.py. -->
<p align="center"><img alt="City-neutral framework: GMNS objects and separate population-household/activity preparation feed four stages; observation linkage, static methods and finite space-time CG remain distinct." src="assets/presentation_r3/framework_overview.png" width="100%"/></p>
<h1 id="mobility-computation-lab">Mobility Computation Lab</h1>
<p><strong>An open-source computational framework for GMNS city models, four-stage demand, static assignment, and finite space–time optimization.</strong> City networks, travel demand and reproducible network computation.</p>
<p>The reusable objects come first; cities are instances. Networks, zones and explicit units enter shared interfaces. Users can start with supplied vehicle OD, or prepare vehicle demand from a supported person-demand and choice specification. Static assignment and finite space–time capacitated flow are <strong>different model branches</strong>, not interchangeable algorithms for one universal problem.</p>
<blockquote>
<p><strong>Executed CG evidence is part of the public release—not only a roadmap.</strong> Boston has one accepted bounded real-city pilot that clears Phase I, reaches reference-objective agreement with the arc-flow LP on the same finite time-expanded graph, and establishes independent pricing closure for 10/10 demands. Sioux Falls retains separate 200-OD and 250-OD historical selected-OD runs that clear Phase I and each reach their own reference objective; independent pricing closure is not established for those retained runs.</p>
</blockquote>
<p align="center"><a href="#framework">Framework</a> · <a href="#cg-experiments">Executed CG experiments</a> · <a href="#admm-r2">ADMM R2</a> · <a href="#distributed-assignment">Distributed assignment</a> · <a href="#algorithm-b">Algorithm B</a> · <a href="#coverage">Case coverage</a> · <a href="#boston">Case 01 · Boston</a> · <a href="#sioux-falls">Case 02 · Sioux Falls</a> · <a href="#hong-kong">Case 03 · Hong Kong</a> · <a href="#run-your-input">Run new inputs</a> · <a href="#mobility-data-support">Open data &amp; tools</a></p>
<p><a id="framework"></a></p>
<h2 id="01-the-shared-framework">01 / The shared framework</h2>
<h3 id="gmns-is-the-common-object-contract">GMNS is the common object contract</h3>
<p><code>zone / super_zone → centroid / access → physical node / directed link</code> keeps the different objects distinct. Source-ID mappings connect supplied demand, matched observations and saved outputs without merging their identities. The exchange profile records directions, units, capacities and supported extensions. A nonphysical connector is not a road; a shared link reference does not make two datasets the same trip or observation.</p>
<p>The <strong>framework diagram above is conceptual</strong>. It contains no city geography or empirical values. Actual source-backed objects and record-level demonstrations appear inside each labeled case below. <a href="data-contract.html">Data contract</a> · <a href="city-workflow.html">City and hierarchy workflow</a>.</p>
<h3 id="population-households-activity-preparation">Population, Households &amp; Activity Preparation</h3>
<p>Before any optional demand estimation, source statistics and activity evidence need <strong>version, field, unit and geography checks</strong>. Statistical polygons and model zones are different objects: a declared spatial allocation can create zonal population and household attributes with source IDs, coverage and uncertainty limits retained. Activity evidence can supply a separate attraction attribute. A generation model must then declare which attribute it uses; households are one possible input, not a universal rate base. This preparation is <strong>upstream of stage 01</strong>, not a fifth numbered stage or an automatic adapter for every city.</p>
<p>Boston below demonstrates an actual aggregate ACS-to-H3 allocation and transferred household-rate example. Sioux Falls begins with supplied benchmark vehicle OD and has <strong>no estimated demographic stage</strong>. A user with valid vehicle OD may bypass population preparation and stages 01–03. <a href="datasets/boston-population-households.html">Boston's exact source fields, allocation and saved-table check</a>.</p>
<p><a id="four-step-workflow"></a></p>
<h3 id="four-stages-with-explicit-inputs-and-outputs">Four stages, with explicit inputs and outputs</h3>
<div class="table-scroll"><table>
<thead>
<tr>
<th>Stage</th>
<th>Question</th>
<th>Computational object</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>01 · Trip generation</strong></td>
<td>How much travel is produced and attracted?</td>
<td>Activity/household evidence and a declared model → purpose-specific productions and attractions</td>
</tr>
<tr>
<td><strong>02 · Trip distribution</strong></td>
<td>Where does that travel go?</td>
<td>Margins, impedance and boundary treatment → directed person OD</td>
</tr>
<tr>
<td><strong>03 · Mode choice</strong></td>
<td>Which available alternatives are used?</td>
<td>Absolute costs or a declared pivot model → probabilities and mode demand; occupancy → vehicles</td>
</tr>
<tr>
<td><strong>04 · Traffic assignment</strong></td>
<td>Which paths and roads carry the demand?</td>
<td>A declared network, vehicle demand, period and objective → path/link flows and independent checks</td>
</tr>
</tbody>
</table></div>
<p>A four-stage label is not a guarantee of a calibrated regional model. Input support, modeling assumptions and empirical status are recorded per case. <strong>Users who already have vehicle OD can enter directly at stage 04.</strong> No GPS, census or transit feed is required by the generic direct-vehicle entry.</p>
<h3 id="gps-and-service-evidence-enter-through-explicit-relationships">GPS and service evidence enter through explicit relationships</h3>
<pre><code class="language-text">positions + timestamps → quality checks → road/service matching
                                            ↓
                          a supported interval/cost/parameter input
                                            ↓
                           mode demand and/or network calculation
</code></pre>
<p>Map matching is a computation, not a property supplied automatically by the GMNS file format. A position sample is not a traffic count, and matched vehicle paths do not automatically reveal all passenger OD. Each application must define what an observation supports. Boston below separates spatial linkage from an exploratory transit-time feedback experiment.</p>
<h3 id="methods-choose-the-mathematical-problem-before-the-solver">Methods: choose the mathematical problem before the solver</h3>
<div class="table-scroll"><table>
<thead>
<tr>
<th>Model family</th>
<th>Existing implementations</th>
<th>What the method returns</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Static, fixed-demand user-equilibrium approximation</strong></td>
<td>Frank–Wolfe; solved finite-path reference; native Diagnostic L3; official <code>tap-b</code> Algorithm B with an explicitly named adapter route</td>
<td>BPR/Beckmann path and link flow under the declared period and units</td>
</tr>
<tr>
<td><strong>Finite space–time, fixed-cost capacitated flow</strong></td>
<td>Arc-flow reference LP; Phase-I/II column generation; bounded Sioux Lagrangian R2; Sioux/Boston ADMM R2_S</td>
<td>Time-indexed flows and shared-capacity checks; algorithm-specific certificates and physical-link back-projection</td>
</tr>
</tbody>
</table></div>
<p>Compression changes a representation and requires a checked reconstruction. It is <strong>not</strong> the same operation as time expansion. Diagnostic <strong>L3</strong> is an algorithm profile name, not GMNS Level 3 or stage 03 of the demand model. <a href="methods/origin-based-algorithm-b.html">Official <code>tap-b</code> Algorithm B results</a> are a separate static assignment branch. <a href="methods/admm-space-time.html">ADMM R2</a> has selected Sioux and bounded Boston evidence under the finite time-expanded LP contract. <a href="methods.html">Actual method sources and supported scopes</a>.</p>
<h3 id="why-a-spacetime-network-is-built-before-cg">Why a space–time network is built before CG</h3>
<p>A physical node is replicated as <code>(node, time)</code>. A movement connects departure to a later arrival state; waiting stays at the same physical node while advancing time; demand-specific source/sink connections attach departure and arrival support. A path through that network becomes a generated column in the restricted master. <strong>Phase I restores feasibility by clearing artificial flow. Phase II improves the real-path objective.</strong> The arc-flow LP on the same finite time-expanded graph is a reference, not another city or the static FW objective.</p>
<p><a href="methods/space-time-cg.html">Construction and master/pricing guide</a>. Both cases now use the same CG evidence vocabulary and reading order: <a href="cases/boston-space-time.html">Boston's single bounded 10-OD pilot</a> and the distinct <a href="cases/sioux-space-time.html">Sioux Falls 200/250-OD selected-OD benchmarks</a>. Boston has independent pricing closure; that certificate is <strong>not</strong> imputed to Sioux Falls.</p>
<p><a id="cg-evidence"></a></p>
<h3 id="case-parallel-finite-spacetime-cg-evidence">Case-parallel finite space–time CG evidence</h3>
<p>The two cases keep their own scale and unique supplementary evidence, but every shared CG stage uses the same term and section order.</p>
<div class="table-scroll"><table>
<thead>
<tr>
<th>Shared evidence stage</th>
<th>Boston</th>
<th>Sioux Falls</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>From the physical network to time-indexed columns</strong></td>
<td>Actual B07 physical-to-time cutaway on one bounded real-city pilot</td>
<td>Actual XS170 local cutaway on the historical selected-OD benchmarks</td>
</tr>
<tr>
<td><strong>Phase I restores feasibility</strong></td>
<td>Total and B01–B10 artificial-flow clearance; zero at round 90</td>
<td>200/250-OD artificial-flow clearance; zero at rounds 51/62</td>
</tr>
<tr>
<td><strong>A new path can help a different OD</strong></td>
<td>Saved B07/B09/B10 shared-capacity reallocation</td>
<td>Saved XS170/XS169 shared-capacity reallocation</td>
</tr>
<tr>
<td><strong>Phase II improves the real-path objective</strong></td>
<td>Objective reaches the arc-flow LP on the same finite time-expanded graph</td>
<td>Each benchmark reaches the arc-flow LP on its own selected-OD finite time-expanded graph</td>
</tr>
<tr>
<td><strong>Final physical-link movement flow and validation</strong></td>
<td>125-link pilot view plus conservation/capacity/objective audit</td>
<td>200/250-OD physical-link views plus conservation/capacity/objective audit</td>
</tr>
<tr>
<td><strong>Independent pricing closure</strong></td>
<td>Established for 10/10 demands at <code>1e-6</code></td>
<td>Not established for the retained historical runs</td>
</tr>
</tbody>
</table></div>
<p><a href="cases/boston-space-time.html">Open the Boston CG evidence</a> · <a href="cases/sioux-space-time.html">Open the Sioux Falls CG evidence</a> · <a href="visualizations.html">Compare the figure families</a>.</p>
<p><a id="admm-r2"></a></p>
<h3 id="finite-spacetime-admm-r2-saved-result-verification">Finite space–time ADMM R2 · saved-result verification</h3>
<p align="center"><a href="methods/admm-space-time.html"><img alt="Accepted ADMM R2 results for selected Sioux Falls 200/250 OD and bounded Boston 10 OD, each independently checked against its own finite-graph LP." src="assets/admm_r2/figures/admm_results_overview.png" width="100%"/></a></p>
<div class="table-scroll"><table>
<thead>
<tr>
<th>Bounded case</th>
<th style="text-align:right">Accepted iterations</th>
<th style="text-align:right">Relative objective gap to same-graph arc-flow LP</th>
<th>Independent gates</th>
</tr>
</thead>
<tbody>
<tr>
<td>Sioux Falls 200 OD</td>
<td style="text-align:right">85</td>
<td style="text-align:right">6.30e-6</td>
<td>Pass</td>
</tr>
<tr>
<td>Sioux Falls 250 OD</td>
<td style="text-align:right">101</td>
<td style="text-align:right">7.16e-6</td>
<td>Pass</td>
</tr>
<tr>
<td>Boston 10 OD</td>
<td style="text-align:right">253</td>
<td style="text-align:right">6.68e-6</td>
<td>Pass</td>
</tr>
</tbody>
</table></div>
<p>The R2_S scaling and input-derived fixed-rho rule were selected on authored fixtures and Sioux, then frozen before Boston. The independent evaluator made <strong>zero optimizer calls</strong>; the original ADMM solver did use local QP optimization. These are finite time-expanded shared-capacity LP instances, not static Beckmann UE. Sioux cases are selected subsets, and Boston is a 90-node/125-link holdout, not citywide. Objective closeness does not establish identical link, path or time flows. <a href="#admm-r2-figures">Complete convergence, conservation and physical-flow figures below</a> · <a href="methods/admm-space-time.html">Method and gates</a> · <a href="cases/sioux-admm.html">Sioux case</a> · <a href="cases/boston-admm.html">Boston case and 125-row derived table</a> · <a href="assets/admm_r2/figures/admm_results_overview.svg">Editable overview</a>.</p>
<p><a id="cg-experiments"></a></p>
<h2 id="executed-finite-spacetime-cg-experiments">Executed finite space–time CG experiments</h2>
<p>The repository contains <strong>two distinct executed CG evidence families</strong>. Boston is one bounded real-city pilot on an accepted GMNS subnetwork. Sioux Falls contains two historical selected-OD benchmark instances. They share the same method family, but not the same graph, demand, objective value, scale, or certificate status.</p>
<p align="center"><a href="methods/space-time-cg.html"><img alt="Six-stage comparison of executed finite space–time CG evidence: one bounded Boston pilot and two historical Sioux Falls selected-OD runs. Both have saved Phase-I, Phase-II, final-flow and reference evidence; independent pricing closure is established only for Boston." src="assets/presentation_r5/boston_sioux_cg_parallel_overview.png" width="100%"/></a></p>
<div class="table-scroll"><table>
<thead>
<tr>
<th>Executed evidence</th>
<th>Boston</th>
<th>Sioux Falls</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Instance</strong></td>
<td>One bounded real-city pilot: 90 physical nodes, 125 directed links, 10 ODs, 3-second steps, 100-step horizon</td>
<td>Two historical selected-OD subsets: 200 ODs and 250 ODs</td>
</tr>
<tr>
<td><strong>Phase I</strong></td>
<td>Artificial flow <strong>20.5536128974 → 0</strong> in round <strong>90</strong></td>
<td>Artificial flow reaches zero in rounds <strong>51 / 62</strong></td>
</tr>
<tr>
<td><strong>Phase II</strong></td>
<td>Objective <strong>64.39686151152954</strong>, with reference-objective agreement on the same finite time-expanded graph</td>
<td>Objectives <strong>943,155.589771 / 1,521,090.836620</strong>, each with reference-objective agreement on its own selected-OD finite time-expanded graph</td>
</tr>
<tr>
<td><strong>Pricing certificate</strong></td>
<td>Independent full-DAG closure passes <strong>10/10 demands</strong> at <code>1e-6</code></td>
<td>Independent full-DAG closure <strong>not established</strong> for the saved historical runs</td>
</tr>
<tr>
<td><strong>Open the evidence</strong></td>
<td><a href="cases/boston-space-time.html">Boston CG case and full figure family</a></td>
<td><a href="cases/sioux-space-time.html">Sioux Falls CG case</a> · <a href="datasets/sioux-200od.html">200 OD</a> · <a href="datasets/sioux-250od.html">250 OD</a></td>
</tr>
</tbody>
</table></div>
<p><em>These are saved-result visualizations. Boston is not citywide CG; Sioux Falls is not a modern real-city demand model. The fixed-cost hard-capacity CG objectives are not directly comparable with static BPR/Beckmann FW.</em> <a href="assets/presentation_r5/boston_sioux_cg_parallel_overview.svg">Current overview SVG</a> · <a href="assets/presentation_r5/CG_CASE_SEQUENCE_SOURCES.json">Current source hashes</a> · <a href="assets/presentation_r4/cg_experiments_overview.png">Earlier saved overview</a> and <a href="assets/presentation_r4/CG_EXPERIMENTS_OVERVIEW_SOURCES.json">its source manifest</a>.</p>
<p><a id="admm-r2-figures"></a></p>
<h2 id="executed-finite-spacetime-admm-r2-figure-families">Executed finite space–time ADMM R2 figure families</h2>
<p>The figures below show the accepted convergence and original-unit feasibility traces, commodity conservation where an individual heatmap was released, and final physical-link movement flow against the same-graph LP with its signed difference. They use the frozen R2_S policy; no solver or figure was rerun for this README. <a href="methods/admm-space-time.html">Method and independent gates</a>.</p>
<h4 id="sioux-falls-200-selected-ods">Sioux Falls · 200 selected ODs</h4>
<p><img alt="Sioux 200-OD ADMM R2 residual convergence, original-unit local balance and capacity, objective and fixed rho" src="assets/admm_r2/figures/convergence_Sioux_200OD.png"/></p>
<p><em>Convergence and feasibility on the 200-OD selected finite graph.</em> <a href="assets/admm_r2/figures/convergence_Sioux_200OD.svg">SVG</a> · <a href="assets/admm_r2/figures/convergence_Sioux_200OD.source.json">Source record</a>.</p>
<p><img alt="Sioux 200-OD commodity-level original-unit conservation heatmap" src="assets/admm_r2/figures/admm_sioux_200_local_conservation_heatmap.png"/></p>
<p><em>Commodity-level local balance across the saved iterations; the frozen <code>1e-5</code> gate is marked.</em> <a href="assets/admm_r2/figures/admm_sioux_200_local_conservation_heatmap.svg">SVG</a> · <a href="assets/admm_r2/figures/admm_sioux_200_local_conservation_heatmap.source.json">Source and limits</a>.</p>
<p><img alt="Sioux 200-OD final physical-link movement flows for ADMM and the same-graph LP on one shared scale" src="assets/admm_r2/figures/admm_sioux_200_final_physical_link_flow.png"/></p>
<p><img alt="Sioux 200-OD signed physical-link ADMM-minus-LP movement-flow difference" src="assets/admm_r2/figures/admm_sioux_200_minus_lp.png"/></p>
<p><em>Final movement flow and signed difference. Sioux topology uses a deterministic schematic layout, not geographic coordinates.</em> <a href="assets/admm_r2/figures/admm_sioux_200_final_physical_link_flow.svg">Flow SVG</a> · <a href="assets/admm_r2/figures/admm_sioux_200_minus_lp.svg">Difference SVG</a> · <a href="cases/sioux-admm.html">Full case</a>.</p>
<h4 id="sioux-falls-250-selected-ods">Sioux Falls · 250 selected ODs</h4>
<p><img alt="Sioux 250-OD ADMM R2 residual convergence, original-unit local balance and capacity, objective and fixed rho" src="assets/admm_r2/figures/convergence_Sioux_250OD.png"/></p>
<p><em>The right-hand panel contains the accepted original-unit local balance and capacity traces. A separate 250-OD commodity heatmap was not released; none is implied here.</em> <a href="assets/admm_r2/figures/convergence_Sioux_250OD.svg">SVG</a> · <a href="assets/admm_r2/figures/convergence_Sioux_250OD.source.json">Source record</a>.</p>
<p><img alt="Sioux 250-OD final physical-link movement flows for ADMM and the same-graph LP on one shared scale" src="assets/admm_r2/figures/admm_sioux_250_final_physical_link_flow.png"/></p>
<p><img alt="Sioux 250-OD signed physical-link ADMM-minus-LP movement-flow difference" src="assets/admm_r2/figures/admm_sioux_250_minus_lp.png"/></p>
<p><em>Final movement flow and signed difference on the 250-OD selected graph; the schematic layout is not a geographic map.</em> <a href="assets/admm_r2/figures/admm_sioux_250_final_physical_link_flow.svg">Flow SVG</a> · <a href="assets/admm_r2/figures/admm_sioux_250_minus_lp.svg">Difference SVG</a> · <a href="cases/sioux-admm.html">Full case</a>.</p>
<h4 id="boston-bounded-10-od-holdout">Boston · bounded 10-OD holdout</h4>
<p><img alt="Boston 10-OD ADMM R2 residual convergence, original-unit local balance and capacity, objective and fixed rho" src="assets/admm_r2/figures/convergence_Boston_10OD.png"/></p>
<p><em>Convergence and feasibility under the Sioux-selected policy frozen before Boston.</em> <a href="assets/admm_r2/figures/convergence_Boston_10OD.svg">SVG</a> · <a href="assets/admm_r2/figures/convergence_Boston_10OD.source.json">Source record</a>.</p>
<p><img alt="Boston 10-OD commodity-level original-unit conservation heatmap" src="assets/admm_r2/figures/admm_boston_10od_local_conservation_heatmap.png"/></p>
<p><em>All ten saved commodity balance traces, with the frozen <code>1e-5</code> gate marked.</em> <a href="assets/admm_r2/figures/admm_boston_10od_local_conservation_heatmap.svg">SVG</a> · <a href="assets/admm_r2/figures/admm_boston_10od_local_conservation_heatmap.source.json">Source and limits</a>.</p>
<p><img alt="Boston 10-OD final physical-link movement flows for ADMM and the same-graph LP on one shared scale" src="assets/admm_r2/figures/admm_boston_10od_final_physical_link_flow.png"/></p>
<p><img alt="Boston 10-OD signed physical-link ADMM-minus-LP movement-flow difference" src="assets/admm_r2/figures/admm_boston_10od_minus_lp.png"/></p>
<p><em>The absolute panels share a scale; the signed map retains the actual ±<code>4.24e-4</code>-vehicle maximum rather than enlarging it. Maps use already-public GMNS Plus geometry and IDs under Apache-2.0 attribution.</em> <a href="assets/admm_r2/figures/admm_boston_10od_final_physical_link_flow.svg">Flow SVG</a> · <a href="assets/admm_r2/figures/admm_boston_10od_minus_lp.svg">Difference SVG</a> · <a href="assets/admm_r2/data/boston_10od_physical_link_admm_lp_comparison.csv">125-row derived table</a> · <a href="cases/boston-admm.html">Full case and rights limits</a>.</p>
<p><a id="distributed-assignment"></a></p>
<h2 id="static-and-distributed-assignment-results">Static and distributed assignment results</h2>
<h3 id="distributed-assignment-algorithms-bounded-accepted-results">Distributed assignment algorithms / bounded accepted results</h3>
<p>The Sioux 200/250-OD <strong>finite time-expanded shared-capacity</strong> instances also have accepted, method-specific saved results. These are not static user equilibrium or full 528-OD network solutions. Their mathematical contract is separate from static FW; no cross-contract objective comparison is implied.</p>
<div class="table-scroll"><table>
<thead>
<tr>
<th>Method</th>
<th>Accepted Sioux 200 OD</th>
<th>Accepted Sioux 250 OD</th>
<th>Necessary distinction</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Lagrangian R2</strong></td>
<td>Dual lower bound <strong>942,452.403471</strong>; separately recovered feasible primal <strong>943,155.589771</strong> vehicle-min; <strong>0.0746%</strong> certified gap</td>
<td>Dual <strong>1,516,258.347432</strong>; feasible primal <strong>1,521,090.836620</strong> vehicle-min; <strong>0.3177%</strong> gap, below frozen 1% gate</td>
<td>Capacity-price dual generates paths; a separate restricted-path LP recovers the primal. Both primals match their own same-graph arc-flow LP objectives.</td>
</tr>
<tr>
<td><strong>ADMM R2_S</strong></td>
<td>Objective <strong>943,161.533307</strong> vehicle-min; <strong>6.30e-6</strong> relative gap to own LP</td>
<td>Objective <strong>1,521,101.731718</strong> vehicle-min; <strong>7.16e-6</strong> relative gap to own LP</td>
<td>Frozen Sioux-selected policy also passes a separate bounded Boston 10-OD holdout; independent conservation/capacity/KKT/projection checks pass. <a href="methods/admm-space-time.html">Full cross-city ADMM evidence</a>.</td>
</tr>
</tbody>
</table></div>
<div class="table-scroll"><table><tr><td width="50%"><a href="methods/distributed-assignment.html#lagrangian-capacity-pricing-with-separate-primal-recovery"><img alt="Sioux 200-OD Lagrangian saved lower-bound and feasible-recovery evidence" src="assets/sioux/distributed_r1/Sioux_200OD_P07.svg" width="100%"/></a></td><td width="50%"><a href="methods/distributed-assignment.html#lagrangian-capacity-pricing-with-separate-primal-recovery"><img alt="Sioux 250-OD Lagrangian saved lower-bound and feasible-recovery evidence" src="assets/sioux/distributed_r1/Sioux_250OD_P07.svg" width="100%"/></a></td></tr></table></div>
<p><em>Saved Lagrangian R2 histories, in matching 200/250-OD layouts. The lower and upper bounds are different mathematical outputs; a dual lower bound alone is not a feasible assignment.</em></p>
<div class="table-scroll"><table><tr><td width="50%"><a href="methods/distributed-assignment.html#admm-localconsensus-shared-capacity-decomposition"><img alt="200-OD ADMM result is 0.000434 percent above its own LP objective" src="assets/sioux/distributed_r1/sioux_200od_objective_difference.svg" width="100%"/></a></td><td width="50%"><a href="methods/distributed-assignment.html#admm-localconsensus-shared-capacity-decomposition"><img alt="250-OD ADMM result is 0.000607 percent above its own LP objective" src="assets/sioux/distributed_r1/sioux_250od_objective_difference.svg" width="100%"/></a></td></tr></table></div>
<p><em>Earlier R1 paired scalar figures are retained as historical evidence; they are not the new R2_S histories. The R1 250-OD iteration history was not supplied, so none was created.</em> <a href="methods/distributed-assignment.html">R1 source and limits</a> · <a href="cases/sioux-admm.html">R2 matched figures</a>.</p>
<p>The Lagrangian row describes accepted Sioux selected-OD results only; its Boston transfer remains gated by the frozen 1% duality-gap criterion. ADMM R2_S additionally passes the separate bounded Boston 10-OD holdout. Neither changes previously accepted Boston FW or CG results.</p>
<p><a id="algorithm-b"></a></p>
<h3 id="static-user-equilibrium-official-tap-b-algorithm-b">Static user equilibrium / official <code>tap-b</code> Algorithm B</h3>
<p>The official <code>spartalab/tap-b</code> Algorithm B executable was evaluated on frozen static BPR/Beckmann instances. <strong>Sioux Falls</strong> also passed parity through the pinned official TAPLab registered <code>tapb</code> CLI adapter and direct callable; <strong>Boston B0/B1</strong> passed through a <em>task-local TAPLab-compatible lossless adapter</em>. The stock official TAPLab converter was stopped <strong>before</strong> a Boston solve because it changed first-thru-node semantics and rounded OD demand. This is not an official TAPLab Boston parity result.</p>
<p align="center"><a href="methods/origin-based-algorithm-b.html"><img alt="Saved static Algorithm B evidence in two columns, Sioux Falls and Boston B1, and four rows: convergence, physical-link comparison with same-problem FW, selected-origin reconstructed flow, and independent verification." src="assets/algorithm_b_r21/algorithm_b_cross_city_overview.png" width="100%"/></a></p>
<p><em>Figure — Saved static assignment evidence.</em> The eight accepted R2 SVGs are combined without recomputing flows. Boston B1's convergence panel contains <strong>one</strong> accepted iteration; its near-equality with same-problem FW on a low-congestion holdout is not a speed or superiority claim. <a href="assets/algorithm_b_r21/algorithm_b_cross_city_overview.svg">Editable overview</a> · <a href="https://github.com/scholarhaozheng/mobility-network-lab/blob/main/algorithms/origin_based_algorithm_b/README.md">Individual figures and hashes</a>.</p>
<div class="table-scroll"><table>
<thead>
<tr>
<th>Frozen case</th>
<th>Numerical result</th>
<th>Independent check</th>
<th>Adapter status</th>
</tr>
</thead>
<tbody>
<tr>
<td><a href="cases/sioux-algorithm-b.html">Classic Sioux Falls</a></td>
<td>24 nodes, 76 links, 528 positive ODs; Beckmann <strong>4,231,335.287110682 vehicle-min</strong></td>
<td>Relative gap <strong>4.4984e-9</strong>; used-arc slack <strong>8.20e-5 min</strong></td>
<td>Official TAPLab CLI and direct callable match accepted physical-link flows exactly; <code>taplab verify</code> certified</td>
</tr>
<tr>
<td><a href="cases/boston-algorithm-b.html">Central Boston B0</a></td>
<td>26 physical-node ODs, 203.660478635 modeled vehicles; accepted interface control</td>
<td>Objective <strong>707.057923071 vehicle-min</strong>; task-local checks passed</td>
<td>Task-local lossless adapter; official converter contract blocked before solve</td>
</tr>
<tr>
<td><a href="cases/boston-algorithm-b.html">Central Boston B1</a></td>
<td>453 physical-node ODs, <strong>1,936.23847491 PCE</strong> in a two-hour conditional HBW-midday cohort; Beckmann <strong>7,922.083942188 PCE-min</strong></td>
<td>Independent relative gap approximately zero; physical-link flow agrees with same-problem FW</td>
<td>Task-local lossless adapter; official converter contract blocked before solve</td>
</tr>
</tbody>
</table></div>
<p>The B0 interface result has no public aggregate flow/figure in this release. Boston B1 is neither observed traffic nor citywide/empirical validation. The official solver's internal Policy Bush merge, backward-label and restriction-update state was <strong>not exported</strong>; selected-origin displays reconstruct flow from exported OD paths. <a href="methods/origin-based-algorithm-b.html">Method and limits</a> · <a href="integrations/taplab-tapb.html">TAPLab adapter audit</a>.</p>
<p><a id="coverage"></a></p>
<h2 id="02-what-each-case-demonstrates">02 / What each case demonstrates</h2>
<p>The entries distinguish <strong>available code</strong>, <strong>executed case evidence</strong>, and <strong>the scale at which a method was actually accepted</strong>. A missing result is not a claim that the method can never run on that city. A tiny generic fixture does not certify a large Boston solve.</p>
<div class="table-scroll"><table>
<thead>
<tr>
<th>Capability / evidence</th>
<th>Boston</th>
<th>Sioux Falls</th>
<th>Hong Kong pilot</th>
</tr>
</thead>
<tbody>
<tr>
<td>GMNS network, zones and access</td>
<td><strong>Demonstrated:</strong> H3 hierarchy, centroid/access and source-ID round-trip</td>
<td><strong>Benchmark network:</strong> supplied topology and demand; not a present-day H3 city dataset</td>
<td><strong>Demonstrated, bounded:</strong> 780 physical nodes, 1,239 links, 95 SSG/10 STPUG zones and 190 nonphysical connectors</td>
</tr>
<tr>
<td>Population, households and activity preparation</td>
<td><strong>Demonstrated, limited:</strong> source-backed ACS block-group → H3 aggregate allocation; separate MassGIS attraction proxy</td>
<td><strong>Not estimated:</strong> classic benchmark supplies vehicle OD without a demographic build</td>
<td><strong>Demonstrated, limited:</strong> 2021 census SSG area allocation; population and households kept separate</td>
</tr>
<tr>
<td>Trip generation / distribution</td>
<td><strong>Demonstrated, limited:</strong> transferred household rates, activity prior, gravity/IPF and PA-to-OD</td>
<td><strong>Not estimated:</strong> given benchmark OD</td>
<td><strong>Hypothetical deterministic internal-only seed</strong>, not observed or calibrated OD</td>
</tr>
<tr>
<td>Mode choice</td>
<td><strong>Demonstrated, conditional:</strong> regional-share feedback and absolute DA/S2/S3/TW research branch</td>
<td><strong>Not modeled:</strong> fixed vehicle demand</td>
<td><strong>Not calibrated or modeled</strong>; illustrative vehicle conversion only</td>
</tr>
<tr>
<td>GPS / service evidence</td>
<td><strong>Demonstrated, exploratory:</strong> network linkage and default-off interval feedback; no independent AM validation</td>
<td><strong>Not included</strong> in the classic benchmark</td>
<td><strong>Linked layers:</strong> 183 GTFS stops, 294 routes and 50 detector lane observations; UrbanNav points private</td>
</tr>
<tr>
<td>Static Frank–Wolfe</td>
<td><strong>Demonstrated:</strong> small controls and three expanded tiers, up to 17,522 loaded node ODs</td>
<td><strong>Demonstrated:</strong> historical static benchmark; input-identity caveat retained</td>
<td><strong>Not run; assignment_ready=false</strong></td>
</tr>
<tr>
<td>Finite full-path reference</td>
<td><strong>Solved:</strong> 26-OD / 130-path control; <strong>resource-gated</strong> at expanded tiers</td>
<td>No equivalent solved full-path reference claimed by these supplied records</td>
<td><strong>Not run</strong></td>
</tr>
<tr>
<td>Native Diagnostic L3 / compression</td>
<td><strong>Accepted numerical controls:</strong> ranks 26/52; not solved at expanded tiers</td>
<td><strong>Executed numerical candidates:</strong> rank 50; full-network gaps 8.17% / 4.38%, not exact UE</td>
<td><strong>Not run</strong></td>
</tr>
<tr>
<td>Space–time CG</td>
<td><strong>Accepted bounded pilot:</strong> 90 nodes / 125 links / 10 ODs; same-graph LP match and independent 10/10 pricing closure</td>
<td><strong>Historical 200 / 250 OD:</strong> feasible and own-LP matched; independent pricing closure not established</td>
<td><strong>Not run</strong></td>
</tr>
<tr>
<td>Lagrangian capacity pricing</td>
<td><strong>Gated transfer:</strong> feasible recovery but 1.1002% gap missed frozen 1% gate</td>
<td><strong>Accepted R2:</strong> 200/250 OD separately feasible; duality gaps 0.0746% / 0.3177%</td>
<td><strong>Not run</strong></td>
</tr>
<tr>
<td>ADMM shared-capacity decomposition</td>
<td><strong>Accepted R2_S bounded holdout:</strong> 10 ODs, 253 iterations, 6.68e-6 own-LP relative gap</td>
<td><strong>Accepted R2_S selected subsets:</strong> 200/250 OD, 85/101 iterations, 6.30e-6 / 7.16e-6 own-LP gaps</td>
<td><strong>Not run</strong></td>
</tr>
<tr>
<td>Official <code>tap-b</code> Algorithm B static UE</td>
<td><strong>Accepted B0/B1 through task-local lossless adapter; official converter blocked before solve</strong></td>
<td><strong>Accepted classic benchmark; official TAPLab adapter parity and verification pass</strong></td>
<td><strong>Not run</strong></td>
</tr>
<tr>
<td>Saved checks and visualization</td>
<td>GMNS tracing, static original-space checks, full bounded CG figure family</td>
<td>Static/CG records plus accepted bounded Lagrangian/ADMM views</td>
<td>Five public SVGs, relationship validator and trace tool; no assignment figure</td>
</tr>
</tbody>
</table></div>
<p><a href="capabilities.html">Capability definitions and evidence pointers</a>. Boston and Sioux both include assignment research; Hong Kong adds a bounded, explicitly pre-assignment data portability pilot.</p>
<p><a id="boston"></a></p>
<h2 id="03-case-study-boston">03 / Case study — Boston</h2>
<p><strong>What this case demonstrates.</strong> Real-city GMNS object relationships; household/activity-based generation; modeled OD distribution; limited mode-choice branches; exploratory GPS/service linkage; new-input static computation; and FW at increasing demand coverage. It also retains a small <strong>FW / full-path / native L3</strong> control, an accepted <strong>task-local-adapter Algorithm B B0/B1</strong> static branch, and separate bounded finite space–time <strong>CG and ADMM R2_S</strong> pilots. <strong>Not demonstrated here:</strong> citywide CG/ADMM, full-city empirically calibrated demand, or independent AM accuracy.</p>
<div class="table-scroll"><table>
<thead>
<tr>
<th>Boston branch</th>
<th>Scope and purpose</th>
<th>Keep it distinct from</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Semantic service-feedback baseline</strong></td>
<td>36 selected zone ODs × three departures; regional baseline shares; about 202.078 / 202.071 assigned vehicle trips</td>
<td>An absolute-cost baseline-choice model or the expanded all-OD run</td>
</tr>
<tr>
<td><strong>Conditional ABS_PLANNED control</strong></td>
<td>26 road-node ODs, 203.660479 vehicles, frozen 130-path comparison; FW and accepted native ranks 26/52</td>
<td>Expanded L3 performance</td>
</tr>
<tr>
<td><strong>Algorithm B B0/B1 static controls</strong></td>
<td>B0 26-OD interface; B1 453 physical-node ODs, 1,936.23847491 PCE in two hours; official tap-b through task-local lossless adapter</td>
<td>Official TAPLab Boston adapter parity or observed/citywide demand</td>
</tr>
<tr>
<td><strong>Scalable conditional planned service</strong></td>
<td>500 / 2,000 / all 30,790 interzonal source ODs; new absolute attributes and eligible demand</td>
<td>All real Boston traffic or independent behavioral validation</td>
</tr>
<tr>
<td><strong>Bounded finite space–time CG pilot</strong></td>
<td>90 nodes / 125 links / 10 ODs; Phase I + Phase II + independent full-DAG pricing closure</td>
<td>Citywide Boston CG, static BPR/Beckmann assignment, or a second Boston scale</td>
</tr>
</tbody>
</table></div>
<p><a href="cases/boston.html">Complete Boston case</a> · <a href="cases/boston-assignment.html">Static assignment branches</a> · <a href="cases/boston-algorithm-b.html">Algorithm B B0/B1</a> · <a href="cases/boston-space-time.html">Bounded space–time CG result</a>.
<a href="cases/boston-admm.html">Bounded space–time ADMM R2 holdout</a>.</p>
<p align="center"><img alt="Dark navy Mobility Computation Lab cover with real Central Boston street and zone geometry on the right." src="assets/boston/visual_release_r1/mcl_boston_hero.png" width="100%"/></p>
<p align="center"><small>Central Boston road geometry: GMNS Plus 21_Boston (Apache-2.0), commit 116447ab641cca1ed34797d019c8e704063393c3; H3 zones and cover composition: Mobility Computation Lab. Geography only—not measured or modeled traffic.</small></p>
<p><a id="gmns-in-action"></a></p>
<h3 id="boston-gmns-in-action">Boston / GMNS in Action</h3>
<p><strong>One network reference for zones, demand, observations, and results.</strong> The actual Boston exchange keeps H3 zone 35, its centroid, nonphysical access connector and physical road node distinct. A documented crosswalk maps zone identities to road access; zonal S1 demand remains modeled panel vehicle trips. A separate saved GPS path occurrence can reference a physical link and its saved S1 road result without claiming it is the same OD or observed journey.</p>
<p align="center"><a href="datasets/boston-gmns-exchange.html#one-network-multiple-connected-data-layers"><img alt="Actual Boston H3 zones 35 and 71, centroid 35, dashed nonphysical access to road node 14285, an OD relation, and a separate GPS-to-link result branch." src="assets/boston/gmns_in_action_r1/gmns_connected_layers.png" width="100%"/></a></p>
<p><em>Separate objects, explicit relationships. Model access connectors are not physical roads. Shared link references do not imply a shared observed trip.</em> <a href="datasets/boston-gmns-exchange.html">Figure records, field mappings and provenance</a> · <a href="https://github.com/scholarhaozheng/mobility-network-lab/blob/main/examples/boston/gmns_exchange_r1/README.md">Versioned exchange and GMNS Plus profile</a> · <a href="../tools/gmns/trace_gmns_figure.py">Read-only relationship lookup</a>.</p>
<p>From the repository root, inspect the generic relationships with <code>python -B tools/gmns/boston_exchange.py trace --exchange examples/boston/gmns_exchange_r1/data</code>; the <a href="datasets/boston-gmns-exchange.html#reproduce-the-relationships">exact figure segment query</a> is separate. GMNS is the data/exchange contract, not the matching algorithm or evidence of improved prediction. The pinned GMNS Plus Level 2 reader accepted S1/S2 node/link/demand; a separate zone-schema check and the declared <code>mcl_solver_*</code> fields support the existing solver round-trip.</p>
<h3 id="city-network-workflow">City network workflow</h3>
<p>The common foundation is a real city network: <strong>2,852 physical nodes, 5,091 directed links, 177 H3 r9 zones and nine r7 parents</strong>. Zone-access mappings attach demand to roads; ordered link membership defines a corridor; transit and GPS records retain their own identities and connect to the same network. Model access lines are not automatically verified physical routes.</p>
<p><a href="data-contract.html">GMNS-compatible input contract</a> · <a href="city-workflow.html">City and hierarchy guide</a> · <a href="datasets/boston-central.html">Boston network and data layers</a></p>
<h4 id="gmns-foundation-and-toolchain-alignment">GMNS Foundation and Toolchain Alignment</h4>
<p>The <a href="https://github.com/scholarhaozheng/mobility-network-lab/blob/main/examples/boston/gmns_exchange_r1/README.md">versioned Boston exchange</a> now exposes the actual <a href="../examples/boston/gmns_exchange_r1/data/node.csv">GMNS nodes</a>, <a href="../examples/boston/gmns_exchange_r1/data/link.csv">directed links</a>, <a href="../examples/boston/gmns_exchange_r1/data/zone.csv">H3 zones and hierarchy</a>, and separate <a href="../examples/boston/gmns_exchange_r1/data/demand_S1.csv">S1</a>/<a href="../examples/boston/gmns_exchange_r1/data/demand_S2.csv">S2</a> zonal demand. A <a href="../examples/boston/gmns_exchange_r1/data/id_crosswalk.csv">reversible ID/access crosswalk</a> connects 177 distinct zones to 139 physical access nodes. The pinned GMNS Plus structural reader opened both exports; the adapter reconstructed the accepted physical solver inputs without rerunning the model. <a href="datasets/boston-gmns-exchange.html">Open/query/rebuild commands and precise scope</a> distinguish core GMNS fields, GMNS Plus conventions, and MCL GPS/service/result extensions. Source-hourly and solver-period capacities remain separate; nonphysical connectors have no invented routing costs. Grid2demand2/competition approval and empirical calibration are not claimed.</p>
<p align="center"><a href="datasets/boston-central.html#boston-visual-gallery"><img alt="Shared Central Boston foundation: physical roads, H3 zones, study boundary and one ordered 23-link corridor." src="assets/boston/visual_release_r1/boston_network_zones.png" width="780"/></a></p>
<p><em>This is the spatial foundation, not one of the four demand-model stages. Parcel outlines provide geographic context, not building footprints. <a href="datasets/boston-visual-sources.html">Sources, units and original map gallery</a>.</em></p>
<h3 id="boston-population-and-household-preparation">Boston / Population and Household Preparation</h3>
<p>The <strong>U.S. Census Bureau's ACS 2024 five-year (2020–2024)</strong> block-group estimates were accessed through the <strong>Census Reporter <code>acs2024_5yr</code> mirror</strong> for Massachusetts Suffolk <code>025</code>, Middlesex <code>017</code> and Norfolk <code>021</code>; recorded source boundaries came from its <code>tiger2024</code> GeoJSON. The fixed core intersects <strong>174 source block groups</strong>. Those statistical polygons do not coincide with the <strong>177 clipped H3 r9 model zones</strong>. In EPSG:32619, each source estimate is assigned by <code>area(source ∩ clipped zone) / area(full source polygon)</code>; the outside-core share remains a spatial remainder, <strong>not</strong> an observed external-trip matrix. The allocation assumes uniform persons/households within each source polygon.</p>
<div class="table-scroll"><table>
<thead>
<tr>
<th>Prepared quantity</th>
<th style="text-align:right">Saved core value</th>
<th>Role and source</th>
</tr>
</thead>
<tbody>
<tr>
<td>Population, ACS <a href="https://api.census.gov/data/2024/acs/acs5/groups/B01003.html"><code>B01003</code></a></td>
<td style="text-align:right"><strong>171,049.520 persons</strong></td>
<td>Retained H3 demographic attribute, not the household-rate multiplier; acquired via <a href="https://github.com/censusreporter/census-api/blob/master/API.md">Census Reporter <code>acs2024_5yr</code></a></td>
</tr>
<tr>
<td>Households, ACS <a href="https://api.census.gov/data/2024/acs/acs5/groups/B11001.html"><code>B11001</code></a></td>
<td style="text-align:right"><strong>79,537.493 households</strong></td>
<td><code>P_i,p = H_i × r_p</code> with six transferred <a href="https://ctps.org/pub/tdm23_sc/tdm23.2.0/TDM23.2.0_Structures%20and%20Performance.pdf#page=148">CTPS TDM23.2.0 Table 74 rates</a></td>
</tr>
<tr>
<td>Activity attraction</td>
<td style="text-align:right">Separate <a href="https://www.mass.gov/info-details/massgis-data-property-tax-parcels">MassGIS Property Tax Parcels</a> nonresidential/mixed building-area weights</td>
<td>Proxy attraction margins, <strong>not measured employment</strong> or ACS allocation weights</td>
</tr>
</tbody>
</table></div>
<p align="center"><a href="datasets/boston-population-households.html"><img alt="Actual saved Suffolk block-group and clipped H3 geometry; the selected area share allocates population and households separately before household-based generation." src="assets/boston/population_r1/population_allocation.png" width="100%"/></a></p>
<p>The <a href="../examples/boston/population_r1/data/acs_block_group_stats.csv">ACS source statistics</a>, <a href="../examples/boston/population_r1/data/acs_block_group_h3_crosswalk.csv">source-to-H3 contributions</a>, <a href="../examples/boston/population_r1/data/population_or_household_by_zone.csv">H3 attributes</a>, <a href="../examples/boston/behavior_feedback_r1_semantic_fix_r1/data/external_flow_ledger.csv">outside-core ledger</a> and <a href="../examples/boston/behavior_feedback_r1_semantic_fix_r1/data/trip_generation_by_purpose.csv">generation rows</a> are directly openable. <a href="datasets/boston-population-households.html">Source versions, provider/download links, exact fields, assumptions and no-solver reproduction command →</a>. Source margins of error were retained; the H3 estimates do not have a validated propagated MOE. All 177 saved zones have source coverage; in general, missing is not zero.</p>
<h3 id="boston-the-retained-semantic-four-stage-chain">Boston / The retained semantic four-stage chain</h3>
<p><strong>This retained branch is a fixed-panel service-feedback example. The expanded computation follows in the next section.</strong> The numbered sections below describe the saved Boston implementation—not four generic software components.</p>
<div class="table-scroll"><table>
<thead>
<tr>
<th>Stage</th>
<th>Question and actual calculation</th>
<th>What you can inspect</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>01 · Trip generation</strong></td>
<td>How many trips start and end in each zone? Area-allocated ACS household estimates are multiplied by transferred regional rates by purpose; MassGIS activity supplies attraction weights.</td>
<td><a href="datasets/boston-behavior-feedback.html#step-1-trip-generation">Zonal productions and six purpose totals</a>: <strong>816,054.67 modeled workday person trips</strong>, not observed trips.</td>
</tr>
<tr>
<td><strong>02 · Trip distribution</strong></td>
<td>Where do those trips go? Gravity/IPF and purpose/time-specific PA-to-OD conversion create directed demand.</td>
<td><a href="datasets/boston-behavior-feedback.html#step-2-trip-distribution">The saved 177 × 177 HBW midday matrix</a>, totaling <strong>22,807.22 modeled person trips</strong>.</td>
</tr>
<tr>
<td><strong>03 · Mode choice</strong></td>
<td>Which travel alternatives are selected? Scheduled and observation-adjusted journey costs drive a nested response around regional baseline shares.</td>
<td><a href="datasets/boston-behavior-feedback.html#step-3-mode-choice">Saved S1/S2 costs and probability changes</a>. S1 is still a shared regional baseline, not an OD-specific absolute-cost model.</td>
</tr>
<tr>
<td><strong>04 · Traffic assignment</strong></td>
<td>Which roads carry the resulting vehicles? The selected private/occupied-vehicle demand is loaded through the same static FW model.</td>
<td><a href="datasets/boston-behavior-feedback.html#step-4-traffic-assignment">S1 road flows and S2−S1 differences</a>, with input and result tables.</td>
</tr>
</tbody>
</table></div>
<p><strong>The scope narrows deliberately:</strong> regional generation → saved HBW demand → <strong>36 fixed OD pairs × three midday departures</strong> → <strong>78 eligible OD–time cases</strong> → about <strong>202 assigned vehicle trips</strong>. These are different populations and units, not one mass-conserving funnel. The remaining 30 cases retain their exclusion and person-demand records; the full regional demand is not assigned by this panel.</p>
<div class="table-scroll"><table>
<tr><th>01 · Actual generation output</th><th>02 · Actual distribution output</th></tr>
<tr>
<td width="50%"><a href="datasets/boston-behavior-feedback.html#step-1-trip-generation"><img alt="Trip generation: saved modeled workday productions summed by the six source purpose codes." src="assets/boston/four_step_results_r1/step1_generation.png" width="100%"/></a></td>
<td width="50%"><a href="datasets/boston-behavior-feedback.html#step-2-trip-distribution"><img alt="Trip distribution: saved HBW midday origin-destination matrix in stable H3 ID order, with a declared log color scale." src="assets/boston/four_step_results_r1/step2_distribution.png" width="100%"/></a></td>
</tr>
<tr><td>Households and regional effective mean rates generate the modeled total. This is a result chart—not the residential-area input map.</td><td>Rows are origins and columns are destinations. These are modeled OD values, not GPS-inferred trips or mapped routes.</td></tr>
<tr><th>03 · Actual mode response</th><th>04 · Actual assignment output</th></tr>
<tr>
<td><a href="datasets/boston-behavior-feedback.html#step-3-mode-choice"><img alt="Mode choice: saved S2 minus S1 percentage-point changes for all nine model leaves in panel_od_019 at 12:30." src="assets/boston/four_step_results_r1/step3_mode_response.png" width="100%"/></a></td>
<td><a href="datasets/boston-behavior-feedback.html#step-4-traffic-assignment"><img alt="Traffic assignment: modeled S1 fixed-panel vehicle trips on the actual Boston road network." src="assets/boston/visual_release_r1/boston_panel_flow_s1.png" width="100%"/></a></td>
</tr>
<tr><td>The illustrated response depends on this OD's changed service costs. The common S1 shares are not newly estimated local baseline probabilities.</td><td>Static FW loads the selected vehicle panel. No regional background flow is included; this is not measured citywide congestion.</td></tr>
</table></div>
<p><a href="datasets/boston-behavior-feedback.html"><strong>Read the four stages with their inputs, operations and outputs →</strong></a> · <a href="datasets/boston-four-step-sources.html">Download the display data and check the source mapping</a></p>
<p><a id="how-gps-changes-the-result"></a></p>
<h3 id="boston-how-gps-changes-the-result">Boston / How GPS changes the result</h3>
<p><strong>GPS is not an unused map layer, and it is not a fifth stage.</strong> MBTA vehicle positions are matched to the network and related to transit service intervals. In this example, a saved interval observation changes the transit service input; stages 03 and 04 then recompute the dependent response. GPS does <strong>not</strong> determine the regional trip total or the gravity-model OD in this release.</p>
<p align="center"><a href="datasets/boston-gmns-exchange.html#from-gps-coordinates-to-gmns-linked-evidence"><img alt="The same twelve saved route-60 GPS positions before and after saved path association on identical Boston map bounds; ordered matched links join a separate modeled S1 road result." src="assets/boston/gmns_in_action_r1/gps_to_gmns_evidence.png" width="100%"/></a></p>
<p><em>Source observations → algorithm-derived matching → physical road attributes → separately modeled assignment results.</em> This <strong>qualified route-60 segment</strong> is a spatial-reference illustration, not the route-749 service-feedback event below or a matching-accuracy test. Its 26 ordered path occurrences and projected positions are saved outputs, not newly matched here. <a href="datasets/boston-gmns-exchange.html#from-gps-coordinates-to-gmns-linked-evidence">Shared network reference—not the same observed trip; inspect exact records →</a></p>
<pre><code class="language-text">Vehicle positions → road/service linkage → interval-time adjustment
                                               ↓
                 transit itinerary and travel cost
                                               ↓
                03  mode-share response → vehicle demand
                                               ↓
                04  FW road assignment → link-flow response
</code></pre>
<p>One saved trace uses route <strong>749</strong>, direction <strong>1</strong>, stop pair <strong>1788 → 5093</strong>: <strong>86 s sample-derived elapsed time versus 180 s planned</strong>. Applying the declared exploratory interval adjustment gives the following result for <strong>panel_od_019 at 12:30</strong>:</p>
<div class="table-scroll"><table>
<thead>
<tr>
<th>Quantity in the same OD–departure case</th>
<th style="text-align:right">S1 · planned service</th>
<th style="text-align:right">S2 · exploratory adjustment</th>
</tr>
</thead>
<tbody>
<tr>
<td>Transit journey time</td>
<td style="text-align:right">29.052 min</td>
<td style="text-align:right">27.486 min</td>
</tr>
<tr>
<td>Selected-itinerary fare</td>
<td style="text-align:right">USD 1.70</td>
<td style="text-align:right">USD 1.70</td>
</tr>
<tr>
<td>Walk-access-transit probability, μ_transit = 1</td>
<td style="text-align:right">4.0990%</td>
<td style="text-align:right">4.2246%</td>
</tr>
<tr>
<td>Private/occupied ride-service demand</td>
<td style="text-align:right">2.164631 vehicle trips</td>
<td style="text-align:right">2.161796 vehicle trips</td>
</tr>
</tbody>
</table></div>
<p>Across the <strong>whole eligible panel</strong>, S1/S2 vehicle inputs are <strong>202.078384 / 202.070733</strong>. Seventy-eight links differ by more than <code>1e-10</code>; the maximum absolute link difference is <strong>0.006603 modeled vehicle trips</strong>. A link difference aggregates contributing OD cases and is not attributable solely to the one trace above.</p>
<p><strong>Srestore</strong> switches the service overlay off and independently recomputes the affected costs, probabilities and demand, returning them to S1. This demonstrates an executable dependency, not independent prediction accuracy. The 13 interval adjustments each have one supporting event and are disabled by default.</p>
<p><a href="https://github.com/scholarhaozheng/mobility-network-lab/blob/main/examples/boston/behavior_feedback_r1_semantic_fix_r1/FEEDBACK_TRACE.md"><strong>Follow the exact observation → parameter → itinerary → probability → vehicle → road records →</strong></a> · <a href="datasets/boston-behavior-feedback.html#step-4-traffic-assignment">See the saved S2−S1 road map</a> · <a href="datasets/boston-central.html#one-saved-transit-position-projection">Inspect the separate GPS-to-road projection illustration</a></p>
<p><em>The projection map illustrates a different recorded segment; it is not presented as the same event as this feedback trace. The released calculation is a bounded technical example: no independently validated AM forecast, complete TDM23 reproduction or full-city multimodal assignment is claimed. <a href="datasets/boston-behavior-feedback.html#scope-and-assumptions">Scope and assumptions</a>.</em></p>
<h3 id="boston-scalable-assignment-is-now-the-primary-road-flow-result">Boston / Scalable assignment is now the primary road-flow result</h3>
<p>The same 5,091-link clipped network is now evaluated on progressively larger source-zone demand sets using the <strong>new-input generic FW entry</strong>, not a renamed copy of the 26-OD solution. Planned-service costs were computed for new OD records, and the fixed conditional four-mode specification uses their absolute attributes. Unknown four-mode input remains unknown.</p>
<div class="table-scroll"><table>
<thead>
<tr>
<th>Source-zone OD tier</th>
<th style="text-align:right">Selected person trips</th>
<th style="text-align:right">Evaluated person trips</th>
<th style="text-align:right">Loaded vehicle/PCE trips</th>
<th style="text-align:right">Loaded node ODs</th>
<th style="text-align:right">Positive physical links</th>
<th style="text-align:right">Accepted signed FW gap</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>500</strong></td>
<td style="text-align:right">2,643.767</td>
<td style="text-align:right">2,413.603</td>
<td style="text-align:right">1,936.238</td>
<td style="text-align:right">453</td>
<td style="text-align:right">1,653</td>
<td style="text-align:right">−4.59×10⁻¹⁶</td>
</tr>
<tr>
<td><strong>2,000</strong></td>
<td style="text-align:right">8,415.295</td>
<td style="text-align:right">7,248.674</td>
<td style="text-align:right">5,815.569</td>
<td style="text-align:right">1,684</td>
<td style="text-align:right">1,784</td>
<td style="text-align:right">5.60×10⁻⁶</td>
</tr>
<tr>
<td><strong>All 30,790 interzonal</strong></td>
<td style="text-align:right">22,633.470</td>
<td style="text-align:right">20,231.449</td>
<td style="text-align:right">16,259.122</td>
<td style="text-align:right"><strong>17,522</strong></td>
<td style="text-align:right"><strong>2,147</strong></td>
<td style="text-align:right"><strong>6.81×10⁻⁶</strong></td>
</tr>
</tbody>
</table></div>
<p>The largest accepted FW result has <strong>133 physical endpoints</strong>, Beckmann objective <strong>73,552.277556 PCE-minutes</strong>, zero maximum OD residual and <code>2.84×10⁻¹⁴</code> link reconstruction error. These are checked numerical approximations for a <strong>conditional HBW-midday research cohort</strong>. They do not include all modes, all travelers, external/background traffic or empirical calibration.</p>
<div class="table-scroll"><table class="figure-grid"><tr><th>Source zones: selected demand coverage</th><th>Physical roads: accepted all-tier FW</th></tr><tr><td width="50%"><a href="BOSTON_SCALE_RESULTS.html"><img alt="Saved all-interzonal selected source-zone production and attraction coverage." src="assets/boston/scalable_tool_r1/source_zone_all_coverage.png" width="100%"/></a></td><td width="50%"><a href="BOSTON_SCALE_RESULTS.html"><img alt="All-tier accepted FW: 17,522 loaded node ODs and 2,147 positive links on the clipped physical network." src="assets/boston/scalable_tool_r1/fw_all_flow.png" width="100%"/></a></td></tr><tr><td>30,790 source pairs are not 30,790 loaded physical OD keys. Zone access, input support and same-node accounting remain explicit.</td><td>Model PCE flow, not observed counts. The three tier maps use tier-specific legend maxima; equal colors across tiers do not imply equal values.</td></tr></table></div>
<p><a href="assets/boston/scalable_tool_r1/fw_500_flow.png">500-tier map</a> · <a href="assets/boston/scalable_tool_r1/fw_2000_flow.png">2,000-tier map</a> · <a href="assets/boston/scalable_tool_r1/endpoint_all_coverage.png">All-tier endpoint coverage</a> · <a href="BOSTON_SCALE_RESULTS.html">Complete scale, runtime and resource records</a>.</p>
<div class="table-scroll"><table>
<thead>
<tr>
<th>Expanded method status</th>
<th>500 tier</th>
<th>2,000 tier</th>
<th>All interzonal</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>FW</strong></td>
<td>Accepted</td>
<td>Accepted</td>
<td>Accepted</td>
</tr>
<tr>
<td><strong>Finite full-path</strong></td>
<td>Resource gate before solve; 2,261-path pool exists</td>
<td>Valid 8,412-path K5 pool; solve resource-gated</td>
<td>Path-pool preparation gate; not built</td>
</tr>
<tr>
<td><strong>Native L3, requested 25% / 50% fractions</strong></td>
<td>Basis/solve resource-gated</td>
<td>Basis/solve resource-gated</td>
<td>Pool/basis resource-gated</td>
</tr>
</tbody>
</table></div>
<p>A separate <strong>new-input two-OD fixture</strong> actually ran finite full path and native L3 with IPOPT. That demonstrates changed-input method execution, not success at the large tiers. Accepted FW points have one positive saved path per loaded OD; larger coverage alone is not proof of a hard route-splitting or compression speedup experiment. No expanded L3 map is fabricated or substituted with FW.</p>
<p><a id="boston-case--saved-assignment-methods"></a></p>
<h3 id="boston-small-controlled-assignment-method-comparison">Boston / Small controlled assignment-method comparison</h3>
<p>The real-city <a href="cases/boston.html">Boston case</a> includes <strong>both</strong> the GMNS/four-stage/GPS workflow above <strong>and</strong> executed static assignment methods. The earlier semantic S1/S2 service-feedback example used about <strong>202.078384 / 202.070733</strong> modeled vehicle trips. A separate conditional absolute-attribute choice sensitivity evaluates DA/S2/S3/TW for sufficient-vehicle households: 87 of 108 fixed OD-time objects had known four-mode inputs, 21 remained unknown, and only 78 common objects were road-loaded. Its <a href="https://github.com/scholarhaozheng/mobility-network-lab/blob/main/examples/boston/conditional_choice_r1/README.md">saved probabilities and specification</a> are a reduced transfer sensitivity, not calibrated all-mode TDM23 or an independent AM validation.</p>
<p>For the <strong>fixed ABS_PLANNED</strong> algorithm comparison, FW, the solved uncompressed path reference and two native Diagnostic L3 representations all use the same 5,091 physical links, 26 endpoint OD pairs, 203.6604786350987 modeled vehicle trips, heterogeneous BPR costs and frozen 130-path pool. ABS_OBS_EXPLORATORY FW is a separate service scenario, not another compression method or the old S1 export. <a href="cases/boston-assignment.html">Read full method/instance details and the full-size gallery</a>.</p>
<div class="table-scroll"><table>
<thead>
<tr>
<th>Boston saved method / run</th>
<th style="text-align:right">Original Beckmann F (vehicle-minutes)</th>
<th>Original-space result and scope</th>
</tr>
</thead>
<tbody>
<tr>
<td><a href="../examples/boston/assignment_methods_r1/reference/fw_solution.csv">FW · ABS_PLANNED</a></td>
<td style="text-align:right">707.0579230712884</td>
<td>Same-network static FW; <a href="../algorithms/static_fw/tap_frank_wolfe.py">actual source</a></td>
</tr>
<tr>
<td><a href="../examples/boston/assignment_methods_r1/reference/full_path_flow.csv">Uncompressed 130-path SLSQP</a></td>
<td style="text-align:right">707.0579230712882</td>
<td>Exact saved OD equalities on this finite pool; <a href="https://github.com/scholarhaozheng/mobility-network-lab/blob/main/algorithms/finite_path_reference/README.md">solver/config</a></td>
</tr>
<tr>
<td><a href="../examples/boston/assignment_methods_r1/runs/rank26/outer_02_check.json">Native L3 · rank 26 · outer 02</a></td>
<td style="text-align:right">707.0578811137339</td>
<td>Max OD residual 8.255328278750085e-7; signed full-network relative gap <strong>−5.933966773022305e-8</strong>; 52 path coordinates + 5,091 links = 5,143 variables</td>
</tr>
<tr>
<td><a href="../examples/boston/assignment_methods_r1/runs/rank52/outer_02_check.json">Native L3 · rank 52 · outer 02</a></td>
<td style="text-align:right">707.0578811562873</td>
<td>Max OD residual 8.254705861077127e-7; signed full-network relative gap <strong>−5.927948547394401e-8</strong>; 78 path coordinates + 5,091 links = 5,169 variables</td>
</tr>
<tr>
<td><a href="../examples/boston/conditional_choice_r1/fw_abs_obs_exploratory_solution.csv">FW · ABS_OBS_EXPLORATORY</a></td>
<td style="text-align:right">707.043586277782</td>
<td><strong>Different demand:</strong> 203.6573680559407 vehicle trips; not a same-instance rank comparison</td>
</tr>
</tbody>
</table></div>
<p>The two native points passed declared numerical checks, but their <strong>negative gaps reflect tolerated OD deficits</strong>, not exact feasible equilibria, improved traffic, or roundoff. Their initialization reused the full-path reference. No cold-start acceleration, peak IPOPT memory or independent performance validation is claimed.</p>
<p align="center"><a href="cases/boston-assignment.html#comparison-board"><img alt="Comparison board: FW and native L3 rank 26/rank 52 on the same small ABS_PLANNED input; below are the two signed micro-scale differences and interpretation." src="assets/presentation_r3/boston_method_comparison.png" width="100%"/></a></p>
<p><strong>Read across methods, then down to the signed difference.</strong> The first row compares three absolute-flow maps; the second row gives their differences and interpretation. This is the <strong>small 26-node-OD control</strong>, not the expanded 17,522-node-OD FW run.</p>
<p>Original full-resolution panels remain available: <a href="assets/boston/assignment_methods_r1/boston_abs_planned_fw_flow.png">FW</a> · <a href="assets/boston/assignment_methods_r1/boston_abs_planned_l3_rank26_flow.png">rank 26</a> · <a href="assets/boston/assignment_methods_r1/boston_abs_planned_l3_rank52_flow.png">rank 52</a> · <a href="assets/boston/assignment_methods_r1/boston_abs_planned_l3_rank26_minus_fw.png">rank 26 − FW</a> · <a href="assets/boston/assignment_methods_r1/boston_abs_planned_l3_rank52_minus_fw.png">rank 52 − FW</a>.</p>
<p><em>All three absolute maps share one scale; the two signed maps share a zero-centred scale. They can look almost identical because the maximum native–FW link differences are only about <strong>5.89 × 10⁻⁶ modeled vehicle trips</strong>. These are saved model results, not GPS counts. <a href="assets/boston/assignment_methods_r1/boston_abs_planned_assignment_links.csv">Inspect all 5,091 full-precision physical-link rows</a> · <a href="assets/boston/assignment_methods_r1/BOSTON_ASSIGNMENT_FIGURE_SOURCES.json">Source/field/scale manifest</a> · <a href="../tools/visuals/render_boston_assignment.py">no-solve renderer</a>. GMNS physical link identities and the documented export crosswalk let method outputs attach to the same road network without changing the older S1 demand exchange.</em></p>
<pre><code class="language-bash">python -B tools/mcl_results.py list --case boston
python -B tools/mcl_results.py verify-saved --run boston-abs-planned-full-path
python -B tools/mcl_results.py verify-saved --run boston-abs-planned-l3-rank26-outer02
</code></pre>
<p>These commands inspect saved points; they do not solve, build paths, refit demand or match new GPS data.</p>
<h3 id="boston-bounded-finite-spacetime-cg-pilot">Boston / Bounded finite space–time CG pilot</h3>
<p>This is <strong>one</strong> accepted 90-physical-node, 125-directed-link, 10-OD finite time-expanded instance (3-second steps; 100-step horizon), not the 5,091-link static Boston assignment or a second Boston scale. The fixed-cost hard-capacity objective is distinct from FW/Beckmann.</p>
<p align="center"><a href="cases/boston-space-time.html"><img alt="Boston saved-result CG sequence in six panels: actual time-indexed column; Phase-I artificial-flow clearance; B07/B09/B10 shared-capacity reallocation; Phase-II reference-objective agreement; final physical-link movement flow and validation; independent pricing closure for 10 of 10 demands." src="assets/presentation_r5/boston_cg_case_sequence.png" width="100%"/></a></p>
<p><em>Figure — Boston bounded CG pilot.</em> (a) A recorded B07 path mapped into time-indexed arcs; (b) Phase-I artificial-flow clearance; (c) the B07/B09/B10 shared-capacity event; (d) Phase-II objective against the same-graph arc-flow reference; (e) final physical-link movement flow; (f) independent by-demand pricing check. The display crops retain the plotted evidence; full uncropped figures, numerical validation and limitations are in the <a href="cases/boston-space-time.html">case study</a>. <a href="assets/boston/space_time_cg_r4/boston_cg_summary_panel.png">Supplementary four-panel summary</a> · <a href="#sioux-falls">Matching Sioux Falls figure below</a> · <a href="assets/presentation_r5/boston_cg_case_sequence.svg">SVG</a> · <a href="assets/presentation_r5/CG_CASE_SEQUENCE_SOURCES.json">Source hashes and display crops</a>. No scientific model was rerun.</p>
<div class="table-scroll"><table>
<thead>
<tr>
<th>Shared CG stage</th>
<th>Boston result</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>From the physical network to time-indexed columns</strong></td>
<td>Actual B07 column on the accepted 90-node/125-link pilot</td>
</tr>
<tr>
<td><strong>Phase I restores feasibility</strong></td>
<td>Artificial flow <strong>20.5536128974 → 0</strong> in round <strong>90</strong></td>
</tr>
<tr>
<td><strong>A new path can help a different OD</strong></td>
<td>Recorded B07/B09/B10 shared-capacity reallocation</td>
</tr>
<tr>
<td><strong>Phase II improves the real-path objective</strong></td>
<td><strong>64.39686151152952</strong> after 15 rounds; reference-objective agreement on the same finite time-expanded graph</td>
</tr>
<tr>
<td><strong>Final physical-link movement flow and validation</strong></td>
<td>52 positive-flow physical links; demand, capacity, path and back-projection checks pass</td>
</tr>
<tr>
<td><strong>Independent pricing closure</strong></td>
<td>Five continuation rounds, final column pool <strong>152 → 167</strong>; B01–B10 pass at <code>1e-6</code></td>
</tr>
</tbody>
</table></div>
<p>The <a href="cases/boston-space-time.html">detailed Boston CG page</a> retains the full figure family, exact plot inputs, editable SVGs and hashed provenance. The 15 R4 certificate columns have zero final flow; they complete the dual/pricing certificate rather than create additional physical traffic. Final physical-link movement flows remain unchanged from R3 within numerical precision. The second-machine receiver check remains pending. These are saved-result visualizations only; no model was rerun for this public update.</p>
<p><a id="sioux-falls"></a></p>
<h2 id="04-case-study-sioux-falls">04 / Case study — Sioux Falls</h2>
<p><strong>What this case demonstrates.</strong> A classic supplied-demand benchmark with static FW, accepted official TAPLab/<code>tap-b</code> Algorithm B parity and native L3 research, plus distinct 200/250-OD finite space–time CG instances. <strong>Not modeled here:</strong> real-city trip generation, destination/mode estimation or GPS service feedback. The benchmark does not become a modern city dataset because it shares the framework.</p>
<p><a id="sioux-falls-benchmark-series"></a></p>
<h3 id="sioux-falls-static-methods-and-retained-numerical-candidates">Sioux Falls / Static methods and retained numerical candidates</h3>
<p>The <a href="cases/sioux-falls.html">Sioux Falls case</a> also has actual static assignment work. Its historical <a href="datasets/sioux-static-fw.html">FW result</a> has Beckmann F <strong>4,236,715.140437842</strong>, but the retained runtime OD identity is insufficient to declare it a same-input reference for the native profile. The corrected <a href="https://github.com/scholarhaozheng/mobility-network-lab/blob/main/algorithms/path_compression/diagnostic_l3/README.md">native Diagnostic L3 implementation</a> has accepted <strong>outer-04</strong> points on the frozen 76-link, 528-positive-OD, 2,218-path static instance (rank 50; 585 reduced path coordinates; 661 total native variables):</p>
<div class="table-scroll"><table>
<thead>
<tr>
<th>Sioux native configuration</th>
<th style="text-align:right">Original Beckmann component F</th>
<th style="text-align:right">Max OD residual</th>
<th style="text-align:right">Full-network relative cost gap</th>
</tr>
</thead>
<tbody>
<tr>
<td><a href="../examples/sioux-falls/native_l3_r1/runs/SiouxFalls/A_REG001/outer_04_check.json">A_REG001 · gamma=0.01</a></td>
<td style="text-align:right">4,325,864.946597109</td>
<td style="text-align:right">5.548833712509804e-7</td>
<td style="text-align:right"><strong>8.167461%</strong></td>
</tr>
<tr>
<td><a href="../examples/sioux-falls/native_l3_r1/runs/SiouxFalls/B_BECKMANN/outer_04_check.json">B_BECKMANN · gamma=0</a></td>
<td style="text-align:right">4,289,674.484214505</td>
<td style="text-align:right">6.957361051718181e-7</td>
<td style="text-align:right"><strong>4.381867%</strong></td>
</tr>
</tbody>
</table></div>
<p>Both pass recorded numerical feasibility, but neither has a full-network UE certificate or new empirical validation. A is regularized and B is not. Sioux demand is exogenous; no real-city GPS/GTFS or Boston-style four-stage estimation was added.</p>
<p>The separate <a href="cases/sioux-algorithm-b.html">official TAPLab-adapter Algorithm B classic result</a> has Beckmann <strong>4,231,335.287110682 vehicle-min</strong>, independent relative gap <strong>4.4984e-9</strong>, exact physical-link-flow parity through the registered CLI/direct callable, and a certified <code>taplab verify</code> output. It is the static 528-OD case, not either selected-OD space–time CG experiment.</p>
<h3 id="sioux-falls-historical-200250-od-finite-spacetime-cg">Sioux Falls / Historical 200/250-OD finite space–time CG</h3>
<p>The figures below are <strong>historical finite time-expanded CG</strong>, not native-L3 runs or present-day city observations. Explore the actual saved results before running an example. The two panels below are <strong>different selected-OD benchmark instances</strong>, not a comparison of algorithms on the same demand.</p>
<p align="center"><a href="cases/sioux-space-time.html"><img alt="Sioux Falls saved-result CG sequence in the same six-panel order as Boston: XS170 time-indexed column; separate 200- and 250-OD Phase-I clearance; XS170/XS169 shared-capacity reallocation; separate Phase-II reference-objective traces; final physical-link movement flows and validation; independent pricing closure explicitly not established." src="assets/presentation_r5/sioux_cg_case_sequence.png" width="100%"/></a></p>
<p><em>Figure — Sioux Falls historical CG benchmarks.</em> (a) A recorded XS170 time-indexed column; (b) separate 200- and 250-OD Phase-I traces; (c) the XS170/XS169 shared-capacity exchange; (d) separate Phase-II objective traces against each instance's own reference; (e) final physical-link movement flows; (f) independent pricing closure <strong>not established</strong>. The two OD selections are distinct benchmark instances, not repeated trials. Full uncropped figures and numerical checks are in the <a href="cases/sioux-space-time.html">case study</a>. <a href="#boston">Matching Boston figure above</a> · <a href="assets/presentation_r5/sioux_cg_case_sequence.svg">SVG</a> · <a href="assets/presentation_r5/CG_CASE_SEQUENCE_SOURCES.json">Source hashes and display crops</a>. No scientific model was rerun.</p>
<div class="table-scroll"><table>
<tr>
<th>Sioux Falls · 200 OD</th><th>Sioux Falls · 250 OD</th>
</tr>
<tr>
<td width="50%"><a href="datasets/sioux-200od.html"><img alt="200-OD selected subset: final physical-link movement flow" src="assets/benchmarks/sioux_200od_final_physical_link_flow.png" width="100%"/></a></td>
<td width="50%"><a href="datasets/sioux-250od.html"><img alt="250-OD selected subset: final physical-link movement flow" src="assets/benchmarks/sioux_250od_final_physical_link_flow.png" width="100%"/></a></td>
</tr>
<tr>
<td>24 nodes · 64 selected links · 446 final columns<br/><a href="datasets/sioux-200od.html">Open 200-OD results →</a></td>
<td>24 nodes · 69 selected links · 567 final columns<br/><a href="datasets/sioux-250od.html">Open 250-OD results →</a></td>
</tr>
<tr>
<td><a href="assets/benchmarks/sioux_200od_phase2_objective_trace.png"><img alt="200-OD Phase-II objective trace from saved successful results" src="assets/benchmarks/sioux_200od_phase2_objective_trace.png" width="100%"/></a></td>
<td><a href="assets/benchmarks/sioux_250od_phase2_objective_trace.png"><img alt="250-OD Phase-II objective trace from saved successful results" src="assets/benchmarks/sioux_250od_phase2_objective_trace.png" width="100%"/></a></td>
</tr>
</table></div>
<p><em>Map line width represents final movement flow accumulated over the modelled time horizon. These are schematic physical-link views, not observed traffic, static V/C or a full 528-OD assignment. Opposite directions can overlap in the existing map rendering; use the data cards for numerical interpretation.</em></p>
<div class="table-scroll"><table>
<thead>
<tr>
<th>Road benchmark</th>
<th style="text-align:right">Physical nodes</th>
<th style="text-align:right">Selected links</th>
<th style="text-align:right">OD pairs</th>
<th style="text-align:right">Final columns</th>
<th style="text-align:right">Objective</th>
<th>Access</th>
</tr>
</thead>
<tbody>
<tr>
<td><a href="datasets/sioux-200od.html">Sioux Falls · 200 OD</a></td>
<td style="text-align:right">24</td>
<td style="text-align:right">64</td>
<td style="text-align:right">200</td>
<td style="text-align:right">446</td>
<td style="text-align:right">943,155.589771</td>
<td>Historical result record</td>
</tr>
<tr>
<td><a href="datasets/sioux-250od.html">Sioux Falls · 250 OD</a></td>
<td style="text-align:right">24</td>
<td style="text-align:right">69</td>
<td style="text-align:right">250</td>
<td style="text-align:right">567</td>
<td style="text-align:right">1,521,090.836620</td>
<td>Historical result record</td>
</tr>
<tr>
<td><a href="datasets/sioux-static-fw.html">Sioux Falls · static FW</a></td>
<td style="text-align:right">24</td>
<td style="text-align:right">76</td>
<td style="text-align:right">528</td>
<td style="text-align:right">—</td>
<td style="text-align:right">4,236,715.140438</td>
<td>Approximate static baseline</td>
</tr>
</tbody>
</table></div>
<p><a href="visualizations.html"><strong>All six benchmark figures</strong></a> · <a href="datasets.html">Network and example catalog</a> · <a href="outputs.html">Verification scope</a></p>
<p>Historical road records include checked results and approved figures, <strong>not redistributed raw inputs</strong>. Self-contained <a href="examples.html">synthetic reference inputs</a> are bundled separately for installation and regression testing. Static FW and space–time CG solve different model formulations; their objective values are not directly comparable.</p>
<h3 id="sioux-falls-from-the-physical-network-to-time-indexed-columns">Sioux Falls / From the physical network to time-indexed columns</h3>
<p><strong>The CG examples solve a finite space–time linear flow model with fixed arc costs and explicit capacities.</strong> They are not the same objective as static BPR/Beckmann FW or native L3. Source and sink connectors attach each demand to the time network, movement arcs advance to arrival times, and waiting arcs permit modeled delay.</p>
<p><strong>Panel (a) is an explanatory local cutaway—not a plot of every node and arc.</strong> Positions are schematic; selected IDs and times come from saved records. The highlighted column is <code>source_XS170 → xs_link19_t0 → xs_link15_t2 → sink_XS170_5_t6</code>, corresponding to physical nodes <code>8 → 6 → 5</code> at times <code>0 → 2 → 6</code>. The rest of the horizon and demand-specific connectors are not drawn. <a href="assets/presentation_r3/sioux_space_time_construction.png">Full annotated construction source</a> · <a href="cases/sioux-space-time.html">Construction fields and mappings</a>.</p>
<h3 id="sioux-falls-phase-i-restores-feasibility">Sioux Falls / Phase I restores feasibility</h3>
<div class="table-scroll"><table class="figure-grid"><tr><th>200 OD · artificial flow clears in round 51</th><th>250 OD · artificial flow clears in round 62</th></tr><tr><td width="50%"><a href="assets/sioux/phase_i_r1/sioux_falls_200od_phase_i_academic.png"><img alt="Supplied 200-OD artificial-flow trace, starting at 749.807 and clearing in round 51." src="assets/sioux/phase_i_r1/sioux_falls_200od_phase_i_academic.png" width="100%"/></a></td><td width="50%"><a href="assets/sioux/phase_i_r1/sioux_falls_250od_phase_i_academic.png"><img alt="Supplied 250-OD artificial-flow trace, starting at 4082.888 and clearing in round 62." src="assets/sioux/phase_i_r1/sioux_falls_250od_phase_i_academic.png" width="100%"/></a></td></tr></table></div>
<div class="table-scroll"><table>
<thead>
<tr>
<th>Saved observation</th>
<th style="text-align:right">200 OD</th>
<th style="text-align:right">250 OD</th>
</tr>
</thead>
<tbody>
<tr>
<td>Initial artificial flow</td>
<td style="text-align:right">749.806844</td>
<td style="text-align:right">4,082.887577</td>
</tr>
<tr>
<td>Demands initially carrying artificial flow</td>
<td style="text-align:right">2</td>
<td style="text-align:right">5</td>
</tr>
<tr>
<td>Phase-I zero round</td>
<td style="text-align:right">51</td>
<td style="text-align:right">62</td>
</tr>
<tr>
<td>Added Phase-I / Phase-II columns</td>
<td style="text-align:right">51 / 195</td>
<td style="text-align:right">62 / 255</td>
</tr>
<tr>
<td>Final column pool</td>
<td style="text-align:right">446</td>
<td style="text-align:right">567</td>
</tr>
<tr>
<td>Objective / arc-flow LP reference on the same selected-OD finite time-expanded graph</td>
<td style="text-align:right">943,155.589771</td>
<td style="text-align:right">1,521,090.836620</td>
</tr>
<tr>
<td>Absolute objective difference</td>
<td style="text-align:right">2.33×10⁻¹⁰</td>
<td style="text-align:right">0</td>
</tr>
<tr>
<td>Maximum final demand residual / capacity violations</td>
<td style="text-align:right">0 / 0</td>
<td style="text-align:right">0 / 0</td>
</tr>
</tbody>
</table></div>
<p>The 200-OD selection is contained in the 250-OD selection. There is one recorded run per size, with different iteration/candidate caps. These are <strong>descriptive historical runs</strong>, not repeated runtime trials, a scaling law or a global pricing-closure certificate. The original run summaries explicitly leave <code>optimality_claimed</code> and <code>full_cg_global_convergence_claimed</code> false.</p>
<h3 id="sioux-falls-a-new-path-can-help-a-different-od">Sioux Falls / A new path can help a different OD</h3>
<p>At round 34 (200 OD) and round 39 (250 OD), pricing selected a new path for <strong>XS170</strong>, but <strong>XS169</strong> lost 500 units of artificial flow after restricted-master reoptimization. XS170's 500 real units moved away from <code>xs_link21_t1</code>; XS169's real flow on that binding shared arc grew from 150.193 to 650.193. The total arc load stayed at its 5,050.193 capacity.</p>
<p>Panel (c) shows this recorded coupled-master mechanism, not a proof that this one path was uniquely necessary. The raw capacity dual stays approximately −1 under the saved solver convention. <a href="assets/presentation_r5/sioux_shared_capacity_canonical.png">Standalone capacity plot</a> · <a href="assets/sioux/phase_i_r1/od_level_phase_i_clearance.png">OD-level supplementary figure</a> · <a href="assets/presentation_r3/sioux_capacity_exchange.png">Earlier accepted capacity diagram</a> · <a href="assets/presentation_r5/SIOUX_CAPACITY_CANONICAL_SOURCES.json">Saved plot input and hashes</a> · <a href="assets/sioux/phase_i_r1/data/200_phase_i_trace.csv">Saved trace CSVs</a> · <a href="cases/sioux-space-time.html">Full Sioux CG explanation</a>.</p>
<h3 id="sioux-falls-phase-ii-improves-the-real-path-objective">Sioux Falls / Phase II improves the real-path objective</h3>
<p>The retained 200-OD and 250-OD Phase-II traces are shown above with their final physical-link movement-flow views. Each objective is compared with the arc-flow LP on the <strong>same selected-OD finite time-expanded graph</strong>. The two benchmark objective values must not be compared as if they were alternative algorithms on one demand set.</p>
<h3 id="sioux-falls-final-physical-link-movement-flow-and-validation">Sioux Falls / Final physical-link movement flow and validation</h3>
<p>The 200-OD and 250-OD saved views aggregate final time-indexed movement flow back to physical links. Both retained runs have zero final demand residual and zero capacity violations, and both have reference-objective agreement. These are schematic benchmark views, not observed traffic or static V/C.</p>
<h3 id="sioux-falls-independent-pricing-closure">Sioux Falls / Independent pricing closure</h3>
<p><strong>Not established for the retained 200-OD and 250-OD runs.</strong> Reference-objective agreement remains valid, but Boston's independent pricing-closure certificate is not transferred to Sioux Falls. <a href="cases/sioux-space-time.html#6-independent-pricing-closure">Exact status and reproduction limits</a>.</p>
<p><a id="hong-kong"></a></p>
<h2 id="05-case-study-hong-kong-bounded-gmnsdata-pilot">05 / Case study — Hong Kong bounded GMNS/data pilot</h2>
<p><strong>What this case demonstrates.</strong> Official-derived object alignment in Tsim Sha Tsui–Jordan: <strong>780 physical nodes, 1,239 directed physical links, 95 SSG fine zones, 10 STPUG parent zones, 95 centroids and 190 nonphysical connectors</strong>. Transit relationships retain <strong>183 GTFS stops and 294 route IDs</strong>; a single detector snapshot retains <strong>50 lane observations</strong>. The 2021 census allocation yields <strong>90,677.156 persons and 36,228.315 households</strong> on the bounded pilot geography. <a href="cases/hong-kong-gmns-pilot.html">The full case, five figures, source/rights records and commands</a>.</p>
<p align="center"><a href="cases/hong-kong-gmns-pilot.html"><img alt="Hong Kong bounded pilot physical road graph and source-backed hierarchical statistical zones" src="assets/hong_kong/gmns_pilot_r1/02_roads_zones.svg" width="100%"/></a></p>
<p><em>Source-backed roads and zones, not modeled assignment flow.</em> Centroid access lines are nonphysical. The demand tables are deterministic engineering seeds, not observed/calibrated OD. The public validator and trace tool check relationships offline, but <strong><code>assignment_ready=false</code> and no assignment was run</strong>: accepted free speed, lanes, period capacities, turn enforcement and all-OD directed reachability are still missing. The optional UrbanNav reference trajectory is not traffic demand; its point-level derivatives are private. <a href="https://github.com/scholarhaozheng/mobility-network-lab/blob/main/examples/hong-kong/gmns_pilot_r1/README.md">Open the public instance</a> · <a href="../examples/hong-kong/gmns_pilot_r1/instance/ASSIGNMENT_GATE.json">Assignment gate</a> · <a href="https://github.com/scholarhaozheng/mobility-network-lab/blob/main/examples/hong-kong/gmns_pilot_r1/ATTRIBUTION.md">Attribution</a>.</p>
<p><a id="run-your-input"></a></p>
<h2 id="06-run-new-inputs-or-inspect-saved-results">06 / Run new inputs, or inspect saved results</h2>
<p><strong>These are two different operations.</strong> The new generic preparation/solve entry computes a fresh result from supplied inputs. The saved-result entries below inspect frozen experiments. A documentation build never silently invokes a solver.</p>
<h3 id="new-vehicle-od-preparation-fw-verification-map">New vehicle OD → preparation → FW → verification → map</h3>
<pre><code class="language-bash">python -B tools/mcl_assignment.py prepare --input examples/scalable_vehicle_fixture/network --demand examples/scalable_vehicle_fixture/vehicle.csv --config examples/scalable_vehicle_fixture/config.json --output "my results/instance"
python -B tools/mcl_assignment.py solve --instance "my results/instance" --method fw --output "my results/fw"
python -B tools/mcl_assignment.py verify --run "my results/fw"
python -B tools/mcl_assignment.py plot --run "my results/fw" --output "my results/figures"
</code></pre>
<p>The supported direct-vehicle profile is single-class, fixed-demand and static. It retains text IDs and parallel physical links; units, capacity basis, period and PCE factor are explicit. Unsupported turn-state or class/time inputs are rejected rather than ignored. <code>prepare</code>, FW and <code>verify</code> use the standard library; plotting and optional native methods have separate dependencies.</p>
<p>A second entry accepts person OD, supported absolute skims, the fixed conditional choice specification and occupancy configuration. It feeds the same vehicle-assignment interface; it is not an arbitrary calibrated choice-model library. <a href="RUN_YOUR_OWN_GMNS.html">Full new-input contract and commands</a> · <a href="https://github.com/scholarhaozheng/mobility-network-lab/blob/main/examples/boston/scalable_tool_r1/README.md">Boston scale profile</a> · <a href="SCALABLE_TOOL_DATA_NOTICE.html">Data and dependency terms</a>.</p>
<p><a id="mobility-data-support"></a></p>
<h2 id="mobility-data-support-1">Mobility data support</h2>
<p>Supporting mobility data remain distinct from runnable city models and from the bounded Hong Kong GMNS/data pilot.</p>
<h3 id="open-mobility-evidence">Open mobility evidence</h3>
<p><strong>Explore the data behind a city model, then prepare the records you need.</strong> Selected Open Mobility Data Visibility (OMDV) results now include a downloadable, non-geometric 11,422-city evidence table and actual source-record → content-SHA → city relationships. The executable tools query those records, organize local catalogs and inspect a user-supplied GTFS ZIP.</p>
<!-- open-evidence-overview:start -->
<div class="table-scroll"><table>
<tr>
<td data-evidence-layer="global_city_frame" width="50%"><b>11,422 urban centres</b><br/><a href="open-data.html#global-city-frame">City frame &amp; catalog visibility</a><br/>A common GHSL study frame with explicitly defined catalog-matching scenarios.</td>
<td data-evidence-layer="gtfs_static" width="50%"><b>2,959 cities with GTFS stop evidence</b><br/><a href="open-data.html#gtfs-static">Scheduled-transit evidence</a><br/>4,425 unique parseable content hashes in the all-retained view; city evidence uses inside-polygon stops.</td>
</tr>
<tr>
<td data-evidence-layer="gtfs_realtime"><b>2,465 endpoint representatives</b><br/><a href="open-data.html#gtfs-realtime">GTFS-Realtime source context</a><br/>Metadata accounting and bounded snapshot classifications, not a live health monitor.</td>
<td data-evidence-layer="osm_map_features"><b>29 regional extracts</b><br/><a href="open-data.html#osm">OSM map-feature evidence</a><br/>791 of 916 sampled urban-centre rows have bbox-joined point-feature evidence.</td>
</tr>
<tr>
<td data-evidence-layer="gbfs_shared_mobility"><b>1,516 shared-mobility registry rows</b><br/><a href="open-data.html#gbfs-and-shared-mobility">GBFS source context</a><br/>48 countries represented; location strings are not reviewed city matches.</td>
<td data-evidence-layer="model_interoperability"><b>13 standards and tools</b><br/><a href="interoperability.html">Model-interface crosswalk</a><br/>GMNS, TNTP, GTFS and related formats: references and reuse pathways, not thirteen bundled converters.</td>
</tr>
</table></div>
<!-- open-evidence-overview:end -->
<p>These evidence layers are not additive. Each value is tied to its own unit, source frame and retained research snapshot. They do not measure live service coverage or the number of runnable city models. The public release includes a <strong>selected result projection</strong>, provenance and executable tools—not raw feeds, provider URLs, geometry or live endpoint checks. <a href="open-data-explorer.html">Browse/download 11,422 city rows</a> · <a href="open-data-sources.html">Sources and reproduction scope</a> · <a href="omdv-provenance.html">Trace each metric</a></p>
<h3 id="executable-data-tools-query-evidence-and-prepare-your-own-records">Executable data tools: query evidence and prepare your own records</h3>
<p>The authorized OMDV workflow normalizes a user-supplied feed catalog and city table, performs exact city/country <strong>named-entity matching</strong>, and writes standardized records, unmatched/ambiguous statuses and quality checks.</p>
<pre><code class="language-bash">python -m pip install -r requirements-data-tools.txt
python -B tools/mcl_data.py catalog-city-match --catalog examples/data-tools/feeds_sample.csv --cities examples/data-tools/external_city_universe_sample.csv --output results/data-tools-demo
python -B tools/mcl_data.py query-city --name "Hong Kong" --country CHN --include-relations
python -B tools/mcl_data.py process-gtfs --zip path/to/feed.zip --output results/gtfs-content-report
</code></pre>
<p><code>query-city</code> prefers the stable city ID and explicitly rejects duplicate name/country keys unless <code>--all-matches</code> is requested. <code>process-gtfs</code> reuses the authorized OMDV content parser with a streamed stop-times pass; it makes no network request and does not extract or modify the ZIP. These are evidence/content tools, not GPS-to-road matching, traffic-zone creation, OD estimation or an automatic connection to the solver.</p>
<p><a href="open-data-explorer.html"><strong>Browse city evidence</strong></a> · <a href="data-tools.html"><strong>Use the data tools</strong></a> · <a href="open-data.html"><strong>Explore all six evidence layers</strong></a> · <a href="city-workflow.html"><strong>Connect data to the city workflow</strong></a></p>
<h2 id="quick-start">Quick start</h2>
<p>Use a compatible Python environment and install the network-workflow dependencies. The source has been exercised with Python 3.12 and 3.13; see the <a href="getting-started.html">tested profiles and installation guide</a>.</p>
<pre><code class="language-bash">python -m pip install -r requirements.txt
python tools/mnl.py catalog
</code></pre>
<p>Run the self-contained capacity regression from network and demand tables:</p>
<pre><code class="language-bash">python tools/mnl.py run --input app/cases/capacity_zone_probe/input --config app/cases/capacity_zone_probe/case.json --seed-mode auto --seed-k 1 --output results/capacity-demo
python tools/mnl.py verify --run results/capacity-demo
</code></pre>
<p>Open <code>results/capacity-demo/report.html</code>. The reference example allocates 3 units to one route and 7 to the alternative, with objective <strong>27</strong>. This is a labelled regression example, not a city dataset. Use a new output directory for each run.</p>
<p>To inspect the <strong>saved</strong> Central Boston feedback results without rerunning a model, use the included compact component and a new output directory:</p>
<pre><code class="language-bash">python -B examples/boston/run_saved_example.py --data-dir "examples/boston/behavior_feedback_r1_semantic_fix_r1" --output "results/boston_saved_example"
</code></pre>
<p>The command rebuilds a query database from the released CSVs and exports five saved-result queries; it does not acquire sources, fit parameters, run FW/CG or validate predictions. The <a href="https://github.com/scholarhaozheng/mobility-network-lab/blob/main/examples/boston/SAVED_EXAMPLE.md">saved-result guide</a> also explains how to point <code>--data-dir</code> at <code>public_component</code> after extracting the separate full data asset. The trusted code stays beside the wrapper in this checkout.</p>
<h2 id="use-your-own-network">Use your own network</h2>
<p>Declare node/link/demand fields, units and zone-access rules in <code>case.json</code>, then use the same numerical entry point:</p>
<pre><code class="language-bash">python tools/mnl.py validate --input /path/to/network/input --config /path/to/network/case.json
python tools/mnl.py run --input /path/to/network/input --config /path/to/network/case.json --seed-mode auto --seed-k 5 --output results/network-run
python tools/mnl.py verify --run results/network-run
</code></pre>
<p>The current CG profile uses one-minute steps, positive integer travel times, a common departure time, fixed costs, continuous path flows and shared hard arc capacities. <a href="data-contract.html">Read the exact contract</a> before adapting a dataset; this is not a general static user-equilibrium or unrestricted city-scale DTA interface.</p>
<p><strong>Network + demand → route initialization → explicit space–time network → reference LP + Phase-I/II → final pool, flows and duals → independent checks.</strong></p>
<p>The allowed network is independent of the initial route pool. Every column in the last successfully solved pool is exported, including zero-flow columns. Reference agreement and independently established pricing closure are distinct statements.</p>
<h2 id="tools-methods-and-extensions">Tools, methods and extensions</h2>
<p><a href="https://github.com/zephyr-data-specs/GMNS">GMNS</a> supplies the common network vocabulary. <a href="https://github.com/HanZhengIntelliTransport/GMNS_Plus_Dataset">GMNS Plus Dataset</a>, <a href="https://github.com/asu-trans-ai-lab/OSM2GMNS">OSM2GMNS</a>, <a href="https://github.com/asu-trans-ai-lab/grid2demand">grid2demand</a> and <a href="https://github.com/asu-trans-ai-lab/TAPLab">TAPLab</a> are upstream data/tools with their own implementations and licenses. A reference link is not evidence of a bundled executable integration.</p>
<p>The computational release includes <strong>space–time CG</strong>, <strong>static Frank–Wolfe</strong>, the solved <strong>finite-path Boston reference</strong>, corrected <strong>native Diagnostic L3</strong>, accepted <strong>official <code>tap-b</code> Algorithm B</strong> case evidence, bounded <strong>Sioux Lagrangian R2</strong>, and cross-city bounded <strong>ADMM R2_S</strong> source/evidence. <a href="methods.html">The method table</a> states their distinct objectives, instances and accuracy scopes; <code>python -B tools/mcl_results.py list</code> and <code>verify-saved --run &lt;run-id&gt;</code> inspect previously released points without solving. Generalized raw-city automation, broader GPS traces and map matching, coupled primal–dual work and native internal Policy Bush state inspection remain research extensions. <a href="city-workflow.html">City workflow</a> · <a href="methods/origin-based-algorithm-b.html">Algorithm B method</a> · <a href="methods/admm-space-time.html">ADMM R2</a> · <a href="roadmap.html">Roadmap</a></p>
<h2 id="project-layout">Project layout</h2>
<pre><code class="language-text">app/src/gmns_dynamic/   Existing network input and space–time CG engine
app/cases/             Self-contained, labelled regression examples
algorithms/static_fw/  Separate static traffic-assignment baseline
algorithms/origin_based_algorithm_b/  Selected Algorithm B adapter, evaluator and saved evidence
algorithms/finite_path_reference/  Boston 130-path SLSQP source/config
algorithms/path_compression/diagnostic_l3/  Corrected native builder and profiles
algorithms/distributed_assignment/  Earlier bounded Lagrangian R2 and ADMM R1 source/evidence
algorithms/admm_r2/                  Frozen cross-city bounded R2_S source
algorithms/mode_choice_conditional/  Reduced absolute-attribute choice evaluator
examples/boston/assignment_methods_r1/  Saved FW/full-path/native results
examples/sioux-falls/native_l3_r1/  Selected Sioux native results
examples/hong-kong/gmns_pilot_r1/  Bounded public GMNS/data instance and offline checks
launcher/              Saved-output verification
src/mobilitylab/        Authorized metadata tools and supporting adapters
catalog/               Network records, evidence summaries and provenance
schemas/               Explicit input and output contracts
docs/                  City workflow, visual results and project website
tools/                 User commands, documentation build and checks
</code></pre>
<h2 id="contributing-citation-and-licenses">Contributing, citation and licenses</h2>
<p>Contribute a traceable city/network instance, a focused adapter, a verification improvement or a documented method. Keep observed, estimated and synthetic inputs distinct. <a href="https://github.com/scholarhaozheng/mobility-network-lab/blob/main/CONTRIBUTING.md">Contribution guide</a> · <a href="add-a-network.html">Add a network</a> · <a href="citation.html">Citation</a></p>
<p>Original code in the public tree is distributed under <a href="../LICENSE">MIT</a> within the stated authorization scope. Datasets and third-party tools retain their own terms. See <a href="https://github.com/scholarhaozheng/mobility-network-lab/blob/main/DATA_LICENSES.md">data licenses</a>, <a href="https://github.com/scholarhaozheng/mobility-network-lab/blob/main/THIRD_PARTY_NOTICES.md">third-party notices</a> and <a href="data-access.html">data access</a>.</p>

