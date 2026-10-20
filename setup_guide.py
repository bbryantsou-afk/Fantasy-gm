"""New-user setup instructions using production sync, without test bookmarks."""
import streamlit as st

def render_setup_guide():
    st.markdown('### 📖 第一次使用 · 設定指南')
    desktop,phone=st.tabs(['手機＋電腦','純手機'])
    with desktop:
        st.markdown('**電腦與手機登入同一 Google 帳號，資料自動同步。**')
        st.markdown('''
1. 電腦使用 Chrome 開啟本網站，在「設定」登入 Google；首次選擇匯入既有紀錄或建立紀錄。
2. 進入「聯盟同步 → 首次安裝／同步說明」。
3. 下載擴充功能 ZIP 並解壓縮。
4. Chrome 開啟 `chrome://extensions`，開啟「開發人員模式」，按「載入未封裝項目」，選取含 `manifest.json` 的資料夾。
5. 在同一個 Chrome 登入 Yahoo Fantasy，再回網站重新整理。
6. 在「聯盟同步」選今天的美東日期，按「同步指定日期」。首次核對隊伍配對並確認名單與 IL。
7. 確認畫面顯示「已保存至你的 Google Drive」。
8. 手機開啟同一網站，登入相同 Google 帳號，即可載入紀錄。兩端都可自行保存變更。
''')
        st.info('星號、權重及名單保存後，另一端開著網站時每 5 秒檢查 Drive 更新。電腦關閉不影響手機讀寫 Drive；但 Yahoo 最新名單需由運作中的電腦擴充功能或手機同步書籤取得。')
    with phone:
        st.markdown('**手機自己同步，不需要電腦。手機瀏覽器同步仍為試用功能。**')
        st.markdown('''
1. 用手機 Safari／Chrome 開啟網站，在「設定」登入 Google；首次匯入既有紀錄或建立紀錄。
2. 進入「聯盟同步 → 手機直接同步（不需電腦）」。
3. 展開「設定正式同步書籤」，複製正式同步內容。
4. 在瀏覽器新增書籤，命名為「Fantasy GM 同步」；編輯該書籤的網址／位址，貼上正式同步內容，保留開頭的 `javascript:`。
5. 在同一瀏覽器的當前分頁登入 Yahoo Fantasy，開啟自己的籃球聯盟頁。
6. 執行同步書籤，保持頁面開啟，等讀取完成並自動返回 App。
7. 首次確認隊伍配對並核對名單與 IL，確認「已保存至你的 Google Drive」。
8. 日常收藏一般網站入口；換裝置時登入同一 Google 帳號即可。
''')
        st.caption('Safari：從書籤清單直接點。Chrome：在 Yahoo 分頁的網址列輸入書籤名稱，選有書籤圖示的結果。必須在 Yahoo 網頁執行，不是在本 App、搜尋頁或 Yahoo App 裡執行。')
        st.info('星號與分析設定會自動保存並同步；要取得 Yahoo 新名單，回 Yahoo 聯盟頁點同步書籤。手機鎖定或網站在背景時，跨裝置檢查可能暫停，回到網站後恢復。')

    st.caption('Google 保存與 Yahoo 抓取是兩件事：Drive 讓裝置共用已保存資料；Yahoo 同步負責取得最新聯盟名單。建議仍定期下載備份。')
