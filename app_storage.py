"""Keep anonymous cloud visitors separate; preserve existing Mac local storage."""
import os,sys,tempfile,uuid
from pathlib import Path
import streamlit as st

def private_path(local_path):
    from account_store import account_path
    account=account_path(Path(local_path).name)
    if account is not None:return account
    from mobile_share import shared_path
    shared=shared_path(Path(local_path).name)
    if shared is not None:return shared
    mode=os.environ.get("FANTASY_GM_STORAGE_MODE","local" if sys.platform=="darwin" else "session")
    if mode=="local":
        return Path(local_path)
    token=st.session_state.get("_private_storage_id")
    if token is None:
        token=uuid.uuid4().hex
        st.session_state["_private_storage_id"]=token
    root=Path(tempfile.gettempdir())/"fantasy-gm-sessions"/token
    root.mkdir(parents=True,exist_ok=True)
    return root/Path(local_path).name
