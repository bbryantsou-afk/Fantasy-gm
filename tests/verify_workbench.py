import sys,json
from pathlib import Path
from datetime import date,timedelta
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from team_workbench import lineup_week,SLOTS
from ninecat_model import CATS,KEYS
ref={c:{'mean':.5 if c in ('FG','FT') else 1,'std':1} for c in CATS}
weights={c:1 for c in CATS}
def player(i,position):
    return {'PLAYER_ID':i,'PLAYER_NAME':str(i),'team':'AAA','eligible':{position},**{k:1 for k in KEYS}}
day=date(2026,10,20)
pool={str(i):player(i,'C') for i in range(1,7)}
roster=[{'id':str(i),'name':str(i),'status':'active'} for i in range(1,7)]
out=lineup_week(roster,pool,{'AAA':{day}},[day],weights,ref)
assert out['g']==4 and out['tot']['PTS']==4
roster[0]['status']='IL'
out=lineup_week(roster,pool,{'AAA':{day}},[day],weights,ref)
assert '1' not in out['counts']
pool={str(i):player(i,p) for i,p in enumerate(['PG','SG','PG','SF','PF','SF','C','C','C','C','C'],1)}
roster=[{'id':str(i),'name':str(i),'status':'active'} for i in range(1,12)]
assert lineup_week(roster,pool,{'AAA':{day}},[day],weights,ref)['g']==10
from streamlit.testing.v1 import AppTest
from player_hub import save_stars,load_stars,WATCH
previous=WATCH.read_bytes() if WATCH.exists() else None
try:
    save_stars(['1630530','1630530'])
    assert load_stars()==['1630530']
finally:
    if previous is not None: WATCH.write_bytes(previous)
    else: WATCH.unlink(missing_ok=True)
app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=60).run()
with patch('player_hub.player_news',return_value=[]):
    app.sidebar.radio[0].set_value('球員觀察室 Player Watch').run()
    assert not app.exception
    assert len(app.dataframe[0].value)==13
app.sidebar.radio[0].set_value('每週補強 Weekly Planner').run()
assert not app.exception
available=app.multiselect(key='stream_available')
available.set_value(['203999']).run()
assert not app.exception and len(app.dataframe)>0
assert '全隊淨增場次' in app.dataframe[0].value.columns
app.sidebar.radio[0].set_value('交易分析 Trade Lab').run()
assert not app.exception
app.radio(key='trade_review_mode').set_value('手動比較').run()
outbound=app.multiselect(key='trade_send').options
# Use concrete first roster player through underlying session state.
app.session_state['trade_send']=['1641705']
app.session_state['trade_receive']=['203999']
app.run()
assert not app.exception and len(app.metric)==1
app.sidebar.radio[0].set_value('9-Cat Strategy').run()
assert not app.exception and app.multiselect(key='nc_watch_stars') is not None
print('PASS: slot limits, IL exclusion, full lineup, star persistence, watchroom, planner, trade and 9Cat integration')
