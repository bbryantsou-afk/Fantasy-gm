"""Portable simulator saves; no browser credentials or cached NBA responses."""
import copy,json,math
from datetime import date,timedelta
from pathlib import Path
from app_storage import private_path
FILE=Path(__file__).parent/'simulations.json'
POSITIONS={'PG','SG','G','SF','PF','F','C1','C2','UTIL1','UTIL2'}
STATS={'PTS','REB','AST','STL','BLK','3PM','FGM','FGA','FTM','FTA','TO'}

def validate_simulations(value):
    if not isinstance(value,dict) or len(value)>30 or len(json.dumps(value))>1_500_000:raise ValueError('模擬最多保存 30 組，總大小不得超過 1.5 MB。')
    for name,p in value.items():
        if not isinstance(name,str) or not 1<=len(name)<=80 or not isinstance(p,dict):raise ValueError('模擬名稱格式不符。')
        if p.get('format')!='fantasy-gm-simulation' or p.get('version')!=1:raise ValueError('模擬版本不符。')
        days=p.get('week_dates',[])
        if not isinstance(days,list) or len(days)!=7:raise ValueError('模擬日期不完整。')
        first=date.fromisoformat(days[0])
        if days!=[str(first+timedelta(days=i)) for i in range(7)]:raise ValueError('模擬日期必須連續七天。')
        if type(p.get('selected_day')) is not int or not 0<=p['selected_day']<7:raise ValueError('模擬日期選擇不符。')
        context=p.get('context',{})
        if not isinstance(context,dict) or context.get('season','2026-27') not in ['2025-26','2026-27']:raise ValueError('模擬球季不符。')
        for key in ['my_team','opp_team']:
            if key in context and (not isinstance(context[key],str) or len(context[key])>100):raise ValueError('模擬球隊不符。')
        players=p.get('players');lineups=p.get('lineups');choices=p.get('daily_choices')
        if not isinstance(players,dict) or set(players)!={'my','opp'} or not isinstance(lineups,list) or len(lineups)!=7 or not isinstance(choices,dict):raise ValueError('模擬陣容格式不符。')
        for side in ['my','opp']:
            rows=players[side]
            if not isinstance(rows,list) or len(rows)>40:raise ValueError('模擬人數不符。')
            ids=set()
            for r in rows:
                if not isinstance(r,dict) or not isinstance(r.get('id'),str) or not 1<=len(r['id'])<=140 or r['id'] in ids:raise ValueError('模擬球員 ID 不符。')
                ids.add(r['id'])
                if not isinstance(r.get('name'),str) or not 1<=len(r['name'])<=100:raise ValueError('模擬球員名稱不符。')
                if not isinstance(r.get('eligible'),list) or any(x not in ['PG','SG','SF','PF','C'] for x in r['eligible']):raise ValueError('模擬位置不符。')
            for day in lineups:
                slots=day.get(side) if isinstance(day,dict) else None
                if not isinstance(slots,dict) or set(slots)-POSITIONS:raise ValueError('先發位置不符。')
                occupied=[v for v in slots.values() if v is not None]
                if any(v not in ids for v in occupied) or len(set(occupied))!=len(occupied):raise ValueError('先發球員重複或不存在。')
            if not isinstance(choices.get(side),dict):raise ValueError('每日設定不符。')
        def check(node):
            if isinstance(node,dict):
                for k,v in node.items():
                    if k in STATS and (type(v) not in (int,float) or not math.isfinite(v) or v<0):raise ValueError('模擬數據必須為有限非負數。')
                    check(v)
                for m,a in [('FGM','FGA'),('FTM','FTA')]:
                    if m in node and a in node and node[m]>node[a]:raise ValueError('命中不得超過出手。')
            elif isinstance(node,list):
                for v in node:check(v)
        check(p)
    return copy.deepcopy(value)

def load():
    try:return validate_simulations(json.loads(private_path(FILE).read_text()))
    except (OSError,ValueError,TypeError,KeyError):return {}

def save(records):
    checked=validate_simulations(records);path=private_path(FILE)
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(checked,ensure_ascii=False));tmp.replace(path)
