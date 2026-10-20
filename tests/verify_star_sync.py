import os,sys,copy
from pathlib import Path
from unittest.mock import patch
os.environ['FANTASY_GM_STORAGE_MODE']='session'
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from streamlit.testing.v1 import AppTest
from account_store import CloudConflict
class Profiles:
 def __init__(self):self.row={'revision':1,'payload':{'schema':1,'files':{'player_watchlist.json':{'ids':[]}},'prefs':{}}}
 def load(self,owner):return copy.deepcopy(self.row)
 def save(self,owner,revision,payload):
  if revision!=self.row['revision']:raise CloudConflict('stale')
  self.row={'revision':revision+1,'payload':copy.deepcopy(payload)};return revision+1
db=Profiles();user={'iss':'https://accounts.google.com','sub':'star-sync-test'}
script='''
import sys
sys.path.insert(0,ROOT_PATH)
import streamlit as st
from account_store import init_account,poll_account,finish_account
from player_hub import star_picker,load_stars
init_account();poll_account()
page=st.radio('page',['watch','strategy'])
star_picker([{'PLAYER_ID':1,'PLAYER_NAME':'One'},{'PLAYER_ID':2,'PLAYER_NAME':'Two'}],'watch_stars' if page=='watch' else 'nc_watch_stars')
st.json(load_stars());finish_account()
'''.replace('ROOT_PATH',repr(str(ROOT)))
with patch('account_store.config',return_value={'configured':True}),patch('account_store.init_auth'),patch('account_store.client',return_value=db),patch('account_store.signed_user',return_value=user):
 desktop=AppTest.from_string(script,default_timeout=60).run()
 phone=AppTest.from_string(script,default_timeout=60).run()
 assert not desktop.exception and not phone.exception
 phone.radio[0].set_value('strategy').run()
 assert phone.multiselect[0].value==[]
 desktop.multiselect[0].set_value(['1']).run()
 assert not desktop.exception,desktop.exception
 assert db.row['payload']['files']['player_watchlist.json']['ids']==['1']
 phone.run();assert not phone.exception,phone.exception
 assert phone.multiselect[0].value==['1'] # remote restore invalidates the other page's cached picker too
 phone.multiselect[0].set_value(['1','2']).run()
 desktop.run();assert not desktop.exception,desktop.exception
 assert desktop.multiselect[0].value==['1','2']
 desktop.multiselect[0].set_value(['2']).run();phone.run()
 assert phone.multiselect[0].value==['2']
 assert not any(b.label=='儲存加星名單' for b in desktop.button)
 from account_store import CloudError
 with patch.object(db,'load',side_effect=CloudError('offline test')):
  phone.run();assert any('跨裝置更新暫停' in w.value for w in phone.warning)
 phone.run();assert not any('跨裝置更新暫停' in w.value for w in phone.warning)
 next(b for b in phone.button if b.label=='重新檢查 Google Drive').click().run()
 assert not phone.exception
print('PASS automatic star add/remove save, two-way independent-session refresh and both star-picker cache invalidation')
