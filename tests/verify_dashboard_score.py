import sys,copy
from pathlib import Path
from datetime import date
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dashboard_matchup import weekly_score
start,end,today=date(2026,10,19),date(2026,10,25),date(2026,10,24)
league={'matchup_schedule':{'weeks':[{'start':str(start),'end':str(end),'opponents':{'A':'B','B':'A'}}]}}
# Deliberately conflicting totals must never affect Yahoo's displayed 5:4.
record={'source':'Yahoo 官方對局總表','updated_at':'2026-10-24T17:00:00Z','teams':{'A':{'opponent':'B','score':5,'totals':{}},'B':{'opponent':'A','score':4,'totals':{}}}}
league['yahoo_matchups']={str(start):record}
assert weekly_score(league,{},'A',start,end,today,{'players':{'bad':{}}})['score']==(5,4,0)
assert weekly_score(league,{},'B',start,end,today)['score']==(4,5,0)
old=copy.deepcopy(record);old['updated_at']='2026-10-23T00:00:00Z';old['teams']['A']['score']=4;old['teams']['B']['score']=5
assert weekly_score(league,{'weeks':{str(start):old}},'A',start,end,today)['score']==(5,4,0)
del league['yahoo_matchups'][str(start)]['teams']['A']['score']
assert weekly_score(league,{},'A',start,end,today)['score'] is None
assert weekly_score({}, {'weeks':{str(start):{'final':True,'teams':{}}}},'A',start,end,today)['score'] is None
print('PASS Yahoo displayed score only, correct orientation, newest official record and no computed fallback')

from yahoo_matchup_results import import_results,validate_stored_results
from ninecat_model import KEYS
zero=dict.fromkeys(KEYS,0)
raw={'week':1,'start':'2026-10-20','end':'2026-10-25','capturedAt':'2026-10-25T00:00:00Z','teams':[{'id':'1','opponent':'2','totals':zero,'score':5},{'id':'2','opponent':'1','totals':zero,'score':4}]}
k,r=import_results(raw,'7',{'7:1':'A','7:2':'B'},{'A','B'})
clean=validate_stored_results({k:r},{'A','B'})
assert clean[k]['teams']['A']['score']==5
assert clean[k]['teams']['B']['score']==4
print('PASS official displayed score survives import and stored-profile validation')
