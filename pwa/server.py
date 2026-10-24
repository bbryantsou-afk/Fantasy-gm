"""Separate PWA host. Existing Streamlit deployment and private files stay untouched."""
from __future__ import annotations
import argparse,base64,hashlib,http.cookies,json,mimetypes,os,re,secrets,sys,threading,time,tomllib
from datetime import date,datetime
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs,urlencode,urlsplit
import requests
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
WEB=Path(__file__).parent/'web'
SESSIONS={};GUARD=threading.RLock();MAX_BODY=4_100_000

def configuration():
    try:cfg=tomllib.loads((ROOT/'.streamlit/secrets.toml').read_text()).get('google_drive',{})
    except (OSError,ValueError):cfg={}
    return {k:os.environ.get('PWA_GOOGLE_'+k.upper(),cfg.get(k,'')) for k in ('client_id','client_secret')}

def validate_profile(payload):
    from browser_records import validate_records
    if not isinstance(payload,dict) or payload.get('schema')!=1:raise ValueError('紀錄格式不符')
    league=payload.get('files',{}).get('league_rosters.json',{})
    teams=list(league.get('teams',{}))
    if len(teams)>30 or any(not isinstance(t,str) or not 1<=len(t)<=120 for t in teams):raise ValueError('隊伍格式不符')
    files,prefs=validate_records(payload,[{'fantasyTeam':t} for t in teams])
    return {'schema':1,'files':files,'prefs':prefs}

def normalize_snapshot(raw,current=None):
    from league_sync import validate_snapshot,match_snapshot,apply_snapshot
    players=json.loads((ROOT/'ninecat_assets/data.json').read_text())['players']
    entries=json.loads((ROOT/'ninecat_assets/draft.json').read_text())['entries']
    lid=str(raw.get('league',''));day=date.fromisoformat(raw['date'])
    if not re.fullmatch(r'\d{1,10}',lid):raise ValueError('聯盟 ID 不符')
    rows=validate_snapshot(raw,lid,day,len(raw.get('teams',[])))
    if not 2<=len(raw['teams'])<=30:raise ValueError('隊伍數量不符')
    matched,_=match_snapshot(rows,players,entries)
    keys=list(dict.fromkeys(e['fantasyTeam'] for e in entries))
    if len(keys)!=len(raw['teams']):keys=['隊伍'+str(i+1) for i in range(len(raw['teams']))]
    existing=current if current and current.get('sync_league')==lid else None
    mapping=(existing or {}).get('sync_mapping') or {lid+':'+str(t['id']):keys[i] for i,t in enumerate(raw['teams'])}
    league=existing or {'teams':{t:[] for t in mapping.values()},'free':[],'capacity':14,'revision':0}
    from zoneinfo import ZoneInfo
    today=datetime.now(ZoneInfo('America/New_York')).date()
    return apply_snapshot(league,matched,mapping,raw,today)

def normalize_results(raw,current):
    import copy
    from yahoo_matchup_results import import_results
    lid=str(current.get('sync_league',''))
    key,result=import_results(raw,lid,current.get('sync_mapping',{}),set(current.get('teams',{})))
    out=copy.deepcopy(current);out.setdefault('yahoo_matchups',{})[key]=result
    return out

def simulator_status():
    from zoneinfo import ZoneInfo
    from daily_evidence import nba_today
    day=datetime.now(ZoneInfo('America/New_York')).date().isoformat()
    live=nba_today(day)
    return {'day':day,'pregameTeams':live.get('scheduled_teams',[])}

