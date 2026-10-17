# Fantasy NBA GM

Streamlit 的 Fantasy NBA 9-Cat 分析工具。此版本包含球隊週總覽、球員觀察室、9-Cat 適配排名、每週補強、交易包搜尋及 v15 模擬對局。

## 本機執行
使用 Python 3.12 或更新版本：
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud
連接此儲存庫的 main 分支，入口為 app.py。Advanced settings 選 Python 3.12（或更新版本）。Yahoo 功能所需憑證由使用者在介面提供，不要提交 secrets.json、.env 或 OAuth 檔案。
依賴版本已固定為發布時驗證的版本；Python 3.12 是必要條件（部分程式使用新版 f-string 語法）。

## 資料與判讀
- 隨附 2025–26 NBA 例行賽場均及單場紀錄、2026–27 賽程快照。
- 公開選秀名單的 Fantasy 球隊名稱已改為球隊01–14；NBA球員、輪次與配置保留。它不是現行 Yahoo 所有權／自由市場。
- 預估、實績與第三方預測分開標示；模型分數不是實際勝率或對方接受交易的機率。
- 交易開季前採選秀30%＋歷史70%，本季實績按出賽樣本逐步加入。
- NBA／新聞／第三方預測可能限制雲端連線，未取得時顯示缺資料或快取，不補造實績。

## 設定保存
Mac 本機保留現有 JSON 保存方式。雲端及其他平台預設按工作階段隔離私人設定，避免匿名訪客互相覆蓋；重連、重啟或重新部署可能清空。重要名單請使用介面的下載備份。
可用 FANTASY_GM_STORAGE_MODE=local 在可信任的單人環境明確啟用本機保存；公開雲端請保留 session 模式。
私人名單、加星、非賣品、交易評語與憑證均不提交至 GitHub。

## 持續修改
本機修改不會立刻影響雲端；提交並推送 main 後，已連接 main 的 Streamlit App 才會更新。發布標籤保留可回查版本。
修改前保留分支或提交；需要穩定公開版時，可在開發分支測試後再合併 main。

本機可透過已忽略的 ninecat_assets/draft.local.json 保留原始隊名；公開版本僅附匿名 draft.json，請勿上傳本機覆寫檔。
