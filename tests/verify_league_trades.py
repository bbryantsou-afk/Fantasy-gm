import sys,json,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from player_hub import profiles
from ninecat_strategy import load_data
from dashboard_model import draft_roster
from ninecat_model import CATS,cohort_ids,baseline
from trade_packages import near_value_trades
from trade_package_ui import select_quality
s,e=load_data();pool=profiles(s['players'],e);teams=list(dict.fromkeys(r['fantasyTeam'] for r in e))
a=draft_roster(e,teams[0]);b=draft_roster(e,teams[1])
aid=next(str(r['id']) for r in a if str(r.get('id')) in pool)
bid=next(str(r['id']) for r in b if str(r.get('id')) in pool)
ref=baseline(s['players'],cohort_ids(s['players'],e,'draft'));w={c:1 for c in CATS}
r=near_value_trades(a,b,pool,ref,w,w,my_protected=[aid],their_protected=[bid],both_improve=False)
assert r and all(aid not in x['send'] and bid not in x['receive'] for x in r)
try:
    near_value_trades(a,b,pool,ref,w,w,n_receive=3,my_release=[aid],my_protected=[aid])
    raise AssertionError('Protected release accepted')
except ValueError: pass
from streamlit.testing.v1 import AppTest
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(dir=root/'backups') as temp,patch('trade_package_ui.PREFS',Path(temp)/'prefs.json'):
    app=AppTest.from_file(str(root/'app.py'),default_timeout=60).run()
    app.sidebar.radio[0].set_value('交易分析 Trade Lab').run()
    app.selectbox(key='auto_partner').set_value('全部球隊').run()
    assert not app.exception
    own=next(m for m in app.multiselect if m.key and m.key.startswith('auto_protect_my_'))
    own.set_value([aid]).run()
    opponents=[m for m in app.multiselect if m.key and m.key.startswith('auto_protect_opp_')]
    assert len(opponents)==13
    opp=next(m for m in opponents if bid in [str(x) for x in app.session_state[m.key]] or m.label==teams[1])
    opp.set_value([bid]).run()
    app.button(key='auto_find').click().run()
    assert not app.exception
    saved=app.session_state['auto_packages']
    results=saved['results']
    assert 0<len(results)<=5 and len({x['partner'] for x in results})>1
    assert all(x['my_gain']>0 and x['their_gain']>0 and x['my_focus']>0 and x['their_focus']>0 for x in results)
    assert all(aid not in x['send'] for x in results)
    assert all(bid not in x['receive'] for x in results if x['partner']==teams[1])
    assert all(sum(y['partner']==x['partner'] for y in results)<=2 for x in results)
    prefs=json.loads((Path(temp)/'prefs.json').read_text())
    assert aid in prefs[own.key] and bid in prefs[opp.key]
    app.selectbox(key='auto_partner').set_value(teams[1]).run()
    assert not app.exception
    match=next(m for m in app.multiselect if m.label==teams[1])
    assert match.value==[bid]
print('PASS: protected trade/release, 13 opponents independently searched, persistent per-team protections, five diverse two-sided ideas, single-team reuse.')
