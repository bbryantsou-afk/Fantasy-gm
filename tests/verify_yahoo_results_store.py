import sys,copy
from pathlib import Path
from datetime import date
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from yahoo_matchup_results import import_results,merge_into_store,validate_stored_results
from data_center import week_view
from ninecat_model import KEYS
raw={'week':1,'start':'2026-10-20','end':'2026-10-25','capturedAt':'2026-10-22T20:00:00Z','teams':[{'id':'1','opponent':'2','totals':dict.fromkeys(KEYS,2)},{'id':'2','opponent':'1','totals':dict.fromkeys(KEYS,1)}]}
key,row=import_results(raw,'7',{'7:1':'A','7:2':'B'},{'A','B'});assert key=='2026-10-19'
league={'yahoo_matchups':validate_stored_results({key:row},['A','B'])}
data=merge_into_store({'weeks':{},'days':{}},league,date(2026,10,22))
v=week_view(data,'A',key,date(2026,10,22));assert v['status']=='Yahoo 官方即時比分' and v['a']['PTS']==2
assert not data['weeks'][key]['final']
assert merge_into_store({'weeks':{},'days':{}},league,date(2026,10,26))['weeks'][key]['final']
bad=copy.deepcopy(raw);bad['teams'][0]['totals']['FGM']=5
try:import_results(bad,'7',{'7:1':'A','7:2':'B'},{'A','B'});raise AssertionError('bad totals accepted')
except ValueError:pass
print('PASS official totals mapping, backup roundtrip, first-week alignment and live/final week views')
