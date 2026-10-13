import pandas as pd
import streamlit as st
from nba_api.stats.endpoints import (
    leaguedashplayerstats,
    playerindex,
)

# NBA 官方統計資料的快取時間：24 小時
CACHE_SECONDS = 24 * 60 * 60


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def fetch_nba_player_stats(season="2025-26"):
    """
    取得指定球季的 NBA 例行賽球員數據，
    並嘗試合併球員位置。
    """

    response = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season,
        season_type_all_star="Regular Season",
        per_mode_detailed="PerGame",
        timeout=30,
    )

    df = response.get_data_frames()[0]

    if df.empty:
        raise ValueError(
            f"{season} 沒有取得球員統計資料。"
        )

    rename_map = {
        "PLAYER_ID": "PLAYER_ID",
        "PLAYER_NAME": "Player",
        "TEAM_ABBREVIATION": "NBA Team",
        "AGE": "Age",
        "GP": "GP",
        "MIN": "MIN",
        "PTS": "PTS",
        "REB": "REB",
        "AST": "AST",
        "STL": "STL",
        "BLK": "BLK",
        "FG3M": "3PM",
        "FG_PCT": "FG%",
        "FT_PCT": "FT%",
        "TOV": "TO",
        "FGA": "FGA",
        "FTA": "FTA",
    }

    available_columns = [
        col for col in rename_map
        if col in df.columns
    ]

    result = df[available_columns].rename(
        columns=rename_map
    ).copy()

    # 先建立預設位置，避免位置 API 失敗時整個網站出錯
    result["Position"] = "Unknown"

    # 取得球員位置，依 PLAYER_ID 合併
    if "PLAYER_ID" in result.columns:
        try:
            position_response = playerindex.PlayerIndex(
                season=season,
                league_id="00",
                timeout=30,
            )

            position_df = position_response.get_data_frames()[0]

            # 相容不同版本 NBA API 的球員 ID 欄位名稱
            if (
                "PLAYER_ID" not in position_df.columns
                and "PERSON_ID" in position_df.columns
            ):
                position_df = position_df.rename(
                    columns={"PERSON_ID": "PLAYER_ID"}
                )

            if {
                "PLAYER_ID", "POSITION"
            }.issubset(position_df.columns):

                position_df = position_df[
                    ["PLAYER_ID", "POSITION"]
                ].drop_duplicates(
                    subset=["PLAYER_ID"]
                )

                # 避免合併時 ID 型態不同
                result["PLAYER_ID"] = (
                    result["PLAYER_ID"].astype(str)
                )
                position_df["PLAYER_ID"] = (
                    position_df["PLAYER_ID"].astype(str)
                )

                result = result.drop(
                    columns=["Position"],
                    errors="ignore",
                )

                result = result.merge(
                    position_df,
                    on="PLAYER_ID",
                    how="left",
                )

                result = result.rename(
                    columns={"POSITION": "Position"}
                )

                result["Position"] = (
                    result["Position"]
                    .fillna("Unknown")
                    .astype(str)
                )

            else:
                print(
                    "NBA API 的球員位置資料缺少必要欄位。"
                )

        except Exception as e:
            print(f"球員位置資料取得失敗：{e}")

    # 部分統計欄位若缺失，補上預設值
    numeric_columns = [
        "PTS", "REB", "AST", "STL", "BLK",
        "3PM", "FG%", "FT%", "TO", "FGA", "FTA",
    ]

    for col in numeric_columns:
        if col not in result.columns:
            result[col] = 0.0

        result[col] = pd.to_numeric(
            result[col],
            errors="coerce",
        )

    result = result.dropna(subset=["Player"])
    result = result.drop_duplicates(subset=["Player"])

    # PLAYER_ID 只用於合併，不必留在前端表格
    result = result.drop(
        columns=["PLAYER_ID"],
        errors="ignore",
    )

    return (
        result.sort_values("PTS", ascending=False)
        .reset_index(drop=True)
    )


def get_top_players_reference(
    players: pd.DataFrame,
    top_n=200,
):
    """
    暫時依 PTS 建立 Top-N 參考母體。
    這不是 Yahoo 官方 9-Cat 排名。
    """

    if players.empty:
        return players.copy()

    return (
        players.sort_values("PTS", ascending=False)
        .head(top_n)
        .copy()
        .reset_index(drop=True)
    )
