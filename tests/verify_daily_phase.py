"""Pregame and no-game dates are not missing Fantasy production."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datetime import date
from daily_evidence import fantasy_period
from ninecat_model import KEYS
league={'daily_rosters':{}}
day=date(2026,10,21)
for phase in ['pregame','no_games']:
 records,missing,source,stamp=fantasy_period(league,'A',day,day,day,{'by_date':{str(day):{'phase':phase,'players':{}}}})
 assert records==[] and missing==[]
records,missing,_,_=fantasy_period(league,'A',day,day,day,{'by_date':{str(day):{'phase':'started','players':{}}}})
assert missing==[str(day)]
records,missing,_,_=fantasy_period(league,'A',day,day,day,{'by_date':{str(day):{'players':{},'error':'offline'}}})
assert missing==[str(day)]
# Existing confirmed production from yesterday survives today's pregame state.
previous=date(2026,10,20)
league['daily_rosters'][str(previous)]={'captured_at':'2026-10-21T04:00:00Z','stats_scope':'day','teams':{'A':[{'id':'1','name':'Player','team':'SAS','slot':'C','daily_stats':dict.fromkeys(KEYS,1)}]}}
records,missing,_,_=fantasy_period(league,'A',previous,day,day,{'by_date':{str(day):{'phase':'pregame','players':{}}}})
assert len(records)==1 and records[0]['GP']==1 and not missing
print('PASS pregame/no-games do not raise false missing warnings; started/unknown remain flagged; prior actuals retained')
