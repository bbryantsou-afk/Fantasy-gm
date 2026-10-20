"""Google authorization-code + PKCE flow; no credentials in profile backups."""
import base64,hashlib,hmac,json,secrets,time
from pathlib import Path
from urllib.parse import urlencode
import requests
import streamlit as st
import streamlit.components.v1 as components

SCOPE='openid email profile https://www.googleapis.com/auth/drive.appdata'
bridge=components.declare_component('drive_authorization',path=str(Path(__file__).parent/'drive_authorization'))
class AuthError(Exception):pass

def config():
    try:
        c=dict(st.secrets['google_drive'])
        if not all(c.get(k) for k in ('client_id','client_secret','redirect_uri','state_secret')):return None
        if len(c['state_secret'])<32:return None
        if c['redirect_uri']!='https://fantasy-gm-bgjfjwjnxx8mbxjvajm2nk.streamlit.app/' and not c['redirect_uri'].startswith('http://localhost:'):return None
        return c
    except (KeyError,FileNotFoundError):return None

def b64(raw):return base64.urlsafe_b64encode(raw).decode().rstrip('=')
def challenge(verifier):return b64(hashlib.sha256(verifier.encode()).digest())
def make_flow(c):
    verifier=secrets.token_urlsafe(48)
    body=b64(json.dumps({'t':int(time.time()),'n':secrets.token_urlsafe(24),'p':challenge(verifier)},separators=(',',':')).encode())
    state='fgmdrive.'+body+'.'+b64(hmac.new(c['state_secret'].encode(),body.encode(),hashlib.sha256).digest())
    url='https://accounts.google.com/o/oauth2/v2/auth?'+urlencode({'client_id':c['client_id'],'redirect_uri':c['redirect_uri'],'response_type':'code','scope':SCOPE,'state':state,'code_challenge':challenge(verifier),'code_challenge_method':'S256','access_type':'offline','prompt':'consent','include_granted_scopes':'false'})
    return {'state':state,'verifier':verifier,'url':url,'created':time.time()}

def verify_flow(c,state,verifier):
    try:
        prefix,body,sig=state.split('.')
        expected=b64(hmac.new(c['state_secret'].encode(),body.encode(),hashlib.sha256).digest())
        data=json.loads(base64.urlsafe_b64decode(body+'='*(-len(body)%4)))
        if prefix!='fgmdrive' or not hmac.compare_digest(sig,expected) or not 0<=time.time()-data['t']<=600 or not hmac.compare_digest(data['p'],challenge(verifier)):raise ValueError()
    except (ValueError,TypeError,KeyError):raise AuthError('登入驗證已過期或不符，請重新登入。') from None

def cipher(c):
    from cryptography.fernet import Fernet
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(c['state_secret'].encode()).digest()))

def seal(c,refresh,sub):return cipher(c).encrypt(json.dumps({'refresh':refresh,'sub':sub}).encode()).decode()
def unseal(c,envelope):
    from cryptography.fernet import InvalidToken
    try:
        data=json.loads(cipher(c).decrypt(envelope.encode(),ttl=60*60*24*90))
        if not isinstance(data.get('refresh'),str) or not isinstance(data.get('sub'),str):raise ValueError()
        return data
    except (InvalidToken,ValueError,TypeError,KeyError,AttributeError):raise AuthError('此瀏覽器的登入憑證已失效，請重新登入。') from None

def token_request(c,grant):
    try:
        r=requests.post('https://oauth2.googleapis.com/token',data={**grant,'client_id':c['client_id'],'client_secret':c['client_secret']},timeout=20)
        if not r.ok:raise AuthError('Google 授權失效或未完成，請重新登入。')
        token=r.json()
        if not isinstance(token.get('access_token'),str):raise AuthError('Google 登入回應不完整。')
        scopes=set(token.get('scope',SCOPE).split())
        if 'https://www.googleapis.com/auth/drive.appdata' not in scopes:raise AuthError('尚未授權 App 專用 Drive 儲存，無法保存。')
        token['expires_at']=time.time()+int(token.get('expires_in',3600))-60
        return token
    except (requests.RequestException,ValueError,TypeError):raise AuthError('無法連線 Google，請稍後重試登入。') from None

