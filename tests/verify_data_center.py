import os,sys,copy
from pathlib import Path
from datetime import date
from unittest.mock import patch
os.environ['FANTASY_GM_STORAGE_MODE']='session'
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from data_center import checked_week,category_result,standings,lineup_totals,fetch_live
from ninecat_model import KEYS
from streamlit.testing.v1 import AppTest
zero=dict.fromkeys(KEYS,0.)
a=dict(zero,PTS=10,FGM=5,FGA=10,FTM=2,FTA=2,TOV=1)
b=dict(zero,PTS=5,FGM=2,FGA=10,FTM=1,FTA=2,TOV=3)
rows=checked_week([{'team':'A','opponent':'B',**a},{'team':'B','opponent':'A',**b}],['A','B'])
assert category_result(a,b).count(1)==4
scores=standings({'week':{'final':True,'teams':rows},'partial':{'final':False,'teams':rows}},['A','B'])
assert scores[0]['W']==4 and scores[0]['T']==5 and scores[0]['weeks']==1
try:checked_week([{'team':'A','opponent':'A',**a},{'team':'B','opponent':'A',**b}],['A','B']);raise AssertionError()
except ValueError:pass
bad=dict(a,FGM=11)
try:checked_week([{'team':'A','opponent':'B',**bad},{'team':'B','opponent':'A',**b}],['A','B']);raise AssertionError()
except ValueError:pass
rosters={'A':[{'id':'1','name':'Starter','slot':'PG'},{'id':'2','name':'Bench','slot':'BN'},{'id':'3','name':'IL','slot':'IL'}]}
assert lineup_totals(rosters,{'1':a,'2':a,'3':a})[0]['A']['PTS']==10
class Response:
 def raise_for_status(self):pass
 def json(self):return {'scoreboard':{'gameDate':'2026-10-20','games':[]}}
with patch('data_center.requests.get',return_value=Response()):
 assert fetch_live(date(2026,10,20))==({},[])
 try:fetch_live(date(2026,10,19));raise AssertionError()
 except ValueError:pass
app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=60).run()
app.sidebar.radio[0].set_value('Data Source 資料中心').run()
assert not app.exception,app.exception
assert [t.label for t in app.tabs]==['選秀結果','原始數據與備份']
assert any(x.label=='儲存此週結果' for x in app.button)
assert app.sidebar.radio[0].options[-2:]==['Data Source 資料中心','⚙️ 設定']
print('PASS nine-category W/L/T, final-only standings, symmetric opponents, shooting validation, starter-only live totals, date guard and all data-center tabs')

from data_center import week_view
case={'weeks':{'2026-10-19':{'teams':rows,'final':False}},'days':{}}
assert week_view(case,'A','2026-10-19',date(2026,10,20))['opponent']=='B'
assert week_view(case,'A','2026-10-19',date(2026,10,18))['a'] is None
assert week_view({'weeks':{},'days':{}},'A','2026-10-19',date(2026,10,20))['opponent'] is None
case['weeks']['2026-10-19']['final']=True
assert week_view(case,'A','2026-10-19',date(2026,10,27))['status']=='已結算'
app.sidebar.radio[0].set_value('比賽戰況').run();assert not app.exception,app.exception
assert any(x.label=='查看隊伍' for x in app.selectbox)
assert any('聯盟總積分' in x.value for x in app.markdown)
print('PASS independent matchup page, no invented opponents, pregame placeholders and settled-week view')
