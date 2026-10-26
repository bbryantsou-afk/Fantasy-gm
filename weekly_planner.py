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
    with st.container(key='planner_teams'):
        mine,theirs=st.columns(2)
        with mine:roster=choose_roster(entries,'stream_team')
        team=active_team(entries);league=state(entries)
        teams=[t for t in league['teams'] if t!=team]
        with theirs:opponent=st.selectbox('本週對手',teams,key='stream_opponent',format_func=team_formatter())
    opp=shared_roster(entries,opponent)
    today=datetime.now(ZoneInfo('America/New_York')).date()
    with st.container(key='planner_period'):
        goal,start,quota_col=st.columns([1.2,1.3,1])
        with goal:mode=st.radio('補強目標',['本週對局','長期適配'],horizontal=True,key='stream_mode')
        with start:day=st.date_input('開始日期（美東）',max(date(2026,10,20),min(today,date(2027,4,11))),min_value=date(2026,10,20),max_value=date(2027,4,11),key='stream_day')
    monday,sunday=week_bounds(day);days=[day+timedelta(days=i) for i in range((sunday-day).days+1)]
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
    notes.append(f'{day:%m/%d}–{sunday:%m/%d} 剩餘賽程。歷史場均 × 可排入先發場次；不是實績或勝率。已結束日比分尚未納入，傷病與輪休由你排除。每個方案獨立使用 1 次 add，不能直接把五個方案相加。')
    editor(entries,players,team,'stream_roster')
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
    with st.container(key='planner_candidates'):
        candidates,droppable=st.columns(2)
    with candidates:available=st.multiselect('候選球員（留空依位置與賽程比較）',allowed,format_func=lambda k:pool[k]['PLAYER_NAME'],key='stream_available') or suggested
    active=[r for r in roster if r.get('status')!='IL']
    vacancy=len(active)<league['capacity']
    drop_options=[str(r['id']) for r in active if r.get('id') and str(r['id']) in pool]
    weakest=sorted(drop_options,key=lambda k:weighted_z(pool[k],ref,weights))[:3]
    with droppable:drops=st.multiselect('允許列入釋出方案的球員',drop_options,default=[],format_func=lambda k:pool[k]['PLAYER_NAME'],key='stream_drops_'+team+'_'+str(league['revision']))
    from rotation_planner import rotation_workflow
    workflow=rotation_workflow(league,pool,schedule,team,opponent,day,drops,remaining,ref,weights,available,mode)
    before,enemy=workflow['before'],workflow['enemy']
    st.markdown('### 1 · 每日名單與輪轉位置')
    st.caption(f"可輪轉 {workflow['rotation_slots']} 席＝空位 {workflow['vacancies']} 席＋你選擇可釋出 {len(drops)} 人。未選球員不會列入釋出。")
    for item in workflow['days']:
        label=item['date']+(' · 已保存排陣' if item['historical'] else ' · 可補 '+('／'.join(item['open']) or '無空缺'))
        with st.expander(label,expanded=False):
            if not item['known']:st.caption('此日尚無已保存排陣，不用目前名單回填。')
            else:st.dataframe([{'位置':r.get('slot','—'),'球員':r['name'],'NBA':r.get('team',''),'輪轉':'可釋出' if r.get('rotation') else ''} for r in item['rows']],hide_index=True,width='stretch',height='auto')
    st.markdown('### 2 · 優先補哪些 NBA 球隊')
    if workflow['teams']:
        st.dataframe([{'NBA 球隊':r['team'],'最多可排場次':r['games'],'最多淨增':r['net'],'可補日期／位置':'、'.join(d[5:]+' '+pos for d,pos in r['windows'])} for r in workflow['teams'][:10]],hide_index=True,width='stretch')
    else:st.info('先選可釋出的輪轉球員，或保留空位，才會推薦可補的球隊。')
    st.markdown('### 3 · 模擬後的數據補強方向')
    if workflow['missing_history']:st.warning('缺少這些日期的排陣實績：'+'、'.join(workflow['missing_history'])+'；以下依已保存實績與剩餘賽程模擬。')
    focus=workflow['focus']
    st.markdown('**優先補強：'+('、'.join(LABELS[c] for c in focus) if focus else '依九項整體改善')+'**')
    st.table([{'項目':LABELS[c],'我方':(f"{team_value(before,c):.1%}" if c in ('FG','FT') else f"{team_value(before,c):.1f}") if team_value(before,c) is not None else '—','對手':(f"{team_value(enemy,c):.1%}" if c in ('FG','FT') else f"{team_value(enemy,c):.1f}") if team_value(enemy,c) is not None else '—'} for c in CATS])
    notes.append('過去日期保留每日實際排陣；剩餘日期依目前持有名單與 Yahoo 位置試排。球隊表為不同候選的可行日期聯集，不代表任意球員都可占用所有位置。每個推薦獨立使用一次 add。')
    if not vacancy and not drops:st.info('請指定願意釋出的輪轉球員。');return
    if not remaining:st.info('本週沒有剩餘 add。');return
    results=workflow['results']
    results.sort(key=lambda r:r['gain'] if mode=='本週對局' else r['long'],reverse=True)
    chosen=[];seen=set()
    for r in results:
        if r['key'] not in seen:chosen.append(r);seen.add(r['key'])
        if len(chosen)==5:break
    st.markdown('### 4 · 球員推薦')
    if not chosen:st.info('候選在剩餘賽程沒有可排入的場次，暫不建議消耗 add。');return
    def apply_plan(rows,key,count):
        save_team(entries,team,rows)
        st.session_state[key]=count-1
    for i,r in enumerate(chosen):
        key=r['key'];p=pool[key];after=r['after'];confirmed=key in league['free']
        with st.container(border=True,key='planner_plan_'+str(i)):
            import html
            drop_label='釋出 '+pool[r['drop']]['PLAYER_NAME'] if r['drop'] else '使用空位'
            st.caption('可排：'+'、'.join(w['date'][5:]+' '+w['position'] for w in r['windows']))
            ownership_label='✅ 自由球員' if confirmed else '⚠️ 歸屬待確認'
            metrics=[('可排場次',str(after['counts'].get(key,0))),('淨增場次',f"{after['g']-before['g']:+d}"),('適配提升',f"{r['gain']:+.2f}")]
            metric_html=''.join('<div class="plan-number"><span>'+label+'</span><b>'+value+'</b></div>' for label,value in metrics)
            target_text='、'.join(LABELS[c] for c in r['targets']) if r['targets'] else '—'
            best_text=LABELS[r['best']] if r['gain']>0 else '無改善'
            summary=(f'<section class="plan-summary"><div class="plan-top"><div class="plan-person"><img src="https://cdn.nba.com/headshots/nba/latest/260x190/{key}.png" alt=""><div><b>{i+1}. {html.escape(p["PLAYER_NAME"])}</b><span>{html.escape(drop_label)}</span><small>{ownership_label}</small></div></div>{metric_html}</div>'
                     +'<div class="plan-insights"><div><span>接近項目</span><b>'+html.escape(target_text)+'</b></div><div><span>改善最多</span><b>'+html.escape(best_text)+'</b></div></div></section>')
            st.markdown(summary,unsafe_allow_html=True)
            if mode=='長期適配':st.caption(f"每場加權 Z 淨變化 {r['long']:+.2f}；尚未預測成長、健康或交易市價。")
            with st.expander('九項變化'):
                rows=[]
                for cat in CATS:
                    x,y=team_value(before,cat),team_value(after,cat)
                    change='—' if x is None or y is None else f'{(y-x)*100:+.2f} 個百分點' if cat in ('FG','FT') else f'{y-x:+.1f}'
                    rows.append({'項目':LABELS[cat],'改變':change})
                st.table(rows);notes.append('TO 淨減少才是改善；FG/FT 由總命中／總出手加權。適配分不是勝率。')
            if r['gain']<=0:st.caption('這個方案沒有提高目前的對局適配分；保留原名單也是選項。')
            st.button('套用（1 次）',key='stream_apply_'+str(i),disabled=not confirmed,on_click=apply_plan,args=(r['rows'],'stream_adds_'+team+'_'+str(monday),remaining))
