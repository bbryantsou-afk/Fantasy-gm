import sys,json
from pathlib import Path
from datetime import date,timedelta
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dashboard_model import aggregate_logs,production,trend
from ninecat_model import baseline,cohort_ids,KEYS
from streamlit.testing.v1 import AppTest
root=Path(__file__).resolve().parents[1]
logs=json.loads((root/'ninecat_assets/game_logs_2025_26.json').read_text())
assert len({(r['PLAYER_ID'],r['GAME_ID']) for r in logs})==len(logs)
start,end=date(2025,10,27),date(2025,11,2)
agg=aggregate_logs(logs,start,end)
for row in agg:
    source=[g for g in logs if g['PLAYER_ID']==row['PLAYER_ID'] and str(start)<=g['GAME_DATE'][:10]<=str(end)]
    assert row['GP']==len(source)
    for c in KEYS:
        assert row[c]==sum(float(g[c] or 0) for g in source)
a=AppTest.from_file(str(root/'app.py'),default_timeout=60).run()
a.sidebar.radio[0].set_value('總覽 Dashboard').run()
a.selectbox(key='dash_season').set_value('2025-26').run()
assert not a.exception
assert len(a.get('vega_lite_chart'))==9
a.date_input[0].set_value(date(2025,10,28)).run()
assert not a.exception
table=a.dataframe[1].value
w=table.loc[table['球員']=='Victor Wembanyama'].iloc[0]
assert w['PTS']==60 and w['REB']==42 and w['場次']==3
assert w['週場均趨勢'].startswith('📉')
a.radio(key='dash_range').set_value('單日').run()
assert not a.exception
a.selectbox(key='dash_season').set_value('2026-27').run()
a.date_input[0].set_value(date(2027,3,1)).run()
assert not a.exception and any('尚未開始' in x.value for x in a.info)
a.sidebar.radio[0].set_value('9-Cat Strategy').run()
assert not a.exception
print('PASS: real log aggregation, weekly totals/trends, daily view, future season, 9Cat regression')
