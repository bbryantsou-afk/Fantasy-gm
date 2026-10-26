"""Daily roster and rotation slots, team schedule priority, then category/player simulation."""
from datetime import date,timedelta,datetime
from zoneinfo import ZoneInfo
import json
import streamlit as st
from ninecat_model import CATS,LABELS,baseline,cohort_ids,weighted_z
from ninecat_strategy import load_data
from player_hub import choose_roster,profiles,ROOT
from roster_store import active_team,roster as shared_roster,state,ownership,persist,save_team,editor,team_label,team_formatter
from dashboard_model import regular_schedule,week_bounds

def close_category_weights(before,enemy,weights):
    """Emphasize close margins in either direction; TO is lower-is-better."""
    from math import exp
    from team_workbench import team_value
    boosted={};margins={}
    for cat in CATS:
        x,y=team_value(before,cat),team_value(enemy,cat)
        if x is None or y is None:
            boosted[cat]=weights[cat];continue
        # Five percentage points for shooting; 20% of team production for counts.
        width=.05 if cat in ('FG','FT') else max((abs(x)+abs(y))*.1,1)
        margin=(y-x if cat in ('TO','TOV') else x-y)
        proximity=exp(-.5*(margin/width)**2)
        boosted[cat]=weights[cat]*(1+2*proximity)
        margins[cat]=(margin,proximity)
    return boosted,margins

def render_planner():
    notes=[]
    _render_planner(notes)
    if notes:
        with st.expander('補強計算與使用說明',expanded=False):
            for note in dict.fromkeys(notes):st.caption(note)

