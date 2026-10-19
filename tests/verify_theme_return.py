import sys,hmac,hashlib,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from yahoo_auth import build_authorization_url,exchange_code_for_token
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
for theme in ('light','tactics','mirror'):
    _,state=build_authorization_url('test-client','test-secret','https://example.com',theme=theme)
    stamp,nonce,signature=state.split('.')
    assert nonce.startswith(theme+'~')
    assert hmac.compare_digest(signature,hmac.new(b'test-secret',f'{stamp}.{nonce}'.encode(),hashlib.sha256).hexdigest())
    with patch('yahoo_auth.requests.post') as post:
        post.return_value.ok=True
        post.return_value.json.return_value={'access_token':'test-only'}
        assert exchange_code_for_token('dummy',state,None,'test-client','test-secret','https://example.com')['access_token']=='test-only'
        bad=state[:-1]+('0' if state[-1]!='0' else '1')
        try:
            exchange_code_for_token('dummy',bad,None,'test-client','test-secret','https://example.com')
            raise AssertionError('tampered state accepted')
        except ValueError:pass
        assert post.call_count==1
app=AppTest.from_string("""
import streamlit as st
from court_theme import render_court_theme,clear_oauth_query
render_court_theme()
if st.button('clear'):clear_oauth_query()
""",default_timeout=30)
_,state=build_authorization_url('test','test','https://example.com',theme='tactics')
app.query_params['state']=state
app.query_params['code']='dummy'
app.run()
assert not app.exception
assert app.selectbox(key='visual_theme').value=='戰術板草圖'
app.button[0].click().run()
assert not app.exception
assert 'code' not in app.query_params and 'state' not in app.query_params
assert app.query_params['theme']==['tactics'] or app.query_params['theme']=='tactics'
print('PASS signed theme context, tamper rejection and callback cleanup preserves theme')
