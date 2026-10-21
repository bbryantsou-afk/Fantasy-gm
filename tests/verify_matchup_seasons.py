import ast, json, subprocess, tempfile, time
from pathlib import Path
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT))
source=(ROOT/'matchup_simulator_v15.py').read_text()
assert 'chronicaria' not in source and 'Encyclopedia' not in source
script="""
import streamlit as st
from nba_api.stats.endpoints import leaguedashplayerstats, scoreboardv2

def forbidden(*args,**kwargs):
    raise AssertionError('unexpected network in default / historical mode')
leaguedashplayerstats.LeagueDashPlayerStats=forbidden
scoreboardv2.ScoreboardV2=forbidden

def fake_component(*args,**kwargs):
    def capture(**values):
        st.session_state['captured']=values['data']
        return {}
    return capture
st.components.v2.component=fake_component
from matchup_simulator_v15 import render_matchup_simulator
render_matchup_simulator()
"""
start=time.monotonic()
a=AppTest.from_string(script,default_timeout=30).run()
assert not a.exception,a.exception
assert len(a.selectbox(key='sim_my_team').options)==14
assert a.session_state['captured']['players']['my'][0]['profiles']['season']['PTS']>0
a.selectbox(key='sim_opp_team').set_value('球隊 14').run()
assert not a.exception
assert len(a.session_state['captured']['players']['opp'])==13
a.selectbox(key='sim_season').set_value('2025-26').run()
assert not a.exception,a.exception
d=a.session_state['captured']
assert d['historical'] and d['week_dates'][1]=='2025-10-21'
logs=json.loads((ROOT/'ninecat_assets/game_logs_2025_26.json').read_text())
for r in logs:
    if r['GAME_DATE'] in d['week_dates']:
        actual=d['actual_by_player'][r['PLAYER_ID']][r['GAME_DATE']]
        assert actual['PTS']==r['PTS'] and actual['TO']==r['TOV']
# Compile the shipped component and run its actual dailyStats resolver.
tree=ast.parse(source)
js=next(n.value.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='JS' for x in n.targets))
node='/Users/zoupeien/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
with tempfile.TemporaryDirectory() as temp:
    path=Path(temp)/'component.mjs';path.write_text(js)
    subprocess.run([node,'--check',str(path)],check=True)
    resolver=js[js.index('      const dailyKey='):js.index('      const getPlayer =')]
    test="""
const assert = require('node:assert/strict');
const data={today:'2026-10-22',actual_by_player:{1:{'2026-10-20':{PTS:42}}},final_teams:{'2026-10-22':['SAS']}};
const weekDates=['2026-10-20','2026-10-22','2026-10-23'];
const profileLabels={season:'season',manual:'manual'};
const dailyChoices={my:{'x::0':{profile:'manual',custom:{PTS:999}}}};
const p={id:'x',nba_id:1,team:'SAS',profiles:{season:{PTS:20}},actual_by_day:{'2026-10-20':{PTS:999}}};
"""+resolver+"""
assert.equal(dailyStats(p,'my',0).PTS,42); // server actual overrides manual / restored data
assert.deepEqual(dailyStats(p,'my',1),{}); // final but missing log must not become forecast
assert.equal(dailyStats(p,'my',2).PTS,20); // future still uses profile
const pending={...p,id:'pending',nba_id:2,team:'DET'};
data.scheduled_teams=['DET'];
assert.equal(dailyStats(pending,'my',1).PTS,20); // today's confirmed unstarted game uses last season
assert.deepEqual(dailyStats(pending,'my',0),{}); // yesterday remains observed-only
data.actual_by_player[2]={'2026-10-22':{PTS:7}};
assert.equal(dailyStats(pending,'my',1).PTS,7); // real stats always override the forecast
delete data.actual_by_player[2];data.scheduled_teams=[];
assert.deepEqual(dailyStats(pending,'my',1),{}); // missing/started game never silently predicts
console.log('PASS JS real-game locking, scheduled-today projection and missing-final safety');
"""
    subprocess.run([node,'-e',test],check=True)
print('PASS 14 teams, season switching, historical actuals, offline default:',round(time.monotonic()-start,2),'seconds')
