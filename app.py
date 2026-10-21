
import streamlit as st
import pandas as pd
from data_provider import fetch_nba_player_stats, get_top_players_reference
from stats_engine import calculate_weighted_scores
from yahoo_auth import (
    build_authorization_url,
    exchange_code_for_token,
    yahoo_api_get,
)
from matchup_simulator_v15 import render_matchup_simulator
st.set_page_config(
    page_title="Fantasy NBA GM",
    page_icon="🏀",
    layout="wide",
)

from account_store import init_account,render_account,finish_account,poll_account,config as account_config
init_account()
from browser_records import restore_browser_records,save_browser_records
restore_browser_records()
from profile_preferences import hydrate_preferences
hydrate_preferences(st.session_state)
from mobile_share import init_share,watch_share
init_share()
watch_share()

DEMO_PLAYERS = [
    {
        "Player": "Nikola Jokic", "NBA Team": "DEN",
        "Position": "C", "Age": 31, "Experience": 11,
        "NBA Debut": 2015, "Draft Year": 2014, "Draft Pick": "41st",
        "PTS": 26.4, "REB": 12.4, "AST": 9.0,
        "STL": 1.4, "BLK": 0.8, "3PM": 1.0,
        "FG%": 0.576, "FT%": 0.823, "TO": 3.1,
    },
    {
        "Player": "Stephen Curry", "NBA Team": "GSW",
        "Position": "PG", "Age": 38, "Experience": 17,
        "NBA Debut": 2009, "Draft Year": 2009, "Draft Pick": "7th",
        "PTS": 23.4, "REB": 4.5, "AST": 6.1,
        "STL": 1.1, "BLK": 0.4, "3PM": 4.4,
        "FG%": 0.447, "FT%": 0.922, "TO": 3.0,
    },
    {
        "Player": "Jayson Tatum", "NBA Team": "BOS",
        "Position": "SF/PF", "Age": 28, "Experience": 9,
        "NBA Debut": 2017, "Draft Year": 2017, "Draft Pick": "3rd",
        "PTS": 26.9, "REB": 8.1, "AST": 4.9,
        "STL": 1.0, "BLK": 0.6, "3PM": 3.5,
        "FG%": 0.453, "FT%": 0.833, "TO": 2.9,
    },
    {
        "Player": "Tyrese Haliburton", "NBA Team": "IND",
        "Position": "PG", "Age": 26, "Experience": 6,
        "NBA Debut": 2020, "Draft Year": 2020, "Draft Pick": "12th",
        "PTS": 18.6, "REB": 3.5, "AST": 9.2,
        "STL": 1.4, "BLK": 0.7, "3PM": 2.5,
        "FG%": 0.477, "FT%": 0.859, "TO": 2.3,
    },
    {
        "Player": "Anthony Davis", "NBA Team": "DAL",
        "Position": "PF/C", "Age": 33, "Experience": 14,
        "NBA Debut": 2012, "Draft Year": 2012, "Draft Pick": "1st",
        "PTS": 24.7, "REB": 11.6, "AST": 3.5,
        "STL": 1.2, "BLK": 2.2, "3PM": 0.8,
        "FG%": 0.528, "FT%": 0.784, "TO": 2.1,
    },
]

CATEGORIES = [
    "PTS", "REB", "AST", "STL", "BLK",
    "3PM", "FG%", "FT%", "TO"
]

# 初始化示範資料，只在第一次執行時建立
if "players" not in st.session_state:
    st.session_state.players = pd.DataFrame(DEMO_PLAYERS)

players = st.session_state.players

