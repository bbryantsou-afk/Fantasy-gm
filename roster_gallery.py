from player_portraits import portrait_id
"""Read-only current league roster portraits."""
from html import escape

def roster_gallery(rows):
    cards=[]
    for p in rows:
        pid=portrait_id(p)
        image=f'<img loading="lazy" src="https://cdn.nba.com/headshots/nba/latest/260x190/{pid}.png" alt="">' if pid.isdigit() else '<div class="roster-photo">👤</div>'
        positions=p.get('eligible') or []
        detail=' · '.join(filter(None,[p.get('team',''),'/'.join(positions)]))
        status=' · IL' if p.get('status')=='IL' else ''
        cards.append(f'<div class="roster-person">{image}<b>{escape(p.get("name", ""))}</b><small>{escape(detail+status)}</small></div>')
    return '<div class="roster-gallery">'+''.join(cards)+'</div>'
