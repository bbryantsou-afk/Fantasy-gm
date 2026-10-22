"""Weekly category score from dated starters; never use roster reference projections."""
from datetime import date
from daily_evidence import fantasy_period
from data_center import category_result
from ninecat_model import KEYS
from fantasy_schedule import week_for

def weekly_score(league, saved, team, start, end, today, live=None):
    record=saved.get('weeks',{}).get(str(start),{})
    old=record.get('teams',{}).get(team,{})
    pairing=week_for(league,start) or {}
    opponent=pairing.get('opponents',{}).get(team) or old.get('opponent')
    result={'opponent':opponent,'score':None,'status':'對手尚未同步'}
    if not opponent:return result
    if start>today:return dict(result,status='尚未開賽')
    enemy=record.get('teams',{}).get(opponent)
    if record.get('final') and enemy and old.get('totals') is not None:
        a,b=old['totals'],enemy['totals'];status='已結算'
    else:
        stats_start=max(start,date(2026,10,20))
        left,ma,_,_=fantasy_period(league,team,stats_start,end,today,live)
        right,mb,_,_=fantasy_period(league,opponent,stats_start,end,today,live)
        if not left and not right:return dict(result,status='尚無已確認先發實績')
        if (ma and not left) or (mb and not right):return dict(result,status='雙方實績尚未齊備')
        a={k:sum(p[k] for p in left) for k in KEYS}
        b={k:sum(p[k] for p in right) for k in KEYS}
        status='暫時比分 · 部分日期待同步' if ma or mb else '當週即時比分'
    cats=category_result(a,b)
    return dict(result,score=(cats.count(1),cats.count(-1),cats.count(0)),status=status)

def render_weekly_score(league,saved,team,start,end,today,live=None):
    import streamlit as st
    from roster_store import team_label
    view=weekly_score(league,saved,team,start,end,today,live)
    opponent=team_label(view['opponent']) if view['opponent'] else '對手待確認'
    score='–'.join(map(str,view['score'])) if view['score'] is not None else '—'
    st.markdown('**當週大比分　'+score+'**　'+team_label(team)+' vs '+opponent)
    st.caption(view['status']+' · 勝–敗–和（九項）')