def _render_planner(notes):
    from team_workbench import lineup_week,team_value,matchup_score
    snapshot,entries=load_data();players=snapshot['players'];pool=profiles(players,entries)
    today=datetime.now(ZoneInfo('America/New_York')).date()
    st.markdown('### 1 · 球隊與週次')
    with st.container(key='planner_teams'):
        mine,period=st.columns(2)
        with mine:roster=choose_roster(entries,'stream_team')
        team=active_team(entries);league=state(entries)
        weeks=[date(2026,10,19)+timedelta(weeks=i) for i in range(26)]
        current=today-timedelta(days=today.weekday())
        with period:week=st.selectbox('哪一週',weeks,index=weeks.index(current) if current in weeks else 0,format_func=lambda d:f'{d:%m/%d} — {d+timedelta(days=6):%m/%d}',key='planner_week')
    from fantasy_schedule import week_for
    official=week_for(league,week)
    opponent=(official or {}).get('opponents',{}).get(team)
    if not opponent or opponent not in league['teams']:
        st.info('此週尚未同步對手，請先同步 Yahoo 該週賽程。');return
    st.caption('當週對手 · '+team_label(opponent))
    day=max(week,today) if week<=today<=week+timedelta(days=6) else week
    with st.container(key='planner_period'):
        quota_col=st.container()
        mode='本週對局'
    monday,sunday=week_bounds(day);days=[day+timedelta(days=i) for i in range((sunday-day).days+1)]
    current=json.loads((ROOT/'ninecat_assets/data_2026_27.json').read_text()).get('players',[])
    for p in current:
        if str(p['PLAYER_ID']) not in pool:pool[str(p['PLAYER_ID'])]={**p,'team':p['TEAM_ABBREVIATION'],'eligible':set()}
    for rows in league['teams'].values():
        for r in rows:
            if str(r.get('id')) in pool:pool[str(r['id'])].update(team=r.get('team') or pool[str(r['id'])]['team'],eligible=set(r.get('eligible') or []))
    weights={c:float(st.session_state.get('nc_weight_'+c,1)) for c in CATS}
    if not any(weights.values()):st.info('請先在 9-Cat 至少保留一項權重。');return
    ref=baseline(players,cohort_ids(players,entries,'draft'))
    schedule,_=regular_schedule(json.loads((ROOT/'nba_schedule_2026_27.json').read_text()))
    add_key='stream_adds_'+team+'_'+str(monday)
    from roster_store import state as roster_state
    yahoo_quota=roster_state(entries).get('yahoo_adds',{}).get(team,{})
    if yahoo_quota.get('week')==str(monday):st.session_state[add_key]=min(4,yahoo_quota['remaining'])
    if st.session_state.get(add_key) is None:st.session_state[add_key]=4
    with quota_col:remaining=st.number_input('本週剩餘加人次數',0,4,key=add_key)
    notes.append('整週流程依每天操作後的名單接續模擬，計入 add 額度；預測不是保證結果，交易請在 Yahoo 執行。未取得 waiver 釋出時間的球員不安排重新撿回。')
    st.markdown('### 2 · 可丟棄球員')
    from rotation_ui import drop_picker
    drops=drop_picker(roster,'planner_drops_'+team)
    st.caption('點頭像切換外框；包含 IL，標記可丟棄。')
    owners=ownership(entries,team)
    unowned=[k for k in pool if k not in owners]
    with st.expander('確認自由市場／調整候選名單'):
        confirmed=st.multiselect('我已確認可撿的自由球員',unowned,default=[k for k in league['free'] if k in unowned],format_func=lambda k:pool[k]['PLAYER_NAME'],key='stream_free_'+str(league['revision']))
        meta={}
        for k in confirmed:
            a,b=st.columns(2)
            positions=a.multiselect(pool[k]['PLAYER_NAME']+' · Yahoo 位置',['PG','SG','SF','PF','C'],default=sorted(pool[k]['eligible']),key='free_pos_'+k)
            codes=sorted(schedule)
            nba=b.selectbox(pool[k]['PLAYER_NAME']+' · NBA 球隊',codes,index=codes.index(pool[k]['team']) if pool[k]['team'] in codes else 0,key='free_nba_'+k)
            meta[k]={'eligible':positions,'team':nba}
        if st.button('儲存自由市場確認',key='stream_confirm_free'):
            league['free']=confirmed;league.setdefault('player_meta',{}).update(meta);persist(league);st.rerun()
        notes.append('不在選秀名單內，只代表歸屬未確認；不會自動視為自由球員。其他隊已持有的球員不列入候選。')
    research=st.checkbox('也看歸屬未確認的人選（研究用，不能直接套用）',value=not bool(league['free']),key='stream_research')
    allowed=[k for k in unowned if research or k in league['free']]
    notes.append('自由球員的 NBA 隊伍與 Yahoo 位置可在上方確認；未確認位置者只會安排 UTIL。')
    notes.append('自動候選至少有上季 20 場樣本，避免少量出賽的極端場均；仍可手動指定其他球員。')
    suggested=sorted([k for k in allowed if float(pool[k].get('GP',0))>=20],key=lambda k:weighted_z(pool[k],ref,weights),reverse=True)
    available=suggested
    vacancy=sum(r.get('status')!='IL' for r in roster)<league['capacity']
    from rotation_planner import rotation_workflow
    st.markdown('### 3 · 當週排陣')
    from matchup_simulator_v15 import render_matchup_simulator
    layout=render_matchup_simulator(lite=st.session_state.get('device_view')=='手機版',planner_context={'my_team':team,'opp_team':opponent,'start':day,'remaining':remaining})
    if week+timedelta(days=6)<today:
        st.info('此週已結束，保留歷史排陣，不安排補強。');return
    from daily_evidence import nba_today
    pregame=set(nba_today(str(day)).get('scheduled_teams',[])) if day==today else None
    workflow=rotation_workflow(league,pool,schedule,team,opponent,day,drops,remaining,ref,weights,available,mode,layout=layout,pregame_teams=pregame)
    before,enemy=workflow['before'],workflow['enemy']
    st.caption(f"可輪轉 {workflow['rotation_slots']} 席＝空位 {workflow['vacancies']}＋可釋出 {len(drops)} 人。調好後按「用此排陣更新補強推薦」。")
    st.markdown('### 4 · 整週補強流程')
    for issue in workflow['issues']:st.warning(issue)
    if workflow['issues']:return
    st.caption(f"已計畫 add {len(workflow['planned_adds'])} / {remaining}")
    st.markdown('**優先補強球隊**')
    if workflow['teams']:
        st.dataframe([{'NBA 球隊':r['team'],'最多可排場次':r['games'],'最多淨增':r['net'],'可補日期／位置':'、'.join(d[5:]+(' 不限位置' if any(dd==d and pp=='UTIL' for dd,pp in r['windows']) else ' '+pos) for d,pos in r['windows'] if pos=='UTIL' or not any(dd==d and pp=='UTIL' for dd,pp in r['windows']))} for r in workflow['teams'][:10]],hide_index=True,width='stretch')
    else:st.info('先選可釋出的輪轉球員，或保留空位，才會推薦可補的球隊。')
    st.markdown('**補強方向**')
    if workflow['missing_history']:st.warning('缺少這些日期的排陣實績：'+'、'.join(workflow['missing_history'])+'；以下依已保存實績與剩餘賽程模擬。')
    focus=workflow['focus']
    st.markdown('**優先補強：'+('、'.join(LABELS[c] for c in focus) if focus else '依九項整體改善')+'**')
    st.table([{'項目':LABELS[c],'我方':(f"{team_value(before,c):.1%}" if c in ('FG','FT') else f"{team_value(before,c):.1f}") if team_value(before,c) is not None else '—','對手':(f"{team_value(enemy,c):.1%}" if c in ('FG','FT') else f"{team_value(enemy,c):.1f}") if team_value(enemy,c) is not None else '—'} for c in CATS])
    plans=workflow['sequences']
    if not plans:st.info('先選可釋出的球員並確認剩餘 add；目前沒有可排入的補強流程。');return
    notes.append('每個流程是一整週連續操作，五個流程互為替代，不能相加。搜尋會保留多個候選路徑，並非保證全域最佳。同日操作以開賽前可生效為前提，仍須符合 Yahoo waiver 規則。')
    for i,plan in enumerate(plans):
        with st.container(border=True):
            st.markdown(f"**流程 {i+1} · {plan['adds']} 次 add · 淨增 {plan['net_games']:+d} 場**")
            for step in plan['steps']:
                drop='丟 '+step['drop_name'] if step['drop_name'] else '用空位'
                st.markdown(f"**{step['date'][5:]}**　"+('已計畫 · ' if step.get('planned') else '')+f"{drop} → "+("騰位供 IL 回歸" if step.get('release_only') else f"撿 **{step['add_name']}**（{step['nba_team']}）"))
            st.caption(f"剩餘 add {plan['remaining']} · 適配提升 {plan['gain']:+.2f}"+(' · 含歸屬待確認人選' if any(not x['confirmed'] for x in plan['steps']) else ''))
            if plan['gain']<=0:st.caption('未改善目前模擬，建議保留原名單。')
            with st.expander('操作後週曆'):
                columns=st.columns(7)
                for j,d in enumerate(workflow['days']):
                    with columns[j]:
                        st.markdown('**'+['一','二','三','四','五','六','日'][j]+' '+d['date'][5:]+'**')
                        for action in (x for x in plan['steps'] if x['date']==d['date']):st.caption('＋'+action['add_name'])
                        line=next((x for x in plan['calendar'] if x['date']==d['date']),None)
                        if line:
                            for player in line['lineup']:st.caption(player['name'])
                        else:st.caption('保留已保存排陣')
