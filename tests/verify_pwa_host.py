import sys,hashlib,unittest
from pathlib import Path
from unittest.mock import patch,MagicMock
sys.path.insert(0,str(Path(__file__).parents[1]))
from pwa.streamlit_host import dispatch
from google_drive_auth import make_flow,verify_flow
class HostTests(unittest.TestCase):
 def test_cloud_owner_and_league(self):
  user={'sub':'test-owner','iss':'https://accounts.google.com'};service=MagicMock();service.load.return_value={'revision':3}
  with patch('account_store.signed_user',return_value=user),patch('account_store.client',return_value=service):
   self.assertEqual(dispatch({'path':'/api/cloud?league=123'}),{'profile':{'revision':3}})
   self.assertEqual(service.NAME,'fantasy-gm-league-123-v1.json')
   service.load.assert_called_once_with(hashlib.sha256(b'google:test-owner').hexdigest())
 def test_guest_cannot_read_drive(self):
  with patch('account_store.signed_user',return_value=None):
   with self.assertRaises(PermissionError):dispatch({'path':'/api/cloud?league=123'})
 def test_pkce_returns_to_beta(self):
  cfg={'client_id':'test','client_secret':'not-real','redirect_uri':'http://localhost:8501/','state_secret':'x'*48}
  with patch('google_drive_auth.st.query_params',{'app':'1','league':'123'}):flow=make_flow(cfg)
  data=verify_flow(cfg,flow['state'],flow['verifier']);self.assertEqual(data['app'],'1');self.assertEqual(data['league'],'123')
if __name__=='__main__':unittest.main()
