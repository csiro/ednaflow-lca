from pathlib import Path
from types import SimpleNamespace
import csv
from ednaflow_lca.cli import run

def rows(path):
 with open(path,encoding='utf-8') as f:
  r=csv.reader(f,delimiter='\t'); next(r); return {x[7]:x for x in r}

def test_full_upstream_assignment_parity(tmp_path):
 d=Path(__file__).parent/'parity'
 a=SimpleNamespace(feature_table=str(d/'curated_zotuTable_2test_LCAscript.tab'),blast_results=str(d/'blastResult_2test_LCAscript.tab'),taxonomy=str(d/'rankedlineage_subset_2026-11-05.dmp'),query_coverage=100,percent_identity=97,identity_difference=1,assignments=str(tmp_path/'a.tsv'),filtered_hits=str(tmp_path/'h.tsv'),summary=str(tmp_path/'s.tsv'))
 run(a)
 assert rows(tmp_path/'a.tsv') == rows(d/'upstream_expected.tsv')
