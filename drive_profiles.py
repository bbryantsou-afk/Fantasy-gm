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
    def request(self,method,path,upload=False,**kwargs):
        try:
            headers={'Authorization':'Bearer '+access_token(),**kwargs.pop('headers',{})}
            root='https://www.googleapis.com/upload/drive/v3/' if upload else 'https://www.googleapis.com/drive/v3/'
            r=requests.request(method,root+path,headers=headers,timeout=25,**kwargs)
            if r.status_code==412:raise CloudConflict('另一個裝置已更新 Drive 資料。')
            if not r.ok:raise CloudError('Google Drive 暫時無法讀寫，請確認 Drive API 與授權；尚未保存。')
            return r
        except (requests.RequestException,AuthError) as exc:raise CloudError('無法連線或 Drive 授權已失效；修改尚未保存，請重試或重新登入。') from exc
    def lookup(self):
        r=self.request('GET','files',params={'spaces':'appDataFolder','q':"name = '"+self.NAME+"' and trashed = false",'fields':'files(id),nextPageToken','pageSize':100}).json()
        files=r.get('files')
        if not isinstance(files,list) or r.get('nextPageToken') or len(files)>1:raise CloudError('Drive 存在多份帳號設定，已暫停寫入以免覆寫。請先下載備份並處理重複紀錄。')
        if not files:return None
        fid=files[0].get('id','')
        if not re.fullmatch(r'[A-Za-z0-9_-]+',fid):raise CloudError('Drive 檔案識別不符。')
        return fid
    def read(self,fid,owner):
        # Get media and its ETag in the SAME response, so the validator matches these bytes.
        r=self.request('GET','files/'+fid,params={'alt':'media'})
        if len(r.content)>4_100_000:raise CloudError('Drive 設定檔超過大小限制。')
        try:data=r.json()
        except ValueError:raise CloudError('Drive 設定檔不是有效 JSON。') from None
        if not isinstance(data,dict) or data.get('owner')!=owner or type(data.get('revision')) is not int or data['revision']<1 or not isinstance(data.get('payload'),dict):raise CloudError('Drive 設定檔歸屬或格式不符。')
        return data,r.headers.get('ETag')
    def load(self,owner):
        fid=self.lookup()
        if not fid:return None
        data,_=self.read(fid,owner);return data
    def save(self,owner,revision,payload):
        mapping,guard=locks()
        with guard:lock=mapping.setdefault(owner,threading.RLock())
        # Serializes initial creation within this deployment. Duplicate remote files fail closed.
        with lock:
            fid=self.lookup();current=0;etag=None
            if fid:
                data,etag=self.read(fid,owner);current=data['revision']
            if current!=revision:raise CloudConflict('另一個裝置已更新 Drive 資料。')
            body=json.dumps({'owner':owner,'revision':revision+1,'payload':payload},ensure_ascii=False).encode()
            if len(body)>4_100_000:raise CloudError('帳號資料超過大小限制，尚未保存。')
            if fid:
                if not etag:raise CloudError('Drive 未提供版本驗證，已暫停自動寫入，避免覆蓋其他裝置。')
                self.request('PATCH','files/'+fid,upload=True,params={'uploadType':'media'},headers={'If-Match':etag,'Content-Type':'application/json; charset=UTF-8'},data=body)
            else:
                import uuid
                boundary='fgm_'+uuid.uuid4().hex
                meta=json.dumps({'name':self.NAME,'mimeType':'application/json','parents':['appDataFolder']}).encode()
                multipart=b'--'+boundary.encode()+b'\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n'+meta+b'\r\n--'+boundary.encode()+b'\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n'+body+b'\r\n--'+boundary.encode()+b'--\r\n'
                created=self.request('POST','files',upload=True,params={'uploadType':'multipart','fields':'id'},headers={'Content-Type':'multipart/related; boundary='+boundary},data=multipart).json()
                if not created.get('id'):raise CloudError('Drive 未確認檔案建立，請重新載入確認。')
            return revision+1
