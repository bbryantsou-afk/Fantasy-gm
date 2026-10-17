import sys
from pathlib import Path
from datetime import date
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from player_hub import profiles
from ninecat_strategy import load_data
from ninecat_model import CATS,baseline,cohort_ids
from trade_market import market_model
from trade_packages import near_value_trades
s,e=load_data();pool=profiles(s['players'],e);ref=baseline(s['players'],cohort_ids(s['players'],e,'draft'))
prices,details,_=market_model(pool,e,ref,asof=date(2026,10,18))
assert all(abs(d['draft_weight']-.3)<1e-8 and abs(d['historical_weight']-.7)<1e-8 for d in details.values())
by_name={p['PLAYER_NAME']:k for k,p in pool.items()}
roster=lambda names:[{'id':by_name[n],'name':n,'status':'active'} for n in names]
a=roster(['Onyeka Okongwu','Tari Eason']);b=roster(['Cooper Flagg','Jalen Williams'])
w={c:1 for c in CATS};picks={k:d['pick'] for k,d in details.items()}
args=dict(own=a,other=b,pool=pool,ref=ref,my_weights=w,their_weights=w,tolerance=100,both_improve=False)
assert near_value_trades(**args)
assert not near_value_trades(**args,draft_picks=picks)
assert near_value_trades(**args,draft_picks=picks,draft_guard_samples={k:20 for k in pool})
# Interleaved ranks are not blanket-blocked.
b=roster(['Bam Adebayo','Alex Caruso'])
assert near_value_trades(**dict(args,other=b),draft_picks=picks)
from streamlit.testing.v1 import AppTest
app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=90).run()
app.sidebar.radio[0].set_value('交易分析 Trade Lab').run()
assert app.checkbox(key='auto_flexible_sizes').value and app.number_input(key='auto_n_send').disabled
app.selectbox(key='auto_partner').set_value('全部球隊').run()
app.button(key='auto_find').click().run()
assert not app.exception
r=app.session_state['auto_packages']['results']
assert r and len({x['shape'] for x in r})>1
# Configure a known unused historical player as FA; no fantasy availability is claimed.
mine={str(x.get('id')) for x in app.session_state.get('nc_roster',[])}
app.checkbox(key='auto_flexible_sizes').uncheck().run()
assert not app.number_input(key='auto_n_send').disabled and not app.exception
print('PASS: 30/70 prior, strict draft-dominance guard, interleaved ranks, guard fades with sample, flexible and fixed search modes.')
