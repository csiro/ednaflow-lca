from ednaflow_lca.cli import lca
def test_species_conflict():
 a=('Eukaryota','Chordata','Actinopteri','Perciformes','Fam','Gen','Sp1');b=a[:-1]+('Sp2',)
 assert lca([a,b])[-1]=='dropped'
def test_family_conflict_drops_lower():
 a=('Eukaryota','Chordata','Actinopteri','Perciformes','Fam1','Gen1','Sp1');b=('Eukaryota','Chordata','Actinopteri','Perciformes','Fam2','Gen2','Sp2')
 assert lca([a,b])[4:]==('dropped','dropped','dropped')
