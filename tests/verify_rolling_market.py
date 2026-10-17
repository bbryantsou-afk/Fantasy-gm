import sys,tempfile,json
from pathlib import Path
from datetime import date,timedelta
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from trade_market import market_model,current_logs
from player_hub import profiles
from ninecat_strategy import load_data
from ninecat_model import CATS,KEYS,baseline,cohort_ids
from trade_packages import near_value_trades
from dashboard_model import draft_roster
s,e=load_data();p=profiles(s['players'],e)
ref=baseline(s['players'],cohort_ids(s['players'],e,'draft'))
v,d,stats=market_model(p,e,ref,asof=date(2026,10,18))
assert all(x['draft_weight']==.3 and x['actual_weight']==0 for x in d.values())
names={x['PLAYER_NAME']:k for k,x in p.items()}
out=[names[n] for n in ('Onyeka Okongwu','Tari Eason')]
flag=[names[n] for n in ('Cooper Flagg','Jalen Williams')]
bam=[names[n] for n in ('Bam Adebayo','Alex Caruso')]
assert all(d[k]['pick'] for k in out+flag)
assert abs(sum(v[k] for k in out)-sum(v[k] for k in bam))<.25
kid=names['Trey Murphy III']
logs=[{'PLAYER_ID':int(kid),'PLAYER_NAME':'Trey Murphy III','TEAM_ABBREVIATION':'NOP',
       'GAME_ID':str(i),'GAME_DATE':str(date(2026,10,20)+timedelta(days=i)),
       **{c:40 if c=='PTS' else 1 for c in KEYS}} for i in range(20)]
later,detail,blended=market_model(p,e,ref,logs,asof=date(2026,12,1))
assert detail[kid]['gp']==20
assert abs(detail[kid]['draft_weight']-.15)<1e-10
assert abs(detail[kid]['historical_weight']-.35)<1e-10
assert abs(detail[kid]['actual_weight']-.5)<1e-10
assert blended[kid]['PTS']==.5*p[kid]['PTS']+.5*40
pre,preinfo,_=market_model(p,e,ref,logs,asof=date(2026,10,18))
assert pre==v
partial,partialinfo,_=market_model(p,e,ref,logs,asof=date(2026,10,24))
assert partialinfo[kid]['gp']==5 and abs(partialinfo[kid]['draft_weight']-.24)<1e-10
unplayed=names['Victor Wembanyama']
assert detail[unplayed]['draft_weight']==.3
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(dir=root/'backups') as temp,patch('trade_market.CACHE',Path(temp)/'logs.json'):
    current_logs.clear()
    with patch('nba_api.stats.endpoints.leaguegamelog.LeagueGameLog',side_effect=RuntimeError('offline')) as api:
        assert not current_logs('2026-10-18')[0]
        api.assert_not_called()
        assert not current_logs('2026-10-21')[0]
        Path(temp,'logs.json').write_text(json.dumps({'games':logs[:1],'fetched_at':'earlier'}))
        current_logs.clear()
        cached,message,_=current_logs('2026-10-21')
        assert len(cached)==1 and '快取' in message
current_logs.clear()
print('PASS: preseason 30/70, real-GP decay, no future leakage, no-game/no-data retention, real-stat blending, screenshot packages separated, cache fallback.')
