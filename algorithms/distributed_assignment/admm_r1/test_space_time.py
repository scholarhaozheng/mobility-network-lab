import unittest
from pathlib import Path

import numpy as np

from lagrangian import recover
from admm import project_capacity, local_qp
from space_time_contract import load, shortest_path

ROOT=Path(__file__).resolve().parent/"fixtures"/"C1"


class SpaceTimeTests(unittest.TestCase):
    def setUp(self):self.p=load(ROOT/"dynamic_arc.csv",ROOT/"dynamic_demand.csv")

    def test_own_connectors_only(self):
        a=self.p["ids"].index("source_K1")
        self.assertTrue(self.p["allowed"][0,a]);self.assertFalse(self.p["allowed"][1,a])

    def test_dual_sign_and_recovery(self):
        p=self.p; path=shortest_path(p,0,p["cost"])[1]
        self.assertIn(p["ids"].index("path_a"),path)
        pools=[{shortest_path(p,k,p["cost"])[1],shortest_path(p,k,p["cost"]+np.array([0,0,3,0,0,0,0,0]))[1]} for k in range(2)]
        result=recover(p,pools)
        self.assertTrue(result["feasible"]);self.assertAlmostEqual(result["objective"],8.0)
        price=np.zeros(len(p["ids"]));price[p["ids"].index("path_a")]=2
        dual=sum(c["volume"]*shortest_path(p,k,p["cost"]+price)[0] for k,c in enumerate(p["commodities"]))-float(np.dot(price,p["cap"]))
        self.assertLessEqual(dual,8.0+1e-8)

    def test_admm_capacity_projection(self):
        p=self.p
        values=np.zeros((2,len(p["ids"])));a=p["ids"].index("path_a")
        values[:,a]=[2,2]
        z=project_capacity(values,p["cap"],p["allowed"])
        self.assertAlmostEqual(z[:,a].sum(),2.0)
        self.assertAlmostEqual(z[0,a],1.0)
        self.assertEqual(z[1,p["ids"].index("source_K1")],0.0)

    def test_admm_local_qp_conservation(self):
        p=self.p;rho=0.001
        q=np.zeros(len(p["ids"]))
        x,_,residual,_,_,_=local_qp(p,0,q,rho,np.zeros(len(p["nodes"])),500)
        self.assertLess(residual,1e-5)
        self.assertAlmostEqual(x[p["ids"].index("source_K1")],2.0,places=5)


if __name__=="__main__":unittest.main()
