from pathlib import Path
from types import SimpleNamespace
from ednaflow_lca.cli import run

def test_assignment(tmp_path):
 d=Path(__file__).parent/'data'
 a=SimpleNamespace(feature_table=str(d/'features.tsv'),blast_results=str(d/'blast.tsv'),taxonomy=str(d/'taxonomy.tsv'),query_coverage=100,percent_identity=97,identity_difference=1,assignments=str(tmp_path/'a.tsv'),filtered_hits=str(tmp_path/'h.tsv'),summary=str(tmp_path/'s.tsv'))
 run(a)
 lines=(tmp_path/'a.tsv').read_text().splitlines()
 assert len(lines)==2
 assert 'ZotuA' in lines[1]
 assert lines[1].startswith('Eukaryota\tChordata\tActinopteri\tPerciformes\tFamA\tGenusA\tdropped')
