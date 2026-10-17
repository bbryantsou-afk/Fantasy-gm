"""Cloud visitors must not share private JSON files."""
import sys,tempfile,os
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from streamlit.testing.v1 import AppTest
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(dir=root/'backups') as temp:
    script=Path(temp)/'storage_check.py'
    script.write_text("import sys\nsys.path.insert(0,"+repr(str(root))+")\nimport streamlit as st\nfrom app_storage import private_path\np=private_path('player_watchlist.json')\nst.text(str(p))\nif st.button('save'): p.write_text('private-value')\nst.text(p.read_text() if p.exists() else 'empty')\n")
    with patch.dict(os.environ,{'FANTASY_GM_STORAGE_MODE':'session'}),patch('app_storage.tempfile.gettempdir',return_value=temp):
        a=AppTest.from_file(str(script)).run()
        a.button[0].click().run()
        assert a.text[-1].value=='private-value'
        b=AppTest.from_file(str(script)).run()
        assert b.text[-1].value=='empty' and a.text[0].value!=b.text[0].value
        cloud=AppTest.from_file(str(root/'app.py'),default_timeout=60).run()
        cloud.sidebar.radio[0].set_value('9-Cat Strategy').run()
        assert not cloud.exception and cloud.session_state['nc_roster']==[]
print('PASS: separate anonymous cloud sessions and no import of private local roster.')
