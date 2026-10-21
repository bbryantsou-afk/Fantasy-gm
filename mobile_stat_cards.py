"""Wrapped nine-category player rows without horizontal scrolling."""
import html
from ninecat_model import CATS,LABELS

def trend_icon(value):
    return next((icon for icon in ['📈','📉','➖','🆕'] if icon in str(value)),'➖')

def player_rows(rows):
    out=['<div class="mobile-player-rows">']
    for row in rows:
        name=html.escape(str(row.get('球員','')))
        games=row.get('場次',row.get('GP'));games='—' if games is None else str(games)
        icon=trend_icon(row.get('週場均趨勢',''))
        out.append(f'<div class="mobile-stat-player"><div class="mobile-stat-heading"><b>{name}</b><span>{games} 場　{icon}</span></div><div class="mobile-stat-values">')
        for cat in CATS:
            label=LABELS[cat];value=row.get(label,row.get(cat))
            if value is None and cat in ('FG','FT') and row.get(cat+'A'):value=f"{row[cat+'M']/row[cat+'A']:.1%}"
            text='—' if value is None else str(value)
            out.append('<span><small>'+html.escape(label)+'</small><b>'+html.escape(text)+'</b></span>')
        out.append('</div></div>')
    return ''.join(out)+'</div>'
