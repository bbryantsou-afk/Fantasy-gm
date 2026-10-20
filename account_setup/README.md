# 個人 Google Drive 保存：管理者設定

每位使用者的紀錄存在該使用者 Google Drive 的隱藏 appDataFolder，不建立集中式帳號資料庫。
App 伺服器仍會暫時處理資料與授權；這不是端對端加密服務。

## Google Cloud

1. 建立 Google Auth Platform 品牌、支援信箱與外部使用者設定。
2. 啟用 Google Drive API。
3. 僅登記 openid、userinfo.email、userinfo.profile、drive.appdata。
4. 建立網頁 OAuth 用戶端，重新導向 URI 為 `https://fantasy-gm-bgjfjwjnxx8mbxjvajm2nk.streamlit.app/`，不是 `/oauth2callback`。
5. 測試模式需加入測試使用者。Google 授權可能到期，不能保證永久登入；公開前確認發布與驗證要求。
6. 範例的四項設定填入 Streamlit Secrets，保留既有 Yahoo 設定；實際金鑰不可提交 GitHub。

## 使用者流程

1. 在設定點「使用 Google 登入並連接個人 Drive」，確認 Google 顯示的帳號與權限。
2. 第一次登入選擇匯入這台裝置的訪客紀錄，或建立新紀錄。
3. 看到「已保存至你的 Google Drive」後，另一裝置可用同帳號登入。
4. 保存名單、IL、每日 roster、每週結果、星號、權重與偏好。
5. 頁面開啟時每 30 秒檢查 Drive 更新。Yahoo 同步仍需原本的同步入口；Google 登入不會取得 Yahoo 授權。
6. Drive 一般檔案清單看不到 App 專用資料夾。移除 App 資料會失去雲端紀錄；請保留下載備份。

## 安全與限制

- authorization-code + PKCE S256；簽章 state、10 分鐘有效、同瀏覽器 pending state 配對。
- 身分取自 Google userinfo HTTPS，使用穩定 sub 決定歸屬，不能自行指定 email 來讀別人資料。
- access token 僅在伺服器工作階段記憶體。refresh token 加密封套保存於該瀏覽器，最長 90 天；Google 可能更早撤銷。
- 加密封套仍是登入憑證，勿分享瀏覽器資料。更換 state_secret 會要求所有裝置重新登入。
- 登出清除此瀏覽器封套，不撤銷其他裝置授權。
- OAuth token 不在名單 JSON、CSV、Drive 設定檔或瀏覽器紀錄備份中。
- Drive 更新需版本條件；缺少 ETag 時停寫。初次建立在單一伺服器內鎖定，多副本若出現重複檔案則停寫提示，不自動刪檔。

## 驗收

模擬測試不等於正式 OAuth 驗收。啟用後須測試：登入、首次匯入、修改後重新整理、另一裝置還原、兩裝置衝突、登出與重新登入。Drive 條件寫入需實測，通過前不可宣稱功能完成。

官方說明：https://developers.google.com/workspace/drive/api/guides/appdata
