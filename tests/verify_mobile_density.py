import os,sys
from pathlib import Path
from unittest.mock import patch
os.environ['FANTASY_GM_STORAGE_MODE']='session'
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from streamlit.testing.v1 import AppTest
from mobile_stat_cards import player_rows
row={'球員':'<Player>','NBA球隊':'SECRET_TEAM','狀態':'SECRET_STATUS','MVP分':999,'場次':2,'週場均趨勢':'📈 +0.542','PTS':10}
markup=player_rows([row])
assert '&lt;Player&gt;' in markup and '📈' in markup and '+0.542' not in markup
assert all(x not in markup for x in ['SECRET_TEAM','SECRET_STATUS','999'])
with patch('daily_evidence.nba_today',return_value={'phase':'pregame','players':{},'statuses':[],'updated_at':'','error':''}),patch('daily_evidence.refresh_live_page'):
 a=AppTest.from_file(str(ROOT/'app.py'),default_timeout=90)
 a.query_params['view']='mobile';a.run();assert not a.exception,a.exception
 assert any('mobile-player-rows' in m.value for m in a.markdown)
 assert a.sidebar.button(key='mobile_sync_shortcut')
 a.sidebar.button(key='mobile_sync_shortcut').click().run();assert not a.exception,a.exception
 assert a.session_state['main_navigation']=='聯盟同步 League Sync'
 assert any('前往 Yahoo 更新名單' in str(x.proto) for x in a.get('link_button'))
 a.sidebar.radio(key='main_navigation').set_value('9-Cat Strategy').run();assert not a.exception,a.exception
 assert any('mobile-rank-list' in m.value for m in a.markdown)
 assert a.selectbox(key='nc_mobile_detail')
print('PASS compact player rows omit private columns, emoji-only trends, mobile shortcut navigation and compact strategy details')
