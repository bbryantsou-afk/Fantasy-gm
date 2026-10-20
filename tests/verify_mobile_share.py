import os,sys,json
from pathlib import Path
os.environ['FANTASY_GM_STORAGE_MODE']='session'
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from streamlit.testing.v1 import AppTest
from mobile_share import share_root,write_json,create_share
app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=60).run()
app.sidebar.radio[0].set_value('⚙️ 設定').run()
assert not any(b.label=='建立手機共用連結' for b in app.button)
token=create_share(app.session_state['_league'],{'weeks':{},'days':{}})
app.query_params['mobile']=token;app.run()
assert not app.exception,app.exception
token=app.session_state['_mobile_share_token'];root=share_root(token)
assert root and {p.name for p in root.iterdir()}=={'access.json','league_rosters.json','league_results.json'}
phone=AppTest.from_file(str(ROOT/'app.py'),default_timeout=60)
phone.query_params['mobile']=token;phone.run();assert not phone.exception,phone.exception
assert phone.session_state['_league']==app.session_state['_league']
roster=json.loads((root/'league_rosters.json').read_text());team=next(iter(roster['teams']));roster['team_names']={team:'Shared Device Team'}
write_json(root/'league_rosters.json',roster)
phone.run();app.run()
assert phone.session_state['_league']['team_names'][team]=='Shared Device Team'
assert app.session_state['_league']['team_names'][team]=='Shared Device Team'
assert share_root('bad') is None and share_root('a'*64) is None
write_json(root/'access.json',{'expires':1});assert share_root(token) is not None
write_json(root/'access.json',{'revoked':True});assert share_root(token) is None
phone.run();assert any('已停用' in e.value for e in phone.error)
print('PASS legacy-link recovery and revocation; new link creation is absent from settings')
