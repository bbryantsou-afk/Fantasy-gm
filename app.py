
import streamlit as st
import pandas as pd
from data_provider import fetch_nba_player_stats, get_top_players_reference
from stats_engine import calculate_weighted_scores

st.set_page_config(
    page_title="Fantasy NBA GM",
    page_icon="🏀",
    layout="wide",
)

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

with st.sidebar:
    st.title("🏀 Fantasy GM")
    st.caption("PERSONAL NBA ANALYTICS")
    page = st.radio(
        "功能選單",
        ["總覽 Dashboard", "球員名單 Roster",
         "球員比較 Player Compare", "Yahoo API 設定",
     "9-Cat Strategy"]
    )
    st.divider()
    st.warning("Demo Data：非即時球員數據")
    st.caption("Yahoo 帳號尚未連線")

st.title("🏀 NBA Fantasy General Manager")
st.caption("球隊管理 · 球員資料 · 9-category 分析")
st.info(
    "示範模式：目前資料僅用於測試網站功能，"
    "不是你的 Yahoo 球隊，也不代表最新球季統計。"
)

if page == "總覽 Dashboard":
    st.subheader("Team Overview")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("示範球員數", len(players))
    c2.metric("平均 PTS", f"{players['PTS'].mean():.1f}")
    c3.metric("平均 REB", f"{players['REB'].mean():.1f}")
    c4.metric("平均 AST", f"{players['AST'].mean():.1f}")

    st.subheader("球員數據")
    st.dataframe(
        players[["Player", "NBA Team", "Position",
                 "PTS", "REB", "AST", "STL", "BLK"]],
        hide_index=True,
        use_container_width=True,
    )

    st.subheader("9-Cat 數據分布")
    st.bar_chart(players.set_index("Player")[["PTS", "REB", "AST"]])

elif page == "球員名單 Roster":
    st.subheader("Player Database")
    st.write("你可以直接編輯表格中的資料；修改只保存在目前的工作階段。")

    edited = st.data_editor(
        players,
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        key="roster_editor",
    )
    st.session_state.players = edited
    players = edited

    st.caption(
        "注意：重新啟動程式後，這些編輯可能會消失。"
        "後續會加入本機檔案儲存。"
    )

    if len(players) > 0:
        names = players["Player"].fillna("").astype(str).tolist()
        selected = st.selectbox("查看球員背景", names)
        matches = players[players["Player"].astype(str) == selected]

        if not matches.empty:
            p = matches.iloc[0]
            st.subheader(selected)
            a, b, c, d = st.columns(4)
            a.metric("年齡", str(p["Age"]))
            b.metric("NBA 資歷", f"{p['Experience']} 年")
            c.metric("NBA 首秀", str(p["NBA Debut"]))
            d.metric("選秀年份", str(p["Draft Year"]))

            st.write(
                f"**NBA 球隊：** {p['NBA Team']}　"
                f"**位置：** {p['Position']}　"
                f"**選秀順位：** {p['Draft Pick']}"
            )

elif page == "球員比較 Player Compare":
    st.subheader("⚖️ 9-Cat Player Comparison")
    st.write("選擇兩位球員，逐項比較九類 Fantasy 數據。")

    if len(players) < 2:
        st.warning("請先在球員名單新增至少兩位球員。")
    else:
        names = players["Player"].fillna("").astype(str).tolist()
        col1, col2 = st.columns(2)

        with col1:
            player_a = st.selectbox("球員 A", names, index=0)
        with col2:
            default_b = min(1, len(names) - 1)
            player_b = st.selectbox("球員 B", names, index=default_b)

        if player_a == player_b:
            st.warning("請選擇兩位不同的球員。")
        else:
            a = players[players["Player"].astype(str) == player_a].iloc[0]
            b = players[players["Player"].astype(str) == player_b].iloc[0]

            st.markdown(f"### {player_a}  vs  {player_b}")

            comparison = pd.DataFrame({
                "Category": CATEGORIES,
                player_a: [a[c] for c in CATEGORIES],
                player_b: [b[c] for c in CATEGORIES],
            })

            comparison["Difference (A-B)"] = [
                float(a[c]) - float(b[c]) for c in CATEGORIES
            ]

            def format_cat(cat, value):
                if cat in ["FG%", "FT%"]:
                    return f"{float(value):.1%}"
                return f"{float(value):.2f}"

            display = comparison.copy()
            for cat in CATEGORIES:
                display.loc[display["Category"] == cat, player_a] = (
                    display.loc[display["Category"] == cat, player_a]
                    .apply(lambda v: format_cat(cat, v))
                )
                display.loc[display["Category"] == cat, player_b] = (
                    display.loc[display["Category"] == cat, player_b]
                    .apply(lambda v: format_cat(cat, v))
                )

            display["Difference (A-B)"] = [
                format_cat(cat, a[cat] - b[cat]) if cat not in ["FG%", "FT%"]
                else f"{(float(a[cat]) - float(b[cat])) * 100:+.1f} percentage points"
                for cat in CATEGORIES
            ]

            st.dataframe(display, hide_index=True, use_container_width=True)

            st.subheader("數據視覺化")
            chosen_cat = st.selectbox("選擇比較項目", CATEGORIES)
            chart = pd.DataFrame({
                "Player": [player_a, player_b],
                chosen_cat: [a[chosen_cat], b[chosen_cat]]
            }).set_index("Player")
            st.bar_chart(chart)

            st.info(
                "這是單項數據比較，不是完整的 Fantasy 勝負預測。"
                "FG% 和 FT% 會受出手量影響；TO 在 9-cat 通常越低越好。"
                "正式版將加入出賽量、聯盟排名與 Z-score。"
            )

