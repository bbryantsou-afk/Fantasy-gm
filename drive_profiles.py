"""Private per-user appDataFolder profile; conditional writes never blindly overwrite."""
import json,re,threading
import requests
import streamlit as st
from google_drive_auth import access_token,AuthError

class CloudError(Exception):pass
class CloudConflict(CloudError):pass

@st.cache_resource
def locks():return {},threading.Lock()

class CloudClient:
    NAME='fantasy-gm-profile-v1.json'
    def __init__(self,cfg=None):pass
    def request(self,method,path,upload=False,version=3,**kwargs):
        try:
            headers={'Authorization':'Bearer '+access_token(),**kwargs.pop('headers',{})}
            root=('https://www.googleapis.com/upload/drive/' if upload else 'https://www.googleapis.com/drive/')+'v'+str(version)+'/'
            r=requests.request(method,root+path,headers=headers,timeout=25,**kwargs)
            if r.status_code==412:raise CloudConflict('另一個裝置已更新 Drive 資料。')
            if not r.ok:raise CloudError('Google Drive 暫時無法讀寫，請確認 Drive API 與授權；尚未保存。')
            return r
        except (requests.RequestException,AuthError) as exc:raise CloudError('無法連線或 Drive 授權已失效；修改尚未保存，請重試或重新登入。') from exc
    def lookup(self):
        r=self.request('GET','files',params={'spaces':'appDataFolder','q':"name = '"+self.NAME+"' and trashed = false",'fields':'files(id,version),nextPageToken','pageSize':100}).json()
        files=r.get('files')
        if not isinstance(files,list) or r.get('nextPageToken') or len(files)>1:raise CloudError('Drive 存在多份帳號設定，已暫停寫入以免覆寫。請先下載備份並處理重複紀錄。')
        if not files:return None
        fid=files[0].get('id','')
        if not re.fullmatch(r'[A-Za-z0-9_-]+',fid):raise CloudError('Drive 檔案識別不符。')
        self.stamp=(fid,files[0].get('version'))
        return fid
    def read(self,fid,owner,for_write=False):
        # Drive v3 media omits ETag. v2 metadata exposes the validator used by v2 PUT.
        # Bracket the content read to reject a resource changed while it was downloaded.
        before=self.request('GET','files/'+fid,version=2,params={'fields':'id,etag'}).json().get('etag') if for_write else None
        r=self.request('GET','files/'+fid,params={'alt':'media'})
        if len(r.content)>4_100_000:raise CloudError('Drive 設定檔超過大小限制。')
        try:data=r.json()
        except ValueError:raise CloudError('Drive 設定檔不是有效 JSON。') from None
        if not isinstance(data,dict) or data.get('owner')!=owner or type(data.get('revision')) is not int or data['revision']<1 or not isinstance(data.get('payload'),dict):raise CloudError('Drive 設定檔歸屬或格式不符。')
        if for_write:
            after=self.request('GET','files/'+fid,version=2,params={'fields':'id,etag'}).json().get('etag')
            if before!=after:raise CloudConflict('讀取期間其他裝置已更新 Drive 資料。')
        return data,before
    def load(self,owner):
        fid=self.lookup()
        if not fid:return None
        data,_=self.read(fid,owner)
        st.session_state['_drive_profile_seen']=(owner,self.stamp)
        return data
    def load_if_changed(self,owner):
        fid=self.lookup()
        if not fid:return None
        if self.stamp[1] is not None and st.session_state.get('_drive_profile_seen')==(owner,self.stamp):return None
        data,_=self.read(fid,owner)
        st.session_state['_drive_profile_seen']=(owner,self.stamp)
        return data
    def save(self,owner,revision,payload):
        mapping,guard=locks()
        with guard:lock=mapping.setdefault(owner,threading.RLock())
        # Serializes initial creation within this deployment. Duplicate remote files fail closed.
        with lock:
            fid=self.lookup();current=0;etag=None
            if fid:
                data,etag=self.read(fid,owner,for_write=True);current=data['revision']
            if current!=revision:raise CloudConflict('另一個裝置已更新 Drive 資料。')
            body=json.dumps({'owner':owner,'revision':revision+1,'payload':payload},ensure_ascii=False).encode()
            if len(body)>4_100_000:raise CloudError('帳號資料超過大小限制，尚未保存。')
            if fid:
                if not etag:raise CloudError('Drive 未提供版本驗證，已暫停自動寫入，避免覆蓋其他裝置。')
                self.request('PUT','files/'+fid,upload=True,version=2,params={'uploadType':'media'},headers={'If-Match':etag,'Content-Type':'application/json; charset=UTF-8'},data=body)
            else:
                import uuid
                boundary='fgm_'+uuid.uuid4().hex
                meta=json.dumps({'name':self.NAME,'mimeType':'application/json','parents':['appDataFolder']}).encode()
                multipart=b'--'+boundary.encode()+b'\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n'+meta+b'\r\n--'+boundary.encode()+b'\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n'+body+b'\r\n--'+boundary.encode()+b'--\r\n'
                created=self.request('POST','files',upload=True,params={'uploadType':'multipart','fields':'id'},headers={'Content-Type':'multipart/related; boundary='+boundary},data=multipart).json()
                if not created.get('id'):raise CloudError('Drive 未確認檔案建立，請重新載入確認。')
            return revision+1
