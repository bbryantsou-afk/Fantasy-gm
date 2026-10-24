"""Official displayed Yahoo score only; player/live totals never determine this score."""
from daily_evidence import timestamp
from fantasy_schedule import week_for

def weekly_score(league, saved, team, start, end, today, live=None):
    candidates=[league.get('yahoo_matchups',{}).get(str(start),{}),saved.get('weeks',{}).get(str(start),{})]
    candidates=[r for r in candidates if r.get('source')=='Yahoo 官方對局總表']
    record=max(candidates,key=lambda r:timestamp(r.get('updated_at','')),default={})
    own=record.get('teams',{}).get(team,{})
    pairing=week_for(league,start) or week_for(league,end) or {}
    opponent=own.get('opponent') or pairing.get('opponents',{}).get(team)
    result={'opponent':opponent,'score':None,'status':'尚未取得 Yahoo 官方比分，請按 Y 更新'}
    if start>today:return dict(result,status='尚未開賽')
    enemy=record.get('teams',{}).get(opponent,{})
    a,b=own.get('score'),enemy.get('score')
    if enemy.get('opponent')!=team or type(a) is not int or type(b) is not int or not 0<=a<=9 or not 0<=b<=9 or a+b>9:return result
    return dict(result,score=(a,b,9-a-b),status='Yahoo 已保存比分 · '+str(record.get('updated_at','')))

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
