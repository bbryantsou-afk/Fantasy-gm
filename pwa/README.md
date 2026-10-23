# Fantasy GM PWA（獨立預覽）

這是新的手機前端與獨立 Python 服務，不使用 Streamlit 的頁面重跑／側欄元件。原本 `app.py` 與公開 Streamlit 網站保留。

## 沿用現有網站的測試入口

公開站部署此版本後，使用 `/?app=1` 開啟新介面，原入口保留舊版。此模式使用持續存在的前端元件，頁面切換不觸發 Streamlit；資料請求才透過序列化橋接呼叫既有後端。沿用原 Google 回呼設定，不需建立新的 OAuth 用戶端。Google 登入會回到新版入口；主畫面安裝資訊指向 `/?app=1`。此模式仍依賴網路，完整離線外殼由下方獨立部署提供。

## 啟動

從專案根目錄：

```sh
.venv/bin/python pwa/server.py --port 8504
```

開啟 `http://localhost:8504/`。測試手機需另行部署為手機能連線的 HTTPS 網址；手機的 localhost 指向手機本身。服務預設僅綁定本機，不自動開放網路。

## 已接入

- 固定頂欄與同位置的選單按鈕；側欄覆蓋，不推擠頁面。
- 本機切頁、球隊選擇、星號觀察、四欄球員卡與新聞。
- 九項權重與排名、交易前後比較、每週五個補強試算。
- 七日模擬、位置檢查、自動排程、命名存檔與重開。
- 過去／今天僅使用 Yahoo 每日排陣與實績；資料缺少不補預測。
- 賽程、已保存的每週對手與 H2H Each Category 結算積分。
- 現有 JSON 備份／書籤回傳網址匯入，沿用舊版紀錄格式。
- Google Drive 帳號與條件寫入 API；雲端版本不同時停止寫入。
- PWA manifest 與離線介面外殼。私密 API、OAuth 回應不進 Service Worker cache。

## Google 設定與正式部署

上方橋接模式可在現有 Streamlit 執行。若要完全移除 Streamlit 依賴，則需獨立部署這個 HTTP 服務，並設定新 Google OAuth 回呼網址。

服務會讀取 `.streamlit/secrets.toml` 的 `[google_drive]` 用戶端 ID／secret，或使用 `PWA_GOOGLE_CLIENT_ID` 與 `PWA_GOOGLE_CLIENT_SECRET` 環境變數。不要將金鑰寫進前端檔案或提交 Git。

本機測試可使用 `--base http://localhost:8504`，並將 `http://localhost:8504/auth/callback` 加入 Google OAuth 已授權重新導向 URI。正式部署設 `--base https://你的新網域`，回呼為 `https://你的新網域/auth/callback`。

預覽版登入 session 只在服務記憶體中，服務重啟後需重新登入。正式推出前需完成持久化加密 session、HTTPS 部署與 iPhone 實機 OAuth／書籤來回測試。不可宣稱已完成正式跨裝置登入驗證。

新、舊網站使用相同的 Drive 聯盟檔名與格式；請先備份再測試跨版本存檔。輸入同一 Google 帳號與聯盟 ID 才會讀取同一份紀錄。此預覽不會自動讀取或公開工作區內的私人名單檔。

## 預覽範圍

新版已有可操作的基本工作流程，但不是原版全部分析細節的等價替代。每週補強目前是空位新增試算，尚未移植完整釋出球員／禁賣品最佳化；交易頁目前為手選前後比較，尚未移植多組自動推薦；手機模擬目前是點選排陣，不包含完整自訂預測編輯器。原版仍提供這些進階功能。公開 NBA 賽季快照與已同步的 Yahoo 實績由既有模型提供，預覽不會虛構即時數據。

## 驗證

```sh
.venv/bin/python tests/verify_pwa_server.py
node tests/verify_pwa_model.cjs
.venv/bin/python tests/verify_drive_storage.py
```

測試資料僅存在測試程序與暫時預覽，不包含真實使用者名單或憑證。

正式 Google 實機驗證尚未完成；不要把模擬 HTTP 測試當作真實跨裝置登入／寫入成功。`?app=1` 測試模式提供先比較介面的入口，尚未取代原版。
