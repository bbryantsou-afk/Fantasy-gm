import sys,json,io,zipfile,copy,os
from pathlib import Path
os.environ['FANTASY_GM_STORAGE_MODE']='session'
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from roster_import import read_export,match_rows,build_import
players=[{'PLAYER_ID':1,'PLAYER_NAME':'Jimmy Butler III','TEAM_ABBREVIATION':'GSW'}]
r={'ID':['478.p.4912'],'First Name':['Jimmy'],'Last Name':['Butler III'],'Team ID':['478.l.7.t.14'],'Team Name':['Private Team'],'Position':['IL'],'Eligible Positions':['SF,PF,F,Util,IL']}
raw=json.dumps(r).encode();rows,pool=match_rows(read_export(raw),players,[])
assert rows[0]['id']=='1' and rows[0]['status']=='IL' and rows[0]['eligible']==['SF','PF']
b=io.BytesIO()
with zipfile.ZipFile(b,'w') as z:z.writestr('roster.json',raw)
assert read_export(b.getvalue())==read_export(raw)
league={'teams':{'球隊 01':[],'球隊 02':[]},'capacity':14,'free':['1'],'revision':0}
new=build_import(league,rows,{'478.l.7.t.14':'球隊 01'})
assert new['teams']['球隊 01'][0]['id']=='1' and not new['free'] and not league['teams']['球隊 01']
bad=copy.deepcopy(league);bad['teams']['球隊 02']=[{'id':'1','name':'Jimmy Butler III'}]
try:build_import(bad,rows,{'478.l.7.t.14':'球隊 01'});raise AssertionError('duplicate accepted')
except ValueError:pass
unknown=copy.deepcopy(r);unknown['First Name']=['Unknown'];unknown['Last Name']=['Rookie'];unknown['Position']=['BN']
u,_=match_rows(read_export(json.dumps(unknown).encode()),players,[])
assert u[0]['id'] is None and u[0]['status']=='bench'
print('PASS ZIP/JSON, ID conversion, IL/bench, unknown players, atomic import, duplicate ownership rejection')
