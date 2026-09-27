"""No-solve checks for the framework-first/case-specific public narrative."""
from pathlib import Path
import re
import unittest
ROOT=Path(__file__).resolve().parents[1]
class PresentationR3(unittest.TestCase):
    def setUp(self): self.text=(ROOT/'README.md').read_text(encoding='utf-8')
    def test_order(self):
        ids=['framework','coverage','boston','sioux-falls','run-your-input']
        positions=[self.text.index('id="'+i+'"') for i in ids]
        self.assertEqual(positions,sorted(positions))
    def test_generic_prefix_is_not_a_boston_result(self):
        prefix=self.text.split('<a id="cg-experiments">')[0]
        for value in ['816,054','route 749','zone 35','203.660','5,091']:
            self.assertNotIn(value,prefix)
    def test_method_coverage_and_gates(self):
        for term in ['17,522','RESOURCE','resource-gated','130-path','Phase I','Phase II',
                     'Boston and Hong Kong each have a distinct accepted bounded ten-demand pilot',
                     'independent pricing closure', 'None is a citywide CG']:
            self.assertIn(term.lower(),self.text.lower())
    def test_current_bounded_additions_keep_contracts_distinct(self):
        for term in ['Case 03', 'assignment_ready=false', '0.0746%', '0.3177%',
                     '6.30e-6', '7.16e-6', '6.68e-6', '1.1002%',
                     'task-local TAPLab-compatible lossless adapter']:
            self.assertIn(term.lower(), self.text.lower())
    def test_protected_gmns_remains_visible(self):
        for name in ['gmns_connected_layers.png','gps_to_gmns_evidence.png','tools/gmns/trace_gmns_figure.py']:
            self.assertIn(name,self.text)
    def test_comparison_not_five_stacked_images(self):
        self.assertIn('presentation_r3/boston_method_comparison.png',self.text)
        self.assertNotRegex(self.text,r'<img[^>]+assignment_methods_r1/boston_abs_planned_')
        for n in ['fw_flow','l3_rank26_flow','l3_rank52_flow','l3_rank26_minus_fw','l3_rank52_minus_fw']:
            self.assertIn('boston_abs_planned_'+n+'.png',self.text)
    def test_sioux_new_phase_figures_are_linked(self):
        for n in ['sioux_space_time_construction.png','sioux_capacity_exchange.png','sioux_falls_200od_phase_i_academic.png','sioux_falls_250od_phase_i_academic.png']:
            self.assertIn(n,self.text)
    def test_algorithm_b_flow_pair_and_other_source_figures(self):
        section=self.text.split('### Static user equilibrium / official `tap-b` Algorithm B',1)[1].split('## 02 / What each case demonstrates',1)[0]
        self.assertNotRegex(section,r'<img[^>]+algorithm_b_cross_city_overview.png')
        for stem in ('sioux_convergence','boston_b1_convergence','sioux_origin_flow',
                     'boston_b1_origin_flow','sioux_verification','boston_b1_verification'):
            path=f'docs/assets/algorithm_b_r21/source_panels/{stem}.svg'
            self.assertRegex(section,rf'(?m)^!\[[^\]]+\]\({re.escape(path)}\)$')
        flow=section.split('#### Physical-link flow against same-problem FW',1)[1].split('#### Selected-origin reconstructed flow',1)[0]
        for stem in ('sioux','boston_b1'):
            self.assertIn(f'docs/assets/algorithm_b_r21/presentation/{stem}_fw_flow_compact.svg',flow)
            self.assertIn(f'docs/assets/algorithm_b_r21/source_panels/{stem}_fw_flow.svg',flow)
        self.assertEqual(flow.count('<td width="50%">'),2)
        self.assertIn('docs/assets/algorithm_b_r21/algorithm_b_cross_city_overview.png',section)
    def test_requested_cg_pairs_and_boston_construction_heading(self):
        self.assertIn('#### Boston / From the physical network to time-indexed columns',self.text)
        boston=self.text.split('### Boston / Bounded finite space–time CG pilot',1)[1].split('<a id="boston-admm-readme"></a>',1)[0]
        paired=boston.split('#### Final physical-link movement flow and independent pricing closure',1)[1].split('| Shared CG stage |',1)[0]
        self.assertEqual(paired.count('<td width="50%">'),2)
        self.assertIn('boston_cg_final_physical_link_flow.png',paired)
        self.assertIn('boston_pricing_closure_by_demand.png',paired)
        for heading in ('Phase I restores feasibility','Phase II improves the real-path objective',
                        'Final physical-link movement flow and validation'):
            section=self.text.split('### Sioux Falls / '+heading,1)[1].split('### Sioux Falls /',1)[0]
            self.assertEqual(section.count('<td width="50%">'),2,heading)
    def test_case_sources_and_tool_entry(self):
        for p in ['docs/cases/sioux-space-time.md','docs/capabilities.md','tools/mcl_assignment.py','tools/mcl_native_l3.py','tools/build_case_presentation.py']:
            self.assertTrue((ROOT/p).is_file(),p)
if __name__=='__main__': unittest.main()
