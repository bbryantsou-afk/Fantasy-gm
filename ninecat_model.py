"""9-Cat cohort statistics and roster-package fit; no network or state writes."""
import math
import statistics
import unicodedata

CATS = ('PTS', 'FG3M', 'REB', 'AST', 'STL', 'BLK', 'FG', 'FT', 'TOV')
KEYS = ('PTS', 'FG3M', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'FGM', 'FGA', 'FTM', 'FTA')
LABELS = dict(zip(CATS, ('PTS', '3PM', 'REB', 'AST', 'STL', 'BLK', 'FG%', 'FT%', 'TO')))


def norm(name):
    return ''.join(c for c in unicodedata.normalize('NFD', str(name)).lower() if not unicodedata.combining(c)).strip()


def player_key(player):
    pid = player.get('PLAYER_ID')
    return str(pid) if pid is not None else 'missing:' + norm(player['PLAYER_NAME'])


def roster_key(row):
    return str(row['id']) if row.get('id') is not None else 'missing:' + norm(row['name'])


def cohort_ids(players, entries, kind):
    if kind == 'draft':
        return {str(e['playerId']) for e in entries if e['playerId'] is not None}
    ids = set()
    for cat in ('PTS', 'FG3M', 'REB', 'AST', 'STL', 'BLK'):
        ids.update(str(p['PLAYER_ID']) for p in sorted(players, key=lambda p: (-p[cat], int(p['PLAYER_ID'])))[:int(kind)])
    return ids


def baseline(players, ids):
    ref = [p for p in players if str(p['PLAYER_ID']) in ids]
    if not ref:
        raise ValueError('至少需要一位有數據的參考球員。')
    out = {'n': len(ref)}
    for cat in CATS:
        if cat in ('FG', 'FT'):
            attempts = sum(p[cat + 'A'] for p in ref)
            mean = sum(p[cat + 'M'] for p in ref) / attempts if attempts else 0.0
            out[cat] = {'mean': mean, 'std': statistics.pstdev(p[cat+'M'] - mean*p[cat+'A'] for p in ref),
                        'pct_std': statistics.pstdev(p[cat+'M']/p[cat+'A'] if p[cat+'A'] else 0 for p in ref)}
        else:
            out[cat] = {'mean': statistics.mean(p[cat] for p in ref), 'std': statistics.pstdev(p[cat] for p in ref)}
    return out


def aggregate(roster, lookup):
    rows = [r for r in roster if r.get('status') == 'active' and r.get('games', 0) > 0 and str(r.get('id')) in lookup]
    return {'g': sum(r['games'] for r in rows),
            'tot': {c: sum(lookup[str(r['id'])][c]*r['games'] for r in rows) for c in KEYS}}


def value(aggregate_, cat):
    if cat in ('FG', 'FT'):
        den = aggregate_['tot'][cat+'A']
        return aggregate_['tot'][cat+'M']/den if den > 1e-12 else None
    return aggregate_['tot'][cat]/aggregate_['g'] if aggregate_['g'] > 0 else None


def gap(v, mean, cat):
    return None if v is None or mean <= 0 else (v-mean)/mean*(-1 if cat == 'TOV' else 1)


def utility(relative_gap, scale=.2):
    return 1/(1+math.exp(-max(-50, min(50, relative_gap/scale))))


def zscore(player, cat, ref):
    std = ref[cat]['std']
    if not std:
        return 0.0
    delta = player[cat+'M']-ref[cat]['mean']*player[cat+'A'] if cat in ('FG', 'FT') else player[cat]-ref[cat]['mean']
    return delta/std*(-1 if cat == 'TOV' else 1)


def weighted_z(player, ref, weights):
    den = sum(weights.get(c, 1) for c in CATS)
    return sum(zscore(player, c, ref)*weights.get(c, 1) for c in CATS)/den if den else 0.0


def bundle(roster, lookup, additions, drops, ref, weights, games=1, scale=.2):
    """Compare all removals and additions once; missing data never become zeros."""
    before = aggregate(roster, lookup)
    if not before['g']:
        return None
    kept = [r for r in roster if roster_key(r) not in set(drops)]
    unique = {player_key(p): p for p in additions}
    new = [{'id': p.get('PLAYER_ID'), 'name': p['PLAYER_NAME'], 'status': 'active',
            'games': games if p.get('PLAYER_ID') is not None else 0} for p in unique.values()]
    after = aggregate(kept + new, lookup)
    parts, total = {}, 0.0
    den = sum(weights.get(c, 1) for c in CATS) or 1
    for c in CATS:
        old_v, new_v = value(before, c), value(after, c)
        old_g, new_g = gap(old_v, ref[c]['mean'], c), gap(new_v, ref[c]['mean'], c)
        delta = 0 if old_g is None or new_g is None else 100*weights.get(c, 1)*(utility(new_g, scale)-utility(old_g, scale))/den
        parts[c] = {'before': old_v, 'after': new_v, 'before_gap': old_g, 'after_gap': new_g, 'delta': delta}
        total += delta
    return {'total': total, 'parts': parts, 'before': before, 'after': after,
            'missing': sum(p.get('PLAYER_ID') is None for p in unique.values())}


def apply_bundle(roster, additions, drops, games=1, vacancy=False):
    unique = {player_key(p): p for p in additions}
    drops = set(drops)
    keys = {roster_key(r) for r in roster}
    if not unique or not drops.issubset(keys):
        raise ValueError('加入名單為空或釋出名單已變更。')
    if not vacancy and len(unique) != len(drops):
        raise ValueError('滿員時加入與釋出人數必須相同。')
    if keys.intersection(unique):
        raise ValueError('加入名單包含已在我方球隊的球員。')
    kept = [dict(r) for r in roster if roster_key(r) not in drops]
    return kept + [{'id': str(p['PLAYER_ID']) if p.get('PLAYER_ID') is not None else None,
                    'name': p['PLAYER_NAME'], 'status': 'active', 'games': games if p.get('PLAYER_ID') is not None else 0}
                   for p in unique.values()]


def validate_backup(data):
    if not isinstance(data, dict) or data.get('version') != 2 or not isinstance(data.get('roster'), list) or not isinstance(data.get('weekHistory', []), list):
        raise ValueError('請匯入測試網站下載的 version 2 備份。')
    roster = []
    for r in data['roster']:
        if not isinstance(r, dict) or not isinstance(r.get('name'), str) or not r['name'].strip() or r.get('status') not in ('active', 'bench', 'IL'):
            raise ValueError('名單格式錯誤。')
        g = r.get('games')
        if isinstance(g, bool) or not isinstance(g, int) or not 0 <= g <= 82:
            raise ValueError('計分場次必須是0到82的整數。')
        roster.append({**r, 'id': str(r['id']) if r.get('id') is not None else None})
    if len({roster_key(r) for r in roster}) != len(roster):
        raise ValueError('名單含重複球員。')
    for w in data.get('weekHistory', []):
        vals = w.get('values', {}) if isinstance(w, dict) else {}
        if not isinstance(w, dict) or not isinstance(w.get('label'), str) or any(type(vals.get(k)) is not int or vals[k] < 0 for k in ('GP', *KEYS)) or vals['GP'] <= 0:
            raise ValueError('每週紀錄格式錯誤。')
        if vals['FGM'] > vals['FGA'] or vals['FTM'] > vals['FTA']:
            raise ValueError('命中數不能大於出手數。')
    return roster, data.get('weekHistory', [])
