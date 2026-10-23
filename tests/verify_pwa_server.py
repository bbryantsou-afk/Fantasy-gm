"""Private-data boundaries and real bookmark import for the independent PWA."""
import sys,json,threading,unittest
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.request import Request,urlopen
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).parents[1]))
from pwa.server import Handler,ThreadingHTTPServer,normalize_snapshot,validate_profile,ROOT
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler);cls.server.base=f'http://127.0.0.1:{cls.server.server_port}'
  threading.Thread(target=cls.server.serve_forever,daemon=True).start();cls.base=cls.server.base
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close()
 def get(self,path):return urlopen(self.base+path)
 def test_shell_and_public_model(self):
  r=self.get('/');self.assertIn('frame-ancestors',r.headers['Content-Security-Policy']);self.assertIn(b'id="menu"',r.read())
  model=json.load(self.get('/api/model'));self.assertGreater(len(model['players']),100);self.assertIsInstance(model['schedule'],dict)
  self.assertNotIn('teams',model);self.assertNotIn('entries',model)
 def test_auth_and_csrf(self):
  r=self.get('/api/session');cookie=r.headers['Set-Cookie'].split(';')[0];session=json.load(r)
  self.assertNotIn('token',session);self.assertNotIn('secret',json.dumps(session));self.assertIn('HttpOnly',r.headers['Set-Cookie'])
  req=Request(self.base+'/api/validate',data=b'{}',headers={'Content-Type':'application/json'})
  with self.assertRaises(HTTPError) as e:urlopen(req)
  self.assertEqual(e.exception.code,403)
  req=Request(self.base+'/api/validate',data=b'{}',headers={'Cookie':cookie,'Origin':self.base,'X-CSRF-Token':session['csrf'],'Content-Type':'application/json'})
  with self.assertRaises(HTTPError) as e:urlopen(req)
  self.assertEqual(e.exception.code,400)
  with self.assertRaises(HTTPError) as e:self.get('/api/cloud?league=123')
  self.assertEqual(e.exception.code,401)
 def test_no_private_static_access(self):
  for path in ['/../.streamlit/secrets.toml','/api/unknown','/league_rosters.json']:
   with self.assertRaises(HTTPError) as e:self.get(path)
   self.assertEqual(e.exception.code,404)
 def test_real_import_shape(self):
  players=json.loads((ROOT/'ninecat_assets/data.json').read_text())['players'][:2]
  today=datetime.now(ZoneInfo('America/New_York')).date().isoformat()
  raw={'schema':1,'league':'123','date':today,'capturedAt':datetime.now(ZoneInfo('UTC')).isoformat(),'teams':[]}
  for i,p in enumerate(players):raw['teams'].append({'id':str(i+1),'name':'Example '+str(i),'date':today,'rows':[{'yahooPlayerId':str(100+i),'name':p['PLAYER_NAME'],'position':'PG','eligible':['PG'],'nbaTeam':p['TEAM_ABBREVIATION']}]})
  league=normalize_snapshot(raw);self.assertEqual(len(league['teams']),2);self.assertIn(today,league['daily_rosters'])
  checked=validate_profile({'schema':1,'files':{'league_rosters.json':league,'player_watchlist.json':{'ids':[str(players[0]['PLAYER_ID'])]}},'prefs':{}})
  self.assertEqual(checked['files']['league_rosters.json']['sync_league'],'123')
if __name__=='__main__':unittest.main()
