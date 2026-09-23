"""Focused public-presentation regression tests; no scientific pipeline execution."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("readme_pages", ROOT / "tools/check_readme_pages.py")
CHECKS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKS)

class FourStepPresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cls.home = (ROOT / "docs/index.html").read_text(encoding="utf-8")
        cls.detail = (ROOT / "docs/datasets/boston-behavior-feedback.html").read_text(encoding="utf-8")

    def test_current_primary_surfaces(self):
        self.assertEqual(CHECKS.presentation_errors(self.readme, self.home, self.detail), [])

    def test_losing_distribution_link_is_detected(self):
        broken = self.readme.replace("boston-behavior-feedback.md#step-2-trip-distribution", "boston-behavior-feedback.md")
        self.assertTrue(CHECKS.presentation_errors(broken, self.home, self.detail))

    def test_losing_mode_result_is_detected(self):
        broken = self.home.replace("step3_mode_response.png", "missing.png")
        self.assertTrue(CHECKS.presentation_errors(self.readme, broken, self.detail))

    def test_losing_gps_evidence_is_detected(self):
        broken = self.home.replace("4.2246%", "unreported")
        self.assertTrue(CHECKS.presentation_errors(self.readme, broken, self.detail))

    def test_homepage_source_is_actually_rendered(self):
        text = (ROOT / "tools/build_site.py").read_text(encoding="utf-8")
        self.assertIn('render_markdown(DOCS / "index.md", repo_url)', text)
        self.assertNotIn("Homepage integration markers changed", text)

if __name__ == "__main__":
    unittest.main()
