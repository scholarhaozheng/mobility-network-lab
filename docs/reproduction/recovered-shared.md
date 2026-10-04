# Published city-evidence query

The query uses the two frozen tables already included in the repository. It does not repeat GTFS acquisition or rebuild the global collection.

Use Python 3.11 with `requirements-reproduction-public-controls.txt`. The checked runtime was Python 3.11.4, NumPy 1.24.3 and pandas 1.5.3.

```powershell
py -3.11 -m venv .venv-public-controls
.\.venv-public-controls\Scripts\python.exe -m pip install -r requirements-reproduction-public-controls.txt
.\.venv-public-controls\Scripts\python.exe -B tools/mcl_recovered.py run TOOL-CITY-EVIDENCE-QUERY --output ../results/city-query
.\.venv-public-controls\Scripts\python.exe -B tools/mcl_recovered.py verify TOOL-CITY-EVIDENCE-QUERY --run ../results/city-query
```

The original direct interface remains available:

```text
python -B tools/mcl_data.py query-city --name "Hong Kong" --country CHN --include-relations
```

Verification independently reads the CSV tables and compares the complete city row and both relationships. The test returned one unambiguous city and two complete relationships. See `experiments/recovered/shared.json` for exact input/source hashes and `experiments/recovered/receipts/city-query.json` for the execution receipt.
