"""Short first-time setup; optional explanation stays closed."""
import streamlit as st

def render_setup_guide():
    with st.expander('開始使用',expanded=False):
        labels=['純手機','手機＋電腦'] if st.session_state.get('device_view')=='手機版' else ['手機＋電腦','純手機']
        for label,tab in zip(labels,st.tabs(labels)):
            with tab:
                if label=='純手機':
                    st.markdown('''1. 在 App 與手機瀏覽器登入同一 Google 帳號。
2. 展開下方「手機書籤」，複製同步書籤。
3. 新增「Fantasy GM 同步」書籤，把網址換成複製的內容，保留 `javascript:`。
4. 在同一瀏覽器開啟 Yahoo 聯盟，執行書籤並選日期。
5. 首次確認配對，等資料保存至 Drive；回 App 按 **Y** 讀取。''')
                else:
                    st.markdown('''1. 電腦與手機登入同一 Google 帳號。
2. 展開下方「電腦安裝」，下載並解壓縮擴充功能。
3. Chrome 開啟 `chrome://extensions`，啟用「開發人員模式」，選「載入未封裝項目」；選取含 `manifest.json` 的資料夾。
4. 同一 Chrome 登入 Yahoo，回 App 按 **Y**。首次確認配對。
5. 手機 App 按 **Y** 讀取 Drive 最新紀錄。''')
        with st.expander('操作說明',expanded=False):
            st.caption('Safari：從書籤清單執行。Chrome：在 Yahoo 分頁的網址列輸入書籤名稱，選帶書籤圖示的結果。')
            st.caption('電腦開啟自動同步後每 5 分鐘讀取 Yahoo；純手機需執行書籤。Drive 共用已保存紀錄，App 在前景時每 5 分鐘檢查。')
            st.caption('首次配對後會記住隊伍。日期採美東比賽日。保存失敗或配對有誤時，請先處理提示。')
