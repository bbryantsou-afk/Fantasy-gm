# Google 登入與永久帳號資料：管理者啟用指南

程式已提供 Google 登入、帳號隔離、永久保存、第一次匯入及版本衝突處理。
必須完成下列外部設定，才會啟用登入；尚未設定時仍可使用訪客模式。
這個功能不會取得 Yahoo 授權，Yahoo 名單仍由現有同步功能更新。

## 1. 建立 Google 登入設定

1. 在你自己的 Google Cloud 專案開啟 Google Auth Platform。
2. 設定 Branding（App 名稱、支援信箱）與 Audience。
3. 開發測試階段加入測試使用者；正式提供其他人使用前，依 Google 的要求發布應用程式。
4. 建立 OAuth Client，類型選 Web application。
5. Authorized redirect URIs 加入以下完整網址：

   `https://fantasy-gm-bgjfjwjnxx8mbxjvajm2nk.streamlit.app/oauth2callback`

6. 留存 Client ID、Client secret，僅填入 Streamlit Secrets，不要貼聊天或放進 GitHub。
7. 此登入只需要基本身分，不申請 Gmail、Drive 或其他 Google 資料權限。

## 2. 建立永久資料庫

1. 在自己的 Supabase 帳號建立專案，確認所選方案與費用。
2. 開啟 SQL Editor，執行本目錄的 `schema.sql`。
3. 留存 Project URL 和伺服器使用的 Secret key。舊版 service_role key 也支援。
4. 不可使用 publishable／anon key 取代伺服器金鑰；資料表與寫入函式不授權匿名或直接瀏覽器存取。
5. 須開啟 Supabase Data API，公開 schema 為 `public`。資料表已開 RLS，未建立公開讀寫政策；只有伺服器角色可操作。

## 3. 設定正式網站

1. Streamlit Cloud → 本 App → Settings → Secrets。
2. 保留既有 Yahoo 設定，依 `secrets.example.toml` 加入 `[auth]`、`[auth.google]`、`[account_db]`。
3. Cookie secret 使用足夠長的隨機值。可在自己的 Terminal 執行：

   `python3 -c 'import secrets; print(secrets.token_urlsafe(48))'`

4. 實際 Secrets 不可提交 GitHub。儲存後重新啟動 App，讓套件與登入設定生效。
5. 設定頁會出現「使用 Google 登入」。尚未填好時會明確顯示未啟用。

## 4. 首次使用者測試

1. 先在未登入模式完成 Yahoo 同步，確認畫面下方顯示瀏覽器已保存紀錄。
2. 使用 Google 登入。若帳號尚無雲端資料，確認預覽後選「匯入此裝置既有紀錄」。也可選「建立新的帳號紀錄」。
3. 等畫面顯示「帳號紀錄已保存至雲端」。
4. 換另一個瀏覽器或手機，以相同 Google 帳號登入，核對名單、IL、星號、權重及比賽紀錄。
5. 換另一個 Google 帳號登入，應看不到第一個帳號資料。
6. 兩裝置同時修改時，舊版本不能覆寫新版本；設定頁可下載待處理資料，選擇載入雲端或明確保留本裝置版本。
7. 網路失敗時不得顯示雲端已保存。請恢復網路後重試，或先下載備份。

## 保存範圍與限制

- 名單、每日 roster、每週結果、當日數據、加星名單、9-Cat 權重、主題、選定球隊、交易偏好及回饋。
- 使用經驗證的 Google `sub` 計算帳號識別，不使用前端傳入的 email 或帳號 ID 決定資料歸屬。
- Google 密碼、OAuth token、Yahoo token、API 金鑰均不在帳號備份中。
- 登入後以帳號資料為主，不會自動將舊共用連結資料覆寫到帳號。
- 每次互動後保存變更，其他裝置頁面開啟時每 30 秒檢查更新。這不會讓 Yahoo 在電腦關機後自動同步。
- 永久資料保存在 Supabase，不依賴 Streamlit 暫存磁碟；仍應依資料庫方案做好備份與維護。
- 尚未使用真實憑證完成 Google OAuth 與正式資料庫端對端測試，啟用後需完成上述驗收。

官方參考：
- https://docs.streamlit.io/develop/tutorials/authentication/google
- https://docs.streamlit.io/develop/concepts/connections/authentication
- https://supabase.com/docs/guides/database/functions
- https://supabase.com/docs/guides/database/postgres/row-level-security
