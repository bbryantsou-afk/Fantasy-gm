"""Compact matchup schedule summaries; dates use NBA calendar days."""
import html
from datetime import timedelta

def schedule_summary(schedule, week_dates, team_ids, all_games=False):
    counts={team:sum(day in dates for day in week_dates) for team,dates in schedule.items() if team in team_ids}
    maximum=max(counts.values(),default=0)
    leaders=sorted(team for team,n in counts.items() if n==maximum and maximum)
    def logo_grid(teams):
        return '<div class="sched-cards">'+''.join(
            f'<div class="sched-card" title="{t}"><img loading="lazy" src="https://cdn.nba.com/logos/nba/{team_ids[t]}/primary/L/logo.svg" alt="{t} 隊徽"></div>' for t in teams)+'</div>'
    cards=f'<div class="sched-game-count">本週最多 <strong>{maximum} 場</strong> · {len(leaders)} 隊並列</div>'+logo_grid(leaders[:15])
    if len(leaders)>15:
        cards+=f'<details class="sched-more"><summary><span class="sched-expand">⋯ 展開其餘 {len(leaders)-15} 隊</span><span class="sched-collapse">收起</span></summary>'+logo_grid(leaders[15:])+'</details>'
    headers=''.join(f'<th>{label}<small>{day:%m/%d}</small></th>' for label,day in zip('一二三四五六日',week_dates))
    rows=[]
    for team,dates in sorted(schedule.items()):
        if team not in team_ids:
            continue
        b2b={day for day in week_dates if day in dates and (day-timedelta(days=1) in dates or day+timedelta(days=1) in dates)}
        if not b2b and not all_games:
            continue
        cells=[]
        for day in week_dates:
            if day in b2b or (all_games and day in dates):
                adjacent=[d for d in (day-timedelta(days=1),day+timedelta(days=1)) if d in dates]
                tip='、'.join(f'{min(day,d):%m/%d}–{max(day,d):%m/%d}' for d in adjacent)
                marker='✓'
                if any(d not in week_dates for d in adjacent):
                    marker+='*'
                cells.append(f'<td class="sched-b2b" title="{html.escape(tip)}">{marker}</td>')
            else:
                cells.append('<td>·</td>')
        rows.append(f'<tr><th><img src="https://cdn.nba.com/logos/nba/{team_ids[team]}/primary/L/logo.svg" alt="{team}" title="{team}"> {counts[team]} 場</th>'+''.join(cells)+'</tr>')
    calendar=('<div class="sched-calendar"><table><thead><tr><th>球隊</th>'+headers+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>') if rows else '<p>本週沒有 back-to-back。</p>'
    return cards,calendar,leaders

CSS="""<style>
.sched-game-count{font-size:12px;color:#b9c7d9;margin:0 0 6px}.sched-game-count strong{color:#74dfc4}
.sched-cards{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:4px;max-width:240px}
.sched-card{height:44px;box-sizing:border-box;display:flex;flex-direction:column;align-items:center;justify-content:center;background:rgba(23,35,56,.65);border-radius:6px;color:#edf3fb;gap:0;min-width:0}
.sched-card img{height:27px;width:30px;object-fit:contain}
.sched-card strong{font-size:9px;line-height:12px}
.sched-more{max-width:240px;margin-top:5px}.sched-more summary{cursor:pointer;color:#a9c5df;font-size:12px;padding:3px 0;list-style:none}.sched-more summary::-webkit-details-marker{display:none}.sched-more .sched-cards{margin-top:4px}.sched-collapse{display:none}.sched-more[open] .sched-expand{display:none}.sched-more[open] .sched-collapse{display:inline}
.sched-calendar{max-height:260px;overflow:auto;border:1px solid #31445b;border-radius:10px}
.sched-calendar table{border-collapse:separate;border-spacing:0;width:100%;font-size:12px;color:#edf3fb;text-align:center}
.sched-calendar thead{position:sticky;top:0;z-index:1;background:#172338}
.sched-calendar th,.sched-calendar td{padding:5px 6px;border-bottom:1px solid #243247;white-space:nowrap}
.sched-calendar th small{display:block;color:#a8bacf;font-size:10px}
.sched-calendar tbody th{text-align:left;background:#111c2d}
.sched-calendar th img{width:22px;height:22px;vertical-align:middle;margin-right:4px}
.sched-calendar td{color:#53647a}
.sched-calendar td.sched-b2b{background:#163e3b;color:#74f3c9;font-weight:700}
</style>"""
