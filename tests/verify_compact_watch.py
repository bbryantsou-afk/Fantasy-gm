import os,sys
from pathlib import Path
os.environ['FANTASY_GM_STORAGE_MODE']='session'
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from streamlit.testing.v1 import AppTest
script='''
import sys
sys.path.insert(0,ROOT)
import streamlit as st
import player_hub
player_hub.show_player_detail=lambda selected,*args:st.text('DETAIL:'+selected)
player_hub.render_watchroom()
'''.replace('ROOT',repr(str(root)))
a=AppTest.from_string(script,default_timeout=60).run();assert not a.exception,a.exception
cards=[b for b in a.button if b.key and b.key.startswith('watch_expand_')]
assert len(cards)>=11
first,second=cards[0].key,cards[10].key
next(b for b in a.button if b.key==first).click().run();assert not a.exception,a.exception
assert [t.value for t in a.text if t.value.startswith('DETAIL:')]==['DETAIL:'+first.removeprefix('watch_expand_')]
next(b for b in a.button if b.key==second).click().run();assert not a.exception,a.exception
assert len([b for b in a.button if b.key=='watch_collapse'])==1
assert [t.value for t in a.text if t.value.startswith('DETAIL:')]==['DETAIL:'+second.removeprefix('watch_expand_')]
next(b for b in a.button if b.key=='watch_collapse').click().run();assert not a.exception
assert not [t for t in a.text if t.value.startswith('DETAIL:')]
a.session_state['device_view']='手機版';a.run();assert not a.exception
assert any('repeat(5,minmax' in m.value for m in a.markdown)
print('PASS watch controls, ten-column desktop/five-column mobile, switching expanded rows and collapse without duplicate widgets')
