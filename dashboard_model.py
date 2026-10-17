"""Weekly/daily roster production; estimates and actual totals stay separate."""
from datetime import date, datetime, timedelta
import re
from zoneinfo import ZoneInfo

from ninecat_model import CATS, KEYS, norm


def week_bounds(day):
    start = day - timedelta(days=day.weekday())
    return start, start + timedelta(days=6)


def regular_schedule(games):
    result, seen = {}, set()
    for game in games:
        gid = str(game.get('gameId', ''))
        if not gid.startswith('002') or gid in seen:
            continue
        raw = game.get('gameDateEst') or game.get('gameDateTimeEst')
        if raw:
            day = date.fromisoformat(raw[:10])
        elif game.get('gameDateTimeUTC'):
            day = datetime.fromisoformat(game['gameDateTimeUTC'].replace('Z', '+00:00')).astimezone(ZoneInfo('America/New_York')).date()
        else:
            continue
        seen.add(gid)
        for side in ('homeTeam', 'awayTeam'):
            team = game.get(side, {}).get('teamTricode')
            if team:
                result.setdefault(team, set()).add(day)
    return result, len(seen)


def draft_roster(entries, team):
    out = []
    for e in entries:
        if e['fantasyTeam'] != team:
            continue
        match = re.match(r'\((\w+)\s*-', e.get('position', ''))
        out.append({'id': str(e['playerId']) if e.get('playerId') is not None else None,
                    'name': e['name'], 'team': match.group(1) if match else '', 'status': 'active'})
    return out


def production(roster, historical, schedule, start, end, excluded=(), actual=None):
    """actual=None means estimation; actual=[] means a real empty period, never fallback."""
    by_id = {str(p['PLAYER_ID']): p for p in historical}
    by_name = {norm(p['PLAYER_NAME']): p for p in historical}
    actual_by_id = {str(p['PLAYER_ID']): p for p in actual or []}
    actual_by_name = {norm(p['PLAYER_NAME']): p for p in actual or []}
    output = []
    for r in roster:
        dates = sorted(d for d in schedule.get(r['team'], set()) if start <= d <= end)
        p = by_id.get(str(r.get('id'))) or by_name.get(norm(r['name']))
        row = {'name': r['name'], 'team': r['team'], 'dates': dates, 'excluded': r['name'] in excluded,
               'tot': dict.fromkeys(KEYS, 0.0), 'gp': 0, 'covered': False, 'reason': ''}
        if row['excluded']:
            row.update(covered=True, reason='手動排除／IL')
        elif actual is not None:
            record = actual_by_id.get(str(r.get('id'))) or actual_by_name.get(norm(r['name']))
            row.update(covered=True, reason='本期未出賽')
            if record:
                row.update(gp=int(record['GP']), tot={c: float(record.get(c, 0)) for c in KEYS}, reason='NBA實績')
        elif p is None:
            row['reason'] = '無2025–26場均；不估算'
        elif not r['team'] or r['team'] not in schedule:
            row['reason'] = '缺NBA球隊／賽程對照'
        else:
            row.update(covered=True, gp=len(dates), tot={c: p[c]*len(dates) for c in KEYS},
                       reason='上季場均×場次' if dates else '本期沒有賽程')
        output.append(row)
    return output


def totals(rows):
    return {'g': sum(r['gp'] for r in rows), 'tot': {c: sum(r['tot'][c] for r in rows) for c in KEYS}}


def mvp_scores(rows, ref):
    result = []
    for r in rows:
        if not r['covered'] or r['gp'] <= 0:
            continue
        parts = {}
        for c in CATS:
            std = ref[c]['std']
            if c in ('FG', 'FT'):
                contribution = r['tot'][c+'M'] - ref[c]['mean']*r['tot'][c+'A']
            else:
                contribution = r['tot'][c] - ref[c]['mean']*r['gp']
            parts[c] = contribution/std*(-1 if c == 'TOV' else 1) if std else 0.0
        result.append({'name': r['name'], 'gp': r['gp'], 'score': sum(parts.values())/9, 'parts': parts})
    return sorted(result, key=lambda r: (-r['score'], r['name']))


def aggregate_logs(logs, start, end):
    grouped = {}
    for g in logs:
        day = date.fromisoformat(g["GAME_DATE"][:10])
        if not start <= day <= end:
            continue
        key = str(g["PLAYER_ID"])
        r = grouped.setdefault(key, {"PLAYER_ID":g["PLAYER_ID"], "PLAYER_NAME":g["PLAYER_NAME"], "TEAM_ABBREVIATION":g["TEAM_ABBREVIATION"], "GP":0, **dict.fromkeys(KEYS,0)})
        r["GP"] += 1
        r["TEAM_ABBREVIATION"] = g["TEAM_ABBREVIATION"]
        for c in KEYS:
            r[c] += float(g.get(c) or 0)
    return list(grouped.values())

def trend(current, previous, ref):
    if current["gp"] <= 0:
        return "— 未出賽"
    if previous is None or previous["gp"] <= 0:
        return "🆕 無前週出賽"
    a = mvp_scores([current],ref)[0]["score"]/current["gp"]
    b = mvp_scores([previous],ref)[0]["score"]/previous["gp"]
    delta = a-b
    return ("📈" if delta > 0.00001 else "📉" if delta < -0.00001 else "➖") + f" {delta:+.3f}"
