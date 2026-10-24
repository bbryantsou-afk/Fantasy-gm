"""Weekly category score from dated starters; never use roster reference projections."""
from datetime import date
from daily_evidence import fantasy_period,timestamp
from data_center import category_result
from ninecat_model import KEYS
from fantasy_schedule import week_for

def weekly_score(league, saved, team, start, end, today, live=None):
    record=saved.get('weeks',{}).get(str(start),{})
    incoming=league.get('yahoo_matchups',{}).get(str(start),{})
    if incoming.get('source')=='Yahoo 官方對局總表' and timestamp(incoming.get('updated_at',''))>timestamp(record.get('updated_at','')):
        record=incoming

    old=record.get('teams',{}).get(team,{})
    pairing=week_for(league,start) or week_for(league,end) or {}
    opponent=pairing.get('opponents',{}).get(team) or old.get('opponent')
    result={'opponent':opponent,'score':None,'status':'對手尚未同步'}
    if not opponent:return result
    if start>today:return dict(result,status='尚未開賽')
    enemy=record.get('teams',{}).get(opponent)
    if (record.get('final') or record.get('source')=='Yahoo 官方對局總表') and enemy and old.get('totals') is not None:
        a,b=old['totals'],enemy['totals'];status=('Yahoo 官方週比分（週已結束）' if record.get('source')=='Yahoo 官方對局總表' else '已結算') if record.get('final') else 'Yahoo 官方即時比分'
    else:
        stats_start=max(start,date(2026,10,20))
        left,ma,_,_=fantasy_period(league,team,stats_start,end,today,live)
        right,mb,_,_=fantasy_period(league,opponent,stats_start,end,today,live)
        if not left and not right:return dict(result,status='尚無已確認先發實績')
        if (ma and not left) or (mb and not right):return dict(result,status='雙方實績尚未齊備')
        a={k:sum(p[k] for p in left) for k in KEYS}
        b={k:sum(p[k] for p in right) for k in KEYS}
        status='暫時比分 · 部分日期待同步' if ma or mb else '當週即時比分'
    if not record.get('final') and record.get('source')=='Yahoo 官方對局總表':
        # A newer complete daily collection supersedes an older weekly snapshot.
        left,ma,_,sa=fantasy_period(league,team,max(start,date(2026,10,20)),end,today,live)
        right,mb,_,sb=fantasy_period(league,opponent,max(start,date(2026,10,20)),end,today,live)
        stamp=timestamp(record.get('updated_at',''))
        if left and right and not ma and not mb and min(timestamp(sa),timestamp(sb))>stamp:
            a={k:sum(p[k] for p in left) for k in KEYS}
            b={k:sum(p[k] for p in right) for k in KEYS}
            status='最新完整排陣實績比分'
        else:
            status='Yahoo 已保存比分 · '+str(record.get('updated_at',''))
    cats=category_result(a,b)
    return dict(result,score=(cats.count(1),cats.count(-1),cats.count(0)),status=status)

def render_weekly_score(league,saved,team,start,end,today,live=None):
    import streamlit as st
    from roster_store import team_label
    view=weekly_score(league,saved,team,start,end,today,live)
    import html
    opponent=team_label(view['opponent']) if view['opponent'] else '—'
    own,other=(view['score'][:2] if view['score'] is not None else ('—','—'))
    light=st.session_state.get('visual_theme')=='簡約淺色'
    blue,purple=('#236a9a','#79509a') if light else ('#7cc7ff','#d5a0ff')
    st.markdown(f'<div class="dashboard-big-score" aria-label="{html.escape(view["status"],quote=True)}"><div class="dashboard-score-numbers"><strong style="color:{blue}">{own}</strong><span>—</span><strong style="color:{purple}">{other}</strong></div><div class="dashboard-score-opponent">vs {html.escape(opponent)}</div></div>',unsafe_allow_html=True)
    if view['score'] is not None and view['status'].startswith('Yahoo 已保存比分'):
        st.caption(view['status'])
