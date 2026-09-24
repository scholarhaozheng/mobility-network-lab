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
        prefix=self.text.split('<a id="coverage">')[0]
        for value in ['816,054','route 749','zone 35','203.660','5,091']:
            self.assertNotIn(value,prefix)
    def test_method_coverage_and_gates(self):
        for term in ['17,522','RESOURCE','resource-gated','No Boston CG','130-path','Phase I','Phase II']:
            self.assertIn(term.lower(),self.text.lower())
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
    def test_case_sources_and_tool_entry(self):
        for p in ['docs/cases/sioux-space-time.md','docs/capabilities.md','tools/mcl_assignment.py','tools/mcl_native_l3.py','tools/build_case_presentation.py']:
            self.assertTrue((ROOT/p).is_file(),p)
if __name__=='__main__': unittest.main()
