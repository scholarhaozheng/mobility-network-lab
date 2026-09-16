"""Focused, solver-free checks for the public entry point and catalog."""
from pathlib import Path
import json
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
ENTRY=ROOT/'tools/mnl.py'

class PublicEntryTests(unittest.TestCase):
    def command(self,*args):
        return subprocess.run([sys.executable,'-B',str(ENTRY),*args],cwd=ROOT,capture_output=True,text=True,timeout=30)
    def test_catalog_paths(self):
        for item in json.loads((ROOT/'catalog/datasets.json').read_text())['datasets']:
            self.assertTrue((ROOT/item['data_page']).exists())
            if item['access']=='bundled-input':
                self.assertTrue((ROOT/item['input']).is_dir())
                self.assertTrue((ROOT/item['config']).is_file())
    def test_catalog_command(self):
        result=self.command('catalog')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('sioux-200od',result.stdout)
    def test_input_validation(self):
        result=self.command('validate','--input','app/cases/capacity_zone_probe/input','--config','app/cases/capacity_zone_probe/case.json')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'],'PASS')
    def test_auto_does_not_accept_supplied_file(self):
        result=self.command('run','--input','app/cases/capacity_zone_probe/input','--config','app/cases/capacity_zone_probe/case.json','--seed-mode','auto','--seeds','unused.csv','--output','unused-output')
        self.assertEqual(result.returncode,2)
        self.assertFalse((ROOT/'unused-output').exists())
    def test_supplied_requires_file(self):
        result=self.command('run','--input','app/cases/capacity_zone_probe/input','--config','app/cases/capacity_zone_probe/case.json','--seed-mode','supplied','--output','unused-output')
        self.assertEqual(result.returncode,2)
        self.assertFalse((ROOT/'unused-output').exists())

if __name__=='__main__':unittest.main()