# 深色風格
st.markdown("""
<style>
.stApp { background: #0b1020; color: #f1f5f9; }
[data-testid="stSidebar"] { background: #11182b; }
[data-testid="stMetric"] {
    background: #151e33;
    border: 1px solid #293650;
    padding: 14px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

from court_theme import render_court_theme, theme_slug, clear_oauth_query
render_court_theme()

# View belongs to this device/URL, not the cloud profile: a phone must not flip a desktop.
if 'device_view' not in st.session_state:
    requested=st.query_params.get('view')
    st.session_state['device_view']='手機版' if requested=='mobile' or (not requested and st.query_params.get('phone_sync')) else '電腦版'

with st.sidebar:
    st.title("🏀 Fantasy GM")
    if st.session_state.get("_account_id"):
        st.caption("Google 已登入 · "+st.session_state.get("_account_user_name", ""))
    elif account_config():
        from google_drive_auth import render_login
        render_login("drive_sidebar_login")
    elif st.query_params.get("phone_sync"):
        st.caption("手機同步模式")
    st.caption("PERSONAL NBA ANALYTICS")
    page = st.radio(
        "功能選單",
        ["總覽 Dashboard", "球員觀察室 Player Watch",
         "每週補強 Weekly Planner", "交易分析 Trade Lab",
     "9-Cat Strategy", "模擬對局 Matchup Simulator", "聯盟同步 League Sync", "比賽戰況", "Data Source 資料中心", "⚙️ 設定"],
        index=9 if st.query_params.get("code") or st.query_params.get("error") else 6 if st.query_params.get("phone_sync") else 0
    )
    st.divider()
    if page in ("9-Cat Strategy", "總覽 Dashboard", "模擬對局 Matchup Simulator", "Matchup Simulator Lite", "聯盟同步 League Sync", "比賽戰況", "Data Source 資料中心", "⚙️ 設定", "球員觀察室 Player Watch", "每週補強 Weekly Planner", "交易分析 Trade Lab"):
        st.caption("2025–26 場均／2026–27 期間分析")
        st.caption("本機名單分析，不會操作 Yahoo")
    else:
        st.warning("Demo Data：非即時球員數據")
        st.caption("Yahoo 帳號尚未連線")

with st.container(key='current_feature'):
    st.markdown('**'+page+'**')

with st.container(key='app_status_bar'):
    brand,display,cloud=st.columns([1.15,1.85,1.5])
    brand.markdown('**🏀 Fantasy GM**')
    with display:
        view=st.radio('顯示版本',['電腦版','手機版'],horizontal=True,key='device_view',label_visibility='collapsed')
    st.query_params['view']='mobile' if view=='手機版' else 'desktop'
    cloud.caption('☁️ Drive · v'+str(st.session_state.get('_account_revision','—')) if st.session_state.get('_account_loaded') else '☁️ 尚未連接 Drive')
    from roster_store import render_roster_source
    render_roster_source(compact=True)
if page not in ("9-Cat Strategy", "總覽 Dashboard", "模擬對局 Matchup Simulator", "Matchup Simulator Lite", "聯盟同步 League Sync", "比賽戰況", "Data Source 資料中心", "⚙️ 設定", "球員觀察室 Player Watch", "每週補強 Weekly Planner", "交易分析 Trade Lab"):
    st.info(
        "示範模式：目前資料僅用於測試網站功能，"
        "不是你的 Yahoo 球隊，也不代表最新球季統計。"
    )

from league_sync import render_sync_connection
with st.expander('同步狀態／立即更新',expanded=False):
    poll_account()
    if st.session_state.get('_account_loaded'):st.caption('同一 Google 帳號可跨裝置使用；自動檢查每 5 分鐘。手動保存立即上傳。')
    else:st.caption('到設定登入 Google，可保存個人資料並跨裝置使用。')
    if page!='聯盟同步 League Sync':render_sync_connection(full=False)
    render_roster_source()
if page=='聯盟同步 League Sync':render_sync_connection(full=True)
if page!="⚙️ 設定" and (st.session_state.get("_account_new") or st.session_state.get("_account_conflict")):
    render_account()

if page == "總覽 Dashboard":
    from dashboard_overview import render_dashboard
    render_dashboard()

elif page == "球員觀察室 Player Watch":
    from player_hub import render_watchroom
    render_watchroom()

elif page == "每週補強 Weekly Planner":
    from team_workbench import render_streaming
    render_streaming()

elif page == "交易分析 Trade Lab":
    from team_workbench import render_trades
    render_trades()

elif page == "聯盟同步 League Sync":
    from league_sync import render_sync
    render_sync()

elif page == "比賽戰況":
    from data_center import render_matchup_results
    render_matchup_results()

elif page == "Data Source 資料中心":
    from data_center import render_data_center
    render_data_center()

elif page == "⚙️ 設定":
    st.subheader('⚙️ 設定')
    render_account()
    from setup_guide import render_setup_guide
    render_setup_guide()
    from mobile_share import render_mobile_settings
    render_mobile_settings()
    from court_theme import render_theme_settings
    render_theme_settings()
    from league_settings import render_league_settings
    render_league_settings()
    st.divider()
    st.subheader("Yahoo Fantasy Sports API")
    st.write("連接你的 Yahoo Fantasy Basketball 帳號。")

    # 確認 OAuth 憑證已設定
    try:
        yahoo_config = st.secrets["yahoo"]
        client_id = yahoo_config["client_id"]
        client_secret = yahoo_config["client_secret"]
        redirect_uri = yahoo_config["redirect_uri"]
    except Exception:
        st.error(
            "找不到 Yahoo 憑證。請到 Streamlit Cloud 的 "
            "Manage app → Settings → Secrets 檢查設定。"
        )
        save_browser_records()
        finish_account()
        st.stop()

    # 初始化工作階段
    if "yahoo_oauth_state" not in st.session_state:
        st.session_state.yahoo_oauth_state = None

    if "yahoo_access_token" not in st.session_state:
        st.session_state.yahoo_access_token = None

    # 接收 Yahoo OAuth 回傳
    query_params = st.query_params
    code = query_params.get("code")
    returned_state = query_params.get("state")
    oauth_error = query_params.get("error")

    if oauth_error:
        st.error(f"Yahoo 授權未完成：{oauth_error}")
        clear_oauth_query()
        st.session_state.yahoo_oauth_state = None

    elif code:
        expected_state = st.session_state.yahoo_oauth_state

        try:
            token_data = exchange_code_for_token(
                code=code,
                returned_state=returned_state,
                expected_state=expected_state,
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
            )

            st.session_state.yahoo_access_token = token_data[
                "access_token"
            ]
            st.session_state.yahoo_oauth_state = None
            clear_oauth_query()

            st.success("Yahoo 授權完成！")

        except Exception as e:
            st.error(f"授權處理失敗：{e}")

    # 顯示連線狀態
    if st.session_state.yahoo_access_token:
        st.success("目前工作階段已取得 Yahoo Access Token。")

        if st.button("測試 Yahoo Fantasy API"):
            try:
                data = yahoo_api_get(
                    st.session_state.yahoo_access_token
                )
                st.success("Yahoo Fantasy API 回應成功！")
                st.json(data)

            except Exception as e:
                st.error(f"API 測試失敗：{e}")

        if st.button("解除目前工作階段連線"):
            st.session_state.yahoo_access_token = None
            st.session_state.yahoo_oauth_state = None
            st.rerun()

    else:
        st.info(
            "尚未連接 Yahoo。按下按鈕後，"
            "系統會導向 Yahoo 官方網站進行授權。"
        )

        if st.button("連接 Yahoo Fantasy"):
            auth_url, expected_state = build_authorization_url(
                theme=theme_slug(),
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
            )

            st.session_state.yahoo_oauth_state = expected_state

            st.link_button(
                "前往 Yahoo 授權",
                auth_url,
                type="primary",
            )

    st.caption(
        "目前 Token 僅保存在這個 Streamlit 工作階段。"
        "重新啟動或工作階段結束後，可能需要重新授權。"
    )

elif page == "9-Cat Strategy":
    from ninecat_strategy import render_ninecat_strategy
    render_ninecat_strategy()

elif page == "Matchup Simulator Lite":
    render_matchup_simulator(lite=True)

elif page == "模擬對局 Matchup Simulator":
    render_matchup_simulator(lite=view=='手機版')
st.divider()
st.caption("Fantasy NBA GM · 9-Cat 整合版" if page in ("9-Cat Strategy", "總覽 Dashboard", "模擬對局 Matchup Simulator", "Matchup Simulator Lite", "聯盟同步 League Sync", "比賽戰況", "Data Source 資料中心", "⚙️ 設定", "球員觀察室 Player Watch", "每週補強 Weekly Planner", "交易分析 Trade Lab") else "Fantasy NBA GM · Demo Version 0.2")


# Apply the selected light palette after page-specific legacy styles.
if st.session_state.get("visual_theme")=="簡約淺色":
    from light_theme import APP_CSS
    st.markdown("<style>"+APP_CSS+"</style>",unsafe_allow_html=True)

from compact_ui import render_compact_ui
render_compact_ui()
st.caption("版本 2026.10.21-ui4 · 電腦／手機共用版本")

save_browser_records()

finish_account()
