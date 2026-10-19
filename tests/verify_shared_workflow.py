import os,sys,json,copy
from pathlib import Path
from unittest.mock import patch
os.environ['FANTASY_GM_STORAGE_MODE']='session'
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from streamlit.testing.v1 import AppTest
from ninecat_model import CATS
from team_workbench import matchup_score
# Turnovers: lower is always better, with other categories unchanged.
weights={c:float(c=='TOV') for c in CATS};scale={c:1 for c in CATS}
a={'tot':{c:0 for c in ['PTS','REB','AST','STL','BLK','FG3M','TOV','FGM','FGA','FTM','FTA']}}
b=copy.deepcopy(a);a['tot']['TOV']=2;b['tot']['TOV']=5
assert matchup_score(a,b,weights,scale)[0]>50
assert matchup_score(b,a,weights,scale)[0]<50
app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=90).run()
assert not app.exception,app.exception
assert app.sidebar.radio[0].options[-1]=='⚙️ 設定'
assert 'Yahoo API 設定' not in app.sidebar.radio[0].options
assert not any(x.label=='視覺風格' for x in app.selectbox)
league=copy.deepcopy(app.session_state['_league']);team='球隊 01'
# A valid private edit of the shared roster, including IL and a confirmed free player.
league['teams'][team][0]['status']='IL'
removed=league['teams'][team].pop()
league['free']=[str(removed['id'])]
app.session_state['_league']=league
with patch('player_hub.player_news',side_effect=AssertionError('news should be lazy')):
 app.sidebar.radio[0].set_value('球員觀察室 Player Watch').run()
 assert not app.exception,app.exception
 assert len([b for b in app.button if b.label.startswith('⋯ 展開')])==12
 app.radio(key='watch_scope').set_value('星號追蹤').run();assert not app.exception
app.sidebar.radio[0].set_value('每週補強 Weekly Planner').run()
assert not app.exception,app.exception
available=app.multiselect(key='stream_available')
# Other teams' owned players cannot be added (Jokic belongs to team 02).
assert 'Nikola Jokić' not in available.options
app.radio(key='stream_mode').set_value('長期適配').run()
assert not app.exception
assert len([b for b in app.button if b.key and b.key.startswith('stream_apply_')])<=3
app.sidebar.radio[0].set_value('交易分析 Trade Lab').run();assert not app.exception
app.sidebar.radio[0].set_value('9-Cat Strategy').run();assert not app.exception
assert len(app.session_state['nc_roster'])==12
assert app.session_state['nc_roster'][0]['status']=='IL'
app.sidebar.radio[0].set_value('Matchup Simulator Lite').run();assert not app.exception
app.sidebar.radio[0].set_value('⚙️ 設定').run();assert not app.exception
assert app.selectbox(key='_theme_picker')
app.selectbox(key='_theme_picker').set_value('黑色鏡面').run();assert not app.exception
assert app.session_state['visual_theme']=='黑色鏡面'
from league_settings import validate_backup
valid=validate_backup(league,league['teams']);assert valid['capacity']==14
bad=copy.deepcopy(league);bad['teams']['球隊 02'].append(copy.deepcopy(bad['teams'][team][0]))
try:validate_backup(bad,league['teams']);raise AssertionError('duplicate ownership accepted')
except ValueError:pass
print('PASS shared roster/IL, lazy avatar cards, owned-player exclusion, both planner modes, settings and backup validation')
