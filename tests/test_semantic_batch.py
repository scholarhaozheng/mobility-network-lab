"""Check that the multi-egress adapter retains the locked transit route semantics."""
import ast
import dataclasses
import math
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/scalable"))


class SemanticBatch(unittest.TestCase):
    def test_exact_scan_split_and_multiegress_results(self):
        import pandas as pd
        from semantic_transit import Connection,TransferPolicy,transit_route
        from semantic_transit_batch import transit_route_many
        original=ast.parse((ROOT/"tools/scalable/semantic_transit.py").read_text(encoding="utf-8"))
        split_module=ast.parse((ROOT/"tools/scalable/semantic_transit_batch.py").read_text(encoding="utf-8"))
        def body(tree,name):
            return next(n.body for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
        old=body(original,"transit_route")
        cut=next(i for i,n in enumerate(old) if isinstance(n,ast.If) and ast.unparse(n.test)=="not access or not egress")
        scan=body(split_module,"build_search")
        finish=body(split_module,"finish_search")
        dump=lambda seq:[ast.dump(x,include_attributes=False) for x in seq]
        self.assertEqual(dump(old[1:cut]),dump(scan[:-1]))
        self.assertEqual(dump(old[cut:]),dump(finish))
        self.assertFalse(any(isinstance(n,ast.Name) and n.id in {"egress","fare_policy"}
                             for part in old[1:cut] for n in ast.walk(part)))
        stops=pd.DataFrame({"stop_id":["A","B","C"],"parent_station":[None]*3,"location_type":["0"]*3})
        transfers=pd.DataFrame([],columns=["from_stop_id","to_stop_id","transfer_type","min_transfer_time",
                                          "min_walk_time","from_trip_id","to_trip_id"])
        policy=TransferPolicy.build(stops,transfers,None)
        connection=Connection(from_stop="A",to_stop="B",dep=60,arr=180,trip_id="bus",route_id="bus",
            route_type="3",network_id="local_bus",direction_id="0",service_id="weekday",block_id=None,
            from_seq=1,to_seq=2,pickup_allowed=True,dropoff_allowed=True,pickup_type="0",drop_off_type="0",
            overlay_parameter_id=None)
        access={"A":0.0,"B":0.0}
        egress={"B":{"B":0.0},"C":{"C":0.0},"empty":{}}
        many=transit_route_many(0,[connection],access,egress,policy,None,search_end=1000)
        def normalized(value):
            if dataclasses.is_dataclass(value):return normalized(dataclasses.asdict(value))
            if isinstance(value,float) and math.isnan(value):return "NaN"
            if isinstance(value,dict):return {k:normalized(v) for k,v in value.items()}
            if isinstance(value,list):return [normalized(v) for v in value]
            return value
        for key,target in egress.items():
            self.assertEqual(normalized(transit_route(0,[connection],access,target,policy,None,search_end=1000)),
                             normalized(many[key]))


if __name__=="__main__":unittest.main()
