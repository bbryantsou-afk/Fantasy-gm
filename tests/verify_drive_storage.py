import sys,json,time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from google_drive_auth import make_flow,verify_flow,seal,unseal,AuthError,challenge
from drive_profiles import CloudClient,CloudError,CloudConflict
c={'client_id':'test','client_secret':'not-real','redirect_uri':'http://localhost:8501/','state_secret':'x'*48}
flow=make_flow(c);verify_flow(c,flow['state'],flow['verifier'])
assert challenge('dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk')=='E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM'
for state,verifier in [(flow['state']+'x',flow['verifier']),(flow['state'],'bad')]:
 try:verify_flow(c,state,verifier);raise AssertionError('invalid flow accepted')
 except AuthError:pass
with patch('google_drive_auth.time.time',return_value=time.time()+601):
 try:verify_flow(c,flow['state'],flow['verifier']);raise AssertionError('expired flow accepted')
 except AuthError:pass
envelope=seal(c,'test-refresh','sub-a');assert 'test-refresh' not in envelope
assert unseal(c,envelope)=={'refresh':'test-refresh','sub':'sub-a'}
try:unseal(dict(c,state_secret='y'*48),envelope);raise AssertionError('wrong key accepted')
except AuthError:pass
class Response:
 def __init__(self,data,status=200,etag='"v1"'):
  self.data=data;self.status_code=status;self.ok=200<=status<300;self.headers={'ETag':etag} if etag else {};self.content=json.dumps(data).encode()
 def json(self):return self.data
owner='a'*64;payload={'schema':1,'files':{},'prefs':{}}
profile={'owner':owner,'revision':1,'payload':payload}
with patch('drive_profiles.access_token',return_value='private-access'),patch('drive_profiles.requests.request') as request:
 request.side_effect=[Response({'files':[{'id':'file1'}]}),Response({'id':'file1','etag':'"v1"'}),Response(profile),Response({'id':'file1','etag':'"v1"'}),Response({'id':'file1'})]
 assert CloudClient().save(owner,1,payload)==2
 calls=request.call_args_list
 assert calls[0].kwargs['params']['spaces']=='appDataFolder'
 assert calls[4].kwargs['headers']['If-Match']=='"v1"'
 assert calls[4].args[:2]==('PUT','https://www.googleapis.com/upload/drive/v2/files/file1')
 assert all(x.kwargs['headers']['Authorization']=='Bearer private-access' for x in calls)
 assert all('private-access' not in x.args[1] for x in calls)
 request.reset_mock();request.side_effect=[Response({'files':[{'id':'file1'}]}),Response({'id':'file1'}),Response(profile),Response({'id':'file1'})]
 try:CloudClient().save(owner,1,payload);raise AssertionError('unconditional write allowed')
 except CloudError:pass
 assert request.call_count==4
 request.reset_mock();request.side_effect=[Response({'files':[{'id':'file1','version':'10'}]}),Response(profile),Response({'files':[{'id':'file1','version':'10'}]})]
 assert CloudClient().load(owner)['revision']==1
 assert CloudClient().load_if_changed(owner) is None
 assert request.call_count==3 # unchanged checks fetch only metadata, not the whole roster
 request.reset_mock();request.side_effect=[Response({'files':[{'id':'file1'}]}),Response({'id':'file1','etag':'"v1"'}),Response(profile),Response({'id':'file1','etag':'"v1"'}),Response({},412)]
 try:CloudClient().save(owner,1,payload);raise AssertionError('conflict overwritten')
 except CloudConflict:pass
 request.reset_mock();request.side_effect=[Response({'files':[{'id':'file1'}]}),Response({'id':'file1','etag':'"v1"'}),Response(profile),Response({'id':'file1','etag':'"v2"'})]
 try:CloudClient().save(owner,1,payload);raise AssertionError('download race accepted')
 except CloudConflict:pass
 assert request.call_count==4
 request.reset_mock();request.side_effect=[Response({'files':[]}),Response({'id':'new'})]
 assert CloudClient().save(owner,0,payload)==1
 assert b'"parents": ["appDataFolder"]' in request.call_args.kwargs['data']
 request.reset_mock();request.side_effect=[Response({'files':[{'id':'one'},{'id':'two'}]})]
 try:CloudClient().load(owner);raise AssertionError('duplicates silently accepted')
 except CloudError:pass
print('PASS PKCE, state tamper/expiry, encrypted login restore, Drive appData-only requests, conditional writes and duplicate protection (mock HTTP)')
