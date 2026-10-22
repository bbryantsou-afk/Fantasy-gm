import os,sys,json
from pathlib import Path
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
os.environ['FANTASY_GM_STORAGE_MODE']='session'
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from streamlit.testing.v1 import AppTest
script='''
import sys,copy
sys.path.insert(0,ROOT_PATH)
import streamlit as st
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from ninecat_strategy import load_data
from roster_store import state
from ninecat_model import KEYS
from daily_evidence import player_key
import daily_evidence
daily_evidence.nba_today=lambda day:{'players':{},'updated_at':'','error':'fixture offline','statuses':[]}
today=datetime.now(ZoneInfo('America/New_York')).date()
_,entries=load_data();league=state(entries);team=list(league['teams'])[0]
if 'seeded' not in st.session_state:
 r=copy.deepcopy(league['teams'][team][0]);r.update(slot='C',status='active',daily_stats=dict(dict.fromkeys(KEYS,0.),PTS=8,FGM=4,FGA=6))
 league['daily_rosters']={str(today):{'teams':{team:[r]},'stats_scope':'day','captured_at':datetime.now().astimezone().isoformat()}}
 st.session_state['seeded']=True
from dashboard_overview import render_dashboard
render_dashboard()
'''.replace('ROOT_PATH',repr(str(ROOT)))
a=AppTest.from_string(script,default_timeout=60).run();assert not a.exception,a.exception
assert a.selectbox(key='dash_season').value=='2026-27'
today=datetime.now(ZoneInfo('America/New_York')).date()
assert a.date_input[0].value==today
table=next(t.value for t in a.dataframe if '狀態' in t.value.columns)
assert table.iloc[0]['PTS']==8 and table.iloc[0]['場次']==1
assert not any('資料來源：' in c.value or c.value.startswith('美東 ') for c in a.caption)
a.radio(key='dash_range').set_value('單日').run();assert not a.exception,a.exception
assert next(t.value for t in a.dataframe if '狀態' in t.value.columns).iloc[0]['PTS']==8
print('PASS dashboard defaults to current season/today and shows synced in-progress Fantasy starter production despite NBA outage')
# Touch mode uses static diagrams and an in-flow, collapsible data table.
a.session_state['device_view']='手機版';a.run();assert not a.exception,a.exception
assert any('<svg viewBox=' in m.value for m in a.markdown)
assert not a.get('arrow_vega_lite_chart')
assert any(e.label=='查看圓餅圖數據 · 點開／收起' for e in a.expander)
a.selectbox(key='mobile_pie_category').set_value('PTS').run();assert not a.exception
assert next(t.value for t in a.dataframe if '占比' in t.value.columns).iloc[0]['產量']==8
a.selectbox(key='mobile_pie_category').set_value('FG').run();assert not a.exception
assert next(t.value for t in a.dataframe if '占比' in t.value.columns).iloc[0]['命中／出手']=='4/6'
print('PASS mobile static pies without Vega overlays, collapsible contribution table and FG details')
# A fresh user has NBA data but no Fantasy archive: show a labeled reference MVP.
fresh=script.replace(" league['daily_rosters']={str(today):{'teams':{team:[r]},'stats_scope':'day','captured_at':datetime.now().astimezone().isoformat()}}"," league['daily_rosters']={}")
fresh=fresh.replace('from dashboard_overview import render_dashboard', '''r=league['teams'][team][0]
daily_evidence.nba_today=lambda day:{'players':{'espn:1':{'PLAYER_ID':'espn:1','PLAYER_NAME':r['name'],'TEAM_ABBREVIATION':r['team'],'GP':1,**dict(dict.fromkeys(KEYS,0.),PTS=8,FGM=4,FGA=6)}},'updated_at':datetime.now().astimezone().isoformat(),'error':'','source':'ESPN 即時暫存'}
from dashboard_overview import render_dashboard''')
b=AppTest.from_string(fresh,default_timeout=60).run();assert not b.exception,b.exception
assert any('暫定 MVP · NBA 名單實績' in m.value for m in b.markdown)
assert any('NBA 名單參考模式' in w.value for w in b.warning)
raw=next(t.value for t in b.dataframe if '狀態' in t.value.columns)
assert raw.iloc[0]['PTS']>0 and raw.iloc[0]['狀態']=='NBA實績・先發未確認'
# After a real Fantasy starter snapshot arrives, the provisional scope must disappear.
league=b.session_state['_league'];team=list(league['teams'])[0];r=dict(league['teams'][team][0],slot='C',daily_stats=dict(dict.fromkeys(__import__('ninecat_model').KEYS,0.),PTS=8,FGM=4,FGA=6))
league['daily_rosters']={str(today):{'teams':{team:[r]},'stats_scope':'day','captured_at':datetime.now().astimezone().isoformat()}}
b.session_state['_league']=league;b.run();assert not b.exception,b.exception
assert not any('暫定 MVP · NBA 名單實績' in m.value for m in b.markdown)
print('PASS fresh user reference MVP and automatic switch back to verified Fantasy production')

assert '位置' in next(t.value for t in b.dataframe if '狀態' in t.value.columns).columns
league=b.session_state['_league'];team=list(league['teams'])[0]
injured=league['teams'][team][1]['name'];league['teams'][team][1]['status']='IL'
b.session_state['_league']=league;b.run();assert not b.exception,b.exception
assert any('#### 傷兵／IL' in x.value for x in b.markdown)
assert not any(x.label.startswith('傷兵／IL') for x in b.expander)
assert any(x.label.startswith('其餘球員顏色圖例') for x in b.expander)
assert injured not in next(t.value for t in b.dataframe if '狀態' in t.value.columns)['球員'].tolist()
print('PASS collapsed legend, separate IL table and displayed positions')