def identity(token):
    try:
        r=requests.get('https://openidconnect.googleapis.com/v1/userinfo',headers={'Authorization':'Bearer '+token['access_token']},timeout=20)
        if not r.ok:raise AuthError('Google 身分驗證失敗。')
        user=r.json()
        if not isinstance(user.get('sub'),str) or not user['sub']:raise AuthError('Google 身分資料不完整。')
        return {k:user[k] for k in ('sub','name','email','picture') if k in user}|{'iss':'https://accounts.google.com'}
    except (requests.RequestException,ValueError):raise AuthError('無法驗證 Google 帳號，請重新登入。') from None

def access_token():
    c=config();token=st.session_state.get('_drive_token')
    if not token:raise AuthError('請先登入 Google。')
    if token['expires_at']<=time.time():
        refresh=token.get('refresh_token')
        if not refresh:raise AuthError('登入已過期，請重新登入 Google。')
        fresh=token_request(c,{'grant_type':'refresh_token','refresh_token':refresh})
        fresh['refresh_token']=refresh;token=fresh;st.session_state['_drive_token']=token
    return token['access_token']

def init_auth():
    c=config()
    if not c:return
    state=str(st.query_params.get('state',''))
    callback={k:str(st.query_params.get(k,'')) for k in ('code','state','error')} if state.startswith('fgmdrive.') else None
    if st.session_state.get('_drive_logged_out') and not callback:return
    value=bridge(mode='read',callback=callback,key='drive_auth_reader',default=None)
    if st.session_state.get('_drive_auth_ready') and not callback:return
    if not isinstance(value,dict):st.caption('正在恢復登入狀態…');st.stop()
    try:
        if value.get('error'):raise AuthError('無法恢復瀏覽器登入狀態，請重新登入。')
        token=None
        if callback:
            if value.get('error') or callback.get('error'):raise AuthError('Google 登入已取消或無法確認原瀏覽器，請重新登入。')
            verifier=value.get('verifier','');verify_flow(c,state,verifier)
            token=token_request(c,{'grant_type':'authorization_code','code':callback['code'],'redirect_uri':c['redirect_uri'],'code_verifier':verifier})
            if not token.get('refresh_token'):raise AuthError('Google 未提供持續授權，請重新登入並允許 App 專用儲存。')
            user=identity(token)
            st.session_state['_drive_envelope']=seal(c,token['refresh_token'],user['sub'])
        elif value.get('envelope'):
            saved=unseal(c,value['envelope'])
            token=token_request(c,{'grant_type':'refresh_token','refresh_token':saved['refresh']})
            token['refresh_token']=saved['refresh'];user=identity(token)
            if user['sub']!=saved['sub']:raise AuthError('登入帳號不符，請重新登入。')
        if token:
            st.session_state['_drive_user']=user;st.session_state['_drive_token']=token
        st.session_state['_drive_auth_ready']=True
    except AuthError as exc:
        st.session_state['_drive_auth_error']=str(exc);st.session_state['_drive_auth_ready']=True
        st.session_state.pop('_drive_user',None);st.session_state.pop('_drive_token',None)
    if callback:
        for k in ('code','state','scope','authuser','prompt','error','iss'):st.query_params.pop(k,None)
        st.rerun()
def render_login(key='drive_login'):
    c=config()
    if not c:return
    if st.session_state.get('_drive_auth_error'):st.warning(st.session_state['_drive_auth_error'])
    flow=st.session_state.get('_drive_pending_flow')
    if not flow or time.time()-flow.get('created',0)>540:
        flow=make_flow(c);st.session_state['_drive_pending_flow']=flow
    bridge(mode='login',flow=flow,key=key,default=None)

def render_logout(key='drive_logout'):
    result=bridge(mode='logout',key=key,default=None)
    if result=={'logout':True}:
        st.session_state.clear();st.session_state['_drive_logged_out']=True;st.rerun()

def finish_auth():
    if st.session_state.get('_drive_envelope'):
        bridge(mode='save',envelope=st.session_state['_drive_envelope'],key='drive_auth_save',default=None)
