"""Wrapped nine-category player rows without horizontal scrolling."""
import html
import json
from functools import lru_cache
from pathlib import Path
from ninecat_model import CATS,LABELS

@lru_cache(maxsize=1)
def portraits():
    rows=json.loads((Path(__file__).parent/'ninecat_assets/data.json').read_text())['players']
    return {p['PLAYER_NAME']:str(p['PLAYER_ID']) for p in rows}

def trend_icon(value):
    return next((icon for icon in ['📈','📉','➖','🆕'] if icon in str(value)),'➖')

def player_rows(rows):
    out=['<div class="mobile-player-rows">']
    for row in rows:
        raw_name=str(row.get('球員',''));name=html.escape(raw_name)
        pid=str(row.get('_nba_id') or portraits().get(raw_name,''))
        photo=f'<img loading="lazy" src="https://cdn.nba.com/headshots/nba/latest/260x190/{pid}.png" alt="{name}">' if pid.isdigit() else '<span class="mobile-stat-avatar">🏀</span>'
        games=row.get('場次',row.get('GP'));games='—' if games is None else str(games)
        icon=trend_icon(row.get('週場均趨勢',''))
        out.append(f'<div class="mobile-stat-player"><div class="mobile-stat-heading">{photo}<b>{name}</b><span>{games} 場　{icon}</span></div><div class="mobile-stat-values">')
        for cat in CATS:
            label=LABELS[cat];value=row.get(label,row.get(cat))
            if value is None and cat in ('FG','FT') and row.get(cat+'A'):value=f"{row[cat+'M']/row[cat+'A']:.1%}"
            text='—' if value is None else f'{value:g}' if isinstance(value,(int,float)) else str(value)
            out.append('<span><small>'+html.escape(label)+'</small><b>'+html.escape(text)+'</b></span>')
        out.append('</div></div>')
    return ''.join(out)+'</div>'
