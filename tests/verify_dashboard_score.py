import sys
from pathlib import Path
from datetime import date
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dashboard_matchup import weekly_score
from ninecat_model import KEYS
start,end,today=date(2026,10,19),date(2026,10,25),date(2026,10,22)
league={'matchup_schedule':{'weeks':[{'start':str(start),'end':str(end),'opponents':{'A':'B','B':'A'}}]}}
a=dict.fromkeys(KEYS,10.);b=dict.fromkeys(KEYS,5.)
a.update(FGM=5,FGA=10,FTM=9,FTA=10,TOV=2)
b.update(FGM=8,FGA=10,FTM=7,FTA=10,TOV=4)
with patch('dashboard_matchup.fantasy_period',side_effect=[([a],[],'',''),([b],[],'','')]) as calls:
 view=weekly_score(league,{},'A',start,end,today)
 assert view['score']==(8,1,0),view
 assert calls.call_args_list[0].args[2]==date(2026,10,20)
with patch('dashboard_matchup.fantasy_period',side_effect=[([a],[],'',''),([],[str(today)],'','')]):
 assert weekly_score(league,{},'A',start,end,today)['score'] is None
saved={'weeks':{str(start):{'final':True,'teams':{'A':{'opponent':'B','totals':a},'B':{'opponent':'A','totals':b}}}}}
with patch('dashboard_matchup.fantasy_period',side_effect=AssertionError('final uses stored settlement')):
 assert weekly_score(league,saved,'A',start,end,today)['status']=='已結算'
assert weekly_score({}, {},'A',start,end,today)['score'] is None
print('PASS weekly pairing, nine-category score, reverse TO, FG impact, missing-opponent safety and final settlement')
