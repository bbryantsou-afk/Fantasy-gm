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
4. 保存名單、IL、每日 roster、Yahoo 每週對手排程、每週結果、星號、權重、交易偏好與評語。模擬器按「儲存模擬」後，雙方七日先發、每日來源、自訂預測與模擬新增球員也保存；電腦與 Lite 共用。未按儲存的編輯不會上傳。
5. 頁面開啟時每 5 秒檢查 Drive 更新，選取或移除星號後自動保存；手機在背景或鎖定時可能暫停。Yahoo 同步仍需原本的同步入口；Google 登入不會取得 Yahoo 授權。
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

2026-10-20 正式網站已實測：Google 授權、首次匯入個人 Drive、重新整理恢復登入與紀錄、PTS 權重 1→1.1 寫回、新分頁還原 1.1、改回 1 並由原分頁自動載入。測試後權重已還原。

版本條件使用 Drive v2 metadata 的 etag；下載前後驗證未改變，再以帶 If-Match 的 v2 PUT 更新。缺少驗證資訊時不寫入。

帳號隔離、過期與偽造 state、PKCE、封套加密、版本衝突、讀取競態、網路失敗與瀏覽器登出均通過模擬測試；實體 iPhone／Android 跨裝置及同時寫入衝突仍需實機驗收。目前 Google 專案是測試模式，只有已加入的測試帳號能登入，尚未向所有使用者開放。

官方說明：https://developers.google.com/workspace/drive/api/guides/appdata