elif page == "Yahoo API 設定":
    st.subheader("Yahoo Fantasy Sports API")
    st.write("目前尚未連接 Yahoo 官方 API。")
    st.markdown("""
    後續整合步驟：

    1. 申請 Yahoo Developer 應用程式。
    2. 設定 OAuth 2.0 授權。
    3. 取得已授權的聯盟與主要球隊。
    4. 同步真實球員名單與統計資料。
    5. 補齊球員年齡、NBA 資歷、首秀及選秀資料。
    """)
    st.warning(
        "不要把 Yahoo 密碼、Client Secret 或 Access Token "
        "直接貼進程式碼或聊天訊息。"
    )
elif page == "9-Cat Strategy":
    st.title("🏀 9-Cat Strategy")
    st.caption("調整九項數據的權重，找出符合你球隊策略的球員。")

    players = st.session_state.players.copy()
    
    data_mode = st.radio(
        "球員資料來源",
        ["NBA 真實統計", "示範資料"],
        horizontal=True,
        key="strategy_data_mode"
    )

    reference_df = None

    if data_mode == "NBA 真實統計":
        st.caption("資料期間：2025–26 NBA 例行賽完整球季")

        if st.button("🔄 重新抓取 NBA 資料"):
            st.cache_data.clear()

        try:
            with st.spinner("正在取得 NBA 球員統計，請稍候..."):
                players = fetch_nba_player_stats("2025-26")

            if players.empty:
                st.warning("目前沒有取得球員資料。")
            else:
                reference_df = get_top_players_reference(
                    players,
                    top_n=200
                )

                st.success(
                    f"已取得 {len(players)} 位球員，"
                    f"參考母體有 {len(reference_df)} 位球員。"
                )

                st.caption(
                    "目前 Top-200 暫時依 PTS 排序，"
                    "並非 Yahoo 官方排名或正式 Fantasy 排名。"
                )

        except Exception as e:
            players = pd.DataFrame()
            st.error(f"NBA 資料取得失敗：{e}")
            st.info(
                "可以暫時切換到「示範資料」，"
                "或稍後重新抓取。"
            )

    else:
        players = st.session_state.players.copy()
        reference_df = None
        st.info("目前使用示範資料，不代表真實球員排名。")

    st.subheader("1. 設定你的球隊策略")
    st.write(
        "權重 0 代表不重視此項數據；"
        "權重 1 代表一般重視；"
        "權重 2 代表高度重視。"
    )

    categories = [
        "PTS", "REB", "AST", "STL", "BLK",
        "3PM", "FG%", "FT%", "TO"
    ]

    weights = {}
    cols = st.columns(3)

    for i, cat in enumerate(categories):
        with cols[i % 3]:
            weights[cat] = st.slider(
                f"{cat} 權重",
                min_value=0.0,
                max_value=2.0,
                value=1.0,
                step=0.1,
                key=f"strategy_weight_{cat}"
            )

    st.divider()
    st.subheader("2. 球員策略排名")

    if players.empty:
        st.warning("目前沒有球員資料，請先到 Roster 新增球員。")
    else:
        try:
            ranked = calculate_weighted_scores(
                players=players,
                weights=weights,
	        reference=reference_df
            )
            
            st.subheader("🔎 球員篩選")

            filter_col1, filter_col2 = st.columns(2)

            with filter_col1:
                min_gp = st.number_input(
                    "最低出賽場次（GP）",
                    min_value=0,
                    max_value=82,
                    value=30,
                    step=1,
                    key="strategy_min_gp",
                )

            with filter_col2:
                POSITION_OPTIONS = ["PG", "SG", "G", "PF", "SF", "F", "C"]

                if "strategy_positions" not in st.session_state:
                    st.session_state.strategy_positions = POSITION_OPTIONS.copy()

                st.markdown("#### 🏀 指定球員位置")
                st.caption("再次點擊已選位置即可取消")

                guard_col, forward_col, center_col = st.columns(3, gap="small")

                def position_button(position, container):
                    selected = position in st.session_state.strategy_positions

                    if container.button(
                        f"{'✓ ' if selected else ''}{position}",
                        key=f"position_toggle_{position}",
                        type="primary" if selected else "secondary",
                        use_container_width=True,
                    ):
                        if selected:
                            st.session_state.strategy_positions.remove(position)
                        else:
                            st.session_state.strategy_positions.append(position)

                        st.rerun()

                # 後衛：PG、SG 在上，G 在下
                with guard_col:
                    pg_col, sg_col = st.columns(2, gap="small")
                    position_button("PG", pg_col)
                    position_button("SG", sg_col)
                    position_button("G", st.container())

                # 前鋒：PF、SF 在上，F 在下
                with forward_col:
                    pf_col, sf_col = st.columns(2, gap="small")
                    position_button("PF", pf_col)
                    position_button("SF", sf_col)
                    position_button("F", st.container())

                # 中鋒
                with center_col:
                    position_button("C", st.container())

                selected_positions = st.session_state.strategy_positions

                # 先依最低出賽場次篩選
                if "GP" in ranked.columns:
                    ranked["GP"] = pd.to_numeric(
                        ranked["GP"], errors="coerce"
                    )
                    ranked = ranked[ranked["GP"] >= min_gp]
                else:
                    st.warning(
                        "目前球員資料缺少 GP 欄位，無法依出賽場次篩選。"
                    )

                # 再依 Yahoo 位置資格篩選
                if selected_positions:
                    if "Position" in ranked.columns:

                        def position_matches(position):
                            if pd.isna(position):
                                return False

                            raw_positions = (
                                str(position)
                                .upper()
                                .replace("/", ",")
                                .replace("|", ",")
                                .replace("-", ",")
                            )

                            player_positions = {
                                p.strip()
                                for p in raw_positions.split(",")
                                if p.strip() in {"PG", "SG", "SF", "PF", "C"}
                            }

                            eligible_positions = set(player_positions)

                            if player_positions.intersection({"PG", "SG"}):
                                eligible_positions.add("G")

                            if player_positions.intersection({"SF", "PF"}):
                                eligible_positions.add("F")

                            return bool(
                                eligible_positions.intersection(
                                    selected_positions
                                )
                            )

                        ranked = ranked[
                            ranked["Position"].apply(position_matches)
                        ]

                    else:
                        st.warning(
                            "目前球員資料尚無 Position 欄位，無法依位置篩選。"
                        )
                else:
                    ranked = ranked.iloc[0:0]

                      

            st.caption(f"符合條件的球員：{len(ranked)} 位")

            display_columns = [
                col for col in [
                    "Player", "NBA Team", "Position",
                    "PTS", "REB", "AST", "STL", "BLK",
                    "3PM", "FG%", "FT%", "TO",
                    "PTS Z", "REB Z", "AST Z",
                    "STL Z", "BLK Z", "3PM Z",
                    "FG% Z", "FT% Z", "TO Z",
                    "Weighted Z"
                ]
                if col in ranked.columns
            ]

            st.dataframe(
                ranked[display_columns],
                hide_index=True,
                width="stretch"
            )

            if "Weighted Z" in ranked.columns:
                best = ranked.iloc[0]

                st.success(
                    f"目前策略下的最高分球員："
                    f"{best['Player']} "
                    f"（Weighted Z = {best['Weighted Z']:.2f}）"
                )

            st.info(
                "目前使用示範球員作為計算基準。"
                "正式版本會改用 Yahoo Top-200 球員的平均值與標準差，"
                "並加入同位置比較及 FG%／FT% 出手量影響。"
            )

        except Exception as e:
            st.error(f"計算失敗：{e}")
            
st.divider()
st.caption("Fantasy NBA GM · Demo Version 0.2")

