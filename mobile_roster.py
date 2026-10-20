"""Browser-only mobile collection; no Yahoo credentials reach the server."""
import json
from pathlib import Path
from urllib.parse import quote
import streamlit as st
ROOT=Path(__file__).parent

def mobile_script(shared_token=None):
    target='https://fantasy-gm-bgjfjwjnxx8mbxjvajm2nk.streamlit.app/?theme=light&phone_sync=1'
    if shared_token:target+='&mobile='+quote(shared_token,safe='')
    parser=(ROOT/'browser_sync_extension/parser.js').read_text()
    code=(ROOT/'mobile_roster_sync.js').read_text().replace('__PARSER__',parser).replace('__APP_URL__',json.dumps(target))
    # Keep one line for the bookmark address while preserving statement boundaries.
    code='\n'.join(line for line in code.splitlines() if not line.strip().startswith('//'))
    return 'javascript:'+quote(code,safe="()!*'~-._")

def render_mobile_setup():
    st.markdown('### 📱 純手機同步（試用）')
    st.caption('iPhone Safari／Android Chrome：第一次設定同步書籤，之後在 Yahoo 聯盟頁點書籤即可讀取全部隊伍。全程不需要電腦，不上傳 Yahoo 帳密。')
    st.warning('尚未完成真實 iPhone／Android 測試。Yahoo 手機版頁面、瀏覽器書籤限制可能導致失敗；失敗時不覆寫名單。')
    st.markdown('#### 先確認書籤有執行')
    st.caption('如果點書籤後完全沒反應，資料尚未送出，App 內沒有另一個按鈕能補救。先把同一個書籤的網址暫時改為下方測試內容：')
    st.code("javascript:alert('Fantasy GM：書籤已執行');void(0)",language=None)
    st.markdown('在 Yahoo 網頁點這個測試書籤，應跳出「書籤已執行」。沒有跳出時，先不要貼正式同步內容。')
    a,b=st.tabs(['iPhone Safari','Android Chrome'])
    with a:st.write('使用 Safari 的「書籤」清單 → 編輯 → 點該書籤，確認改的是「位址」，不是名稱。位址必須以 javascript: 開頭。完成後回到 Yahoo 網頁，從書籤清單點它。')
    with b:st.write('使用 Chrome 的「書籤」→ 找到書籤 → 編輯，確認「網址」以 javascript: 開頭。回到 Yahoo 網頁後，在網址列輸入書籤名稱，點選顯示書籤圖示的那筆；不要把程式碼當作搜尋字詞送出。')
    with st.expander('測試有跳出視窗後：換成正式同步書籤',expanded=False):
        st.markdown('1. 用 Safari 或 Chrome 將任意頁面加入書籤，命名為「Fantasy GM 同步」。\n2. 編輯這個書籤，把網址替換成下方整段內容（包含 `javascript:`）。\n3. 在同一個瀏覽器登入 Yahoo Fantasy，開啟你的籃球聯盟頁。\n4. 從書籤清單點「Fantasy GM 同步」，保持頁面開啟，完成後會返回 App。')
        st.code(mobile_script(st.session_state.get('_mobile_share_token')),language=None)
        st.caption('只需設定一次；之後每次更新只要在 Yahoo 頁點書籤。請使用瀏覽器，不是在 Yahoo App 內執行。')
    st.caption('回傳只有隊名、球員名稱與 ID、NBA 球隊及先發／BN／IL。首次需確認隊伍配對；之後記住配對。網址片段會在接收後清除。')
