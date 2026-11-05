from pathlib import Path
from types import SimpleNamespace
import pytest
from ednaflow_lca.cli import read_feature_table, read_blast, run
DATA=Path(__file__).parent/'data'
def test_duplicate_feature_ids(tmp_path):
 p=tmp_path/'f.tsv';p.write_text('#ID\tS1\nA\t1\nA\t2\n')
 with pytest.raises(ValueError,match='Duplicate feature ID'): read_feature_table(p)
def test_malformed_blast_columns(tmp_path):
 p=tmp_path/'b.tsv';p.write_text('A\tB\t1\n')
 with pytest.raises(ValueError,match='at least 21'): read_blast(p)
def test_excluded_hit(tmp_path):
 x=['N/A']*22;x[0]='ZotuA';x[1]='s';x[2]='11';x[4]='uncultured organism';x[6]='99';x[7]=x[8]=x[9]='10';x[18]='1e-5';x[20]='100'
 b=tmp_path/'b.tsv';b.write_text('\t'.join(x)+'\n')
 a=SimpleNamespace(feature_table=str(DATA/'features.tsv'),blast_results=str(b),taxonomy=str(DATA/'taxonomy.tsv'),query_coverage=100,percent_identity=97,identity_difference=1,assignments=str(tmp_path/'a'),filtered_hits=str(tmp_path/'h'),summary=str(tmp_path/'s'))
 run(a);assert len((tmp_path/'a').read_text().splitlines())==1;assert 'usable_hits\t0' in (tmp_path/'s').read_text()
