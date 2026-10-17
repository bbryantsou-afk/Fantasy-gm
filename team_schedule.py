import json
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

NBA_TZ = ZoneInfo("America/New_York")


def load_team_schedule():
    path = Path(__file__).parent / "nba_schedule_2026_27.json"

    games = json.loads(path.read_text(encoding="utf-8"))

    schedule = {}

    for game in games:
        utc = game.get("gameDateTimeUTC")

        if not utc:
            continue

        dt = datetime.fromisoformat(
            utc.replace("Z", "+00:00")
        )

        game_date = dt.astimezone(NBA_TZ).date()

        for side in ("homeTeam", "awayTeam"):
            team = game.get(side, {}).get("teamTricode")

            if team:
                schedule.setdefault(team, set()).add(game_date)

    return schedule


def get_game_status(team, selected_date, schedule):
    if isinstance(selected_date, str):
        selected_date = date.fromisoformat(selected_date)

    team = team.upper()
    dates = schedule.get(team, set())

    if selected_date not in dates:
        return "OFF"

    yesterday = selected_date - timedelta(days=1)
    tomorrow = selected_date + timedelta(days=1)

    if yesterday in dates or tomorrow in dates:
        return "B2B"

    return "GAME"


if __name__ == "__main__":
    schedule = load_team_schedule()

    selected = date(2026, 10, 20)

    print("Yahoo 比賽日期：", selected)
    print()

    for team in ("BOS", "DET", "DEN", "GSW", "LAL"):
        print(team, "→", get_game_status(team, selected, schedule))