class Handler(BaseHTTPRequestHandler):
    def log_message(self,fmt,*args):
        # OAuth code, bookmark fragments, tokens and request bodies never enter logs.
        print(self.command,urlsplit(self.path).path,flush=True)
    def reply(self,status,data=None,headers=None):
        body=b'' if data is None else json.dumps(data,ensure_ascii=False,allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        for k,v in (headers or {}).items():self.send_header(k,v)
        self.end_headers();self.wfile.write(body)
    def session(self,create=False):
        cookie=http.cookies.SimpleCookie()
        try:cookie.load(self.headers.get('Cookie',''))
        except http.cookies.CookieError:pass
        key=cookie.get('fgm_pwa');sid=key.value if key else ''
        with GUARD:
            s=SESSIONS.get(sid)
            if s and time.time()-s['created']>86400:SESSIONS.pop(sid,None);s=None
            if not s and create:
                sid=secrets.token_urlsafe(32);s={'created':time.time(),'csrf':secrets.token_urlsafe(32),'state':{}};SESSIONS[sid]=s
        self.sid=sid
        return s
    def cookie(self):
        return 'fgm_pwa='+self.sid+'; Path=/; HttpOnly; SameSite=Lax'+('; Secure' if self.server.base.startswith('https:') else '')
    def body(self):
        n=int(self.headers.get('Content-Length','0'))
        if not 0<n<=MAX_BODY:raise ValueError('資料過大或空白')
        return json.loads(self.rfile.read(n))
    def auth(self,s):
        if not s or not s.get('user'):raise PermissionError('請先登入 Google')
        return hashlib.sha256(('google:'+s['user']['sub']).encode()).hexdigest()
    def token(self,s):
        token=s.get('token',{})
        if token.get('expires_at',0)<=time.time():
            from google_drive_auth import token_request
            fresh=token_request(configuration(),{'grant_type':'refresh_token','refresh_token':token.get('refresh_token','')})
            fresh['refresh_token']=token.get('refresh_token');s['token']=fresh
        return s['token']['access_token']
    def cloud(self,s,lid):
        from drive_profiles import CloudClient
        client=CloudClient(token_provider=lambda:self.token(s),state=s['state'])
        client.NAME='fantasy-gm-league-'+lid+'-v1.json'
        return client
    def do_GET(self):
        try:self.get()
        except (ValueError,KeyError,TypeError):self.reply(400,{'error':'資料格式不符，原紀錄未修改'})
        except PermissionError as e:self.reply(401,{'error':str(e)})
        except Exception as e:
            from drive_profiles import CloudError,CloudConflict
            if isinstance(e,CloudConflict):self.reply(409,{'error':'雲端已更新，請先讀取最新版本'})
            elif isinstance(e,CloudError):self.reply(502,{'error':'Drive 暫時無法讀取，請重新登入或稍後再試'})
            else:self.reply(500,{'error':'載入失敗，請重試；原紀錄未修改'})
    def get(self):
        url=urlsplit(self.path);q=parse_qs(url.query);path=url.path
        if path=='/api/session':
            s=self.session(True);cfg=configuration()
            return self.reply(200,{'csrf':s['csrf'],'user':s.get('user'),'googleConfigured':bool(cfg['client_id'] and cfg['client_secret']),'callback':self.server.base+'/auth/callback'}, {'Set-Cookie':self.cookie()})
        if path=='/api/sim-status':return self.reply(200,simulator_status())
        if path=='/api/strategy-stats':
            from strategy_season import strategy_snapshot
            return self.reply(200,strategy_snapshot(parse_qs(urlsplit(self.path).query).get('season',['2026-27'])[0]))
        if path=='/api/model':
            from dashboard_model import regular_schedule
            data=json.loads((ROOT/'ninecat_assets/data.json').read_text())
            raw_schedule,_=regular_schedule(json.loads((ROOT/'nba_schedule_2026_27.json').read_text()))
            schedule={team:sorted(str(day) for day in days) for team,days in raw_schedule.items()}
            return self.reply(200,{'season':data['season'],'players':data['players'],'schedule':schedule})
        if path=='/api/bookmark':
            parser=(ROOT/'browser_sync_extension/parser.js').read_text()
            target=self.server.base+'/?phone_sync=1'
            script=(ROOT/'mobile_roster_sync.js').read_text().replace('__PARSER__',parser).replace('__APP_URL__',json.dumps(target))
            from urllib.parse import quote
            return self.reply(200,{'bookmark':'javascript:'+quote('\n'.join(x for x in script.splitlines() if not x.strip().startswith('//')),safe="()!*'~-._")})
        if path=='/api/cloud':
            s=self.session();owner=self.auth(s);lid=q.get('league',[''])[0]
            if not re.fullmatch(r'\d{1,10}',lid):raise ValueError()
            return self.reply(200,{'profile':self.cloud(s,lid).load(owner)})
        if path=='/api/news':
            pid=q.get('player',[''])[0]
            if not pid.isdigit():raise ValueError()
            players=json.loads((ROOT/'ninecat_assets/data.json').read_text())['players']
            p=next((p for p in players if str(p['PLAYER_ID'])==pid),None)
            if not p:raise ValueError()
            from player_hub import player_news,translated_news,news_time
            return self.reply(200,{'items':[dict(n,time=news_time(n['published'])) for n in translated_news(player_news(p['PLAYER_NAME']))]})
        if path=='/auth/start':
            s=self.session(True);cfg=configuration()
            if not all(cfg.values()):return self.reply(503,{'error':'新版 Google 登入尚未設定'})
            state=secrets.token_urlsafe(32);verifier=secrets.token_urlsafe(48)
            s['oauth']={'state':state,'verifier':verifier,'at':time.time(),'league':q.get('league',[''])[0]}
            challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
            target='https://accounts.google.com/o/oauth2/v2/auth?'+urlencode({'client_id':cfg['client_id'],'redirect_uri':self.server.base+'/auth/callback','response_type':'code','scope':'openid email profile https://www.googleapis.com/auth/drive.appdata','state':state,'code_challenge':challenge,'code_challenge_method':'S256','access_type':'offline','prompt':'consent'})
            return self.reply(302,headers={'Location':target,'Set-Cookie':self.cookie()})
        if path=='/auth/callback':
            s=self.session();pending=(s or {}).pop('oauth',{})
            if q.get('error') or not pending or time.time()-pending.get('at',0)>600 or not secrets.compare_digest(q.get('state',[''])[0],pending.get('state','')):
                return self.reply(302,headers={'Location':'/?login=failed'})
            from google_drive_auth import token_request,identity
            token=token_request(configuration(),{'grant_type':'authorization_code','code':q['code'][0],'redirect_uri':self.server.base+'/auth/callback','code_verifier':pending['verifier']})
            if not token.get('refresh_token'):return self.reply(302,headers={'Location':'/?login=failed'})
            s['user']=identity(token);s['token']=token
            lid=pending.get('league','');target='/?league='+lid if re.fullmatch(r'\d{1,10}',lid) else '/'
            return self.reply(302,headers={'Location':target,'Set-Cookie':self.cookie()})
        if path.startswith('/api/') or path.startswith('/auth/'):return self.reply(404,{'error':'找不到此操作'})
        file=WEB/('index.html' if path=='/' else path.lstrip('/'))
        if not file.resolve().is_relative_to(WEB.resolve()) or not file.is_file() or file.name.startswith('.'):
            return self.reply(404,{'error':'找不到頁面'})
        data=file.read_bytes();self.send_response(200)
        self.send_header('Content-Type',mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
        self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-cache')
        self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','same-origin')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' https://cdn.nba.com data:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'")
        self.end_headers();self.wfile.write(data)
    def do_POST(self):
        try:
            s=self.session();origin=self.headers.get('Origin');token=self.headers.get('X-CSRF-Token','')
            if not s or origin!=self.server.base or not secrets.compare_digest(token,s['csrf']):return self.reply(403,{'error':'請重新開啟 App 再試'})
            body=self.body();path=urlsplit(self.path).path
            if path=='/api/normalize-results':return self.reply(200,{'league':normalize_results(body['results'],body['current'])})
            if path=='/api/normalize':return self.reply(200,{'league':normalize_snapshot(body['snapshot'],body.get('current'))})
            if path=='/api/validate':return self.reply(200,{'payload':validate_profile(body)})
            if path=='/api/logout':
                with GUARD:SESSIONS.pop(self.sid,None)
                return self.reply(200,{}, {'Set-Cookie':'fgm_pwa=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0'})
            if path=='/api/cloud':
                owner=self.auth(s);lid=str(body.get('league',''))
                if not re.fullmatch(r'\d{1,10}',lid):raise ValueError()
                payload=validate_profile(body['payload'])
                recorded=payload['files'].get('league_rosters.json',{}).get('sync_league')
                if recorded and recorded!=lid:raise ValueError()
                revision=body.get('revision')
                if type(revision) is not int or revision<0:raise ValueError()
                return self.reply(200,{'revision':self.cloud(s,lid).save(owner,revision,payload)})
            return self.reply(404,{'error':'找不到此操作'})
        except (ValueError,KeyError,TypeError):self.reply(400,{'error':'資料格式不符，原紀錄未修改'})
        except PermissionError as e:self.reply(401,{'error':str(e)})
        except Exception as e:
            from drive_profiles import CloudConflict
            self.reply(409 if isinstance(e,CloudConflict) else 502,{'error':'雲端已更新，請先讀取最新版本' if isinstance(e,CloudConflict) else '操作未完成，原紀錄保留；請稍後重試'})

def serve(port=8504,base=None):
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler);server.base=(base or f'http://localhost:{port}').rstrip('/')
    print('Fantasy GM PWA: '+server.base,flush=True);server.serve_forever()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8504);p.add_argument('--base');a=p.parse_args();serve(a.port,a.base)
