"""Three explainable, lineup-aware alternatives; ownership is never inferred as free."""
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
        goal,start,quota=st.columns([1.2,1.3,1])
        with goal:mode=st.radio('補強目標',['本週對局','長期適配'],horizontal=True,key='stream_mode')
        with start:day=st.date_input('開始日期（美東）',max(date(2026,10,20),min(today,date(2027,4,11))),min_value=date(2026,10,20),max_value=date(2027,4,11),key='stream_day')
    monday,sunday=week_bounds(day);days=[day+timedelta(days=i) for i in range((sunday-day).days+1)]
    weights={c:float(st.session_state.get('nc_weight_'+c,1)) for c in CATS}
    if not any(weights.values()):st.info('請先在 9-Cat 至少保留一項權重。');return
    ref=baseline(players,cohort_ids(players,entries,'draft'))
    schedule,_=regular_schedule(json.loads((ROOT/'nba_schedule_2026_27.json').read_text()))
    add_key='stream_adds_'+team+'_'+str(monday)
    if add_key not in st.session_state:st.session_state[add_key]=4
    with quota:remaining=st.number_input('本週剩餘加人次數',0,4,key=add_key)
    notes.append(f'{day:%m/%d}–{sunday:%m/%d} 剩餘賽程。歷史場均 × 可排入先發場次；不是實績或勝率。已結束日比分尚未納入，傷病與輪休由你排除。每個方案獨立使用 1 次 add，不能直接把五個方案相加。')
    editor(entries,players,team,'stream_roster')
    before=lineup_week(roster,pool,schedule,days,weights,ref);enemy=lineup_week(opp,pool,schedule,days,weights,ref)
    scale={c:abs(team_value(enemy,c) or 0) or (ref[c]['mean'] if c in ('FG','FT') else max(ref[c]['mean']*max(enemy['g'],1),1)) for c in CATS}
    priority_weights,margins=close_category_weights(before,enemy,weights)
    original,parts=matchup_score(before,enemy,priority_weights,scale)
    a,b,c=st.columns(3);a.metric('我方可排場次',before['g']);b.metric('對手可排場次',enemy['g']);c.metric('剩餘 add',remaining)
    comparison=[]
    for cat in CATS:
        x,y=team_value(before,cat),team_value(enemy,cat)
        gap=((y-x) if cat in ('TO','TOV') else (x-y)) if x is not None and y is not None else None
        comparison.append({'項目':LABELS[cat],'我方':f'{x:.1%}' if cat in ('FG','FT') and x is not None else f'{x:.1f}' if x is not None else '—',
            '對手':f'{y:.1%}' if cat in ('FG','FT') and y is not None else f'{y:.1f}' if y is not None else '—',
            '狀態':'未估算' if gap is None else '持平' if abs(gap)<1e-8 else '🟢 領先' if gap>0 else '🟠 落後'})
    st.table(comparison)
    focus=sorted((c for c in margins if weights[c]>0 and margins[c][1]>=.6),key=lambda c:margins[c][1],reverse=True)[:3]
    if focus:
        st.markdown('**優先補強：'+'、'.join(LABELS[c]+('（小幅領先）' if margins[c][0]>0 else '（接近落後）' if margins[c][0]<0 else '（持平）') for c in focus)+'**')
    else:st.caption('目前沒有明顯接近的項目，依九項整體改善推薦。')
    notes.append('優先守住小幅領先、追回接近落後；大幅領先或落後的項目降低優先度。仍會扣除釋出造成的其他項目損失，並保留你的九項權重。')
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
    suggested=sorted([k for k in allowed if float(pool[k].get('GP',0))>=20],key=lambda k:weighted_z(pool[k],ref,weights),reverse=True)[:36]
    with st.container(key='planner_candidates'):
        candidates,droppable=st.columns(2)
    with candidates:available=st.multiselect('候選球員（留空自動比較最多 36 位，可輸入指定）',allowed,format_func=lambda k:pool[k]['PLAYER_NAME'],key='stream_available') or suggested
    active=[r for r in roster if r.get('status')!='IL']
    vacancy=len(active)<league['capacity']
    drop_options=[str(r['id']) for r in active if r.get('id') and str(r['id']) in pool]
    weakest=sorted(drop_options,key=lambda k:weighted_z(pool[k],ref,weights))[:3]
    with droppable:drops=st.multiselect('允許列入釋出方案的球員',drop_options,default=weakest if not vacancy else [],format_func=lambda k:pool[k]['PLAYER_NAME'],key='stream_drops_'+team+'_'+str(league['revision']))
    if not vacancy and not drops:st.info('名單已滿，請先選擇願意考慮釋出的人。');return
    if not remaining:st.info('本週沒有剩餘 add 次數，仍可查看上方比較。');return
    if not available:st.info('先確認自由球員，或開啟「歸屬未確認」研究候選。');return
    results=[]
    for key in available:
        p=pool[key]
        for drop in ([None]+drops if vacancy else drops):
            new=[r for r in roster if str(r.get('id'))!=drop]+[{'id':key,'name':p['PLAYER_NAME'],'team':p['team'],'eligible':sorted(p['eligible']),'status':'active','games':1}]
            after=lineup_week(new,pool,schedule,days,weights,ref)
            if after['counts'].get(key,0)==0:continue
            score,contributions=matchup_score(after,enemy,priority_weights,scale)
            long_gain=weighted_z(p,ref,weights)-(weighted_z(pool[drop],ref,weights) if drop else 0)
            gains={c:contributions[c]-parts[c] for c in CATS}
            results.append({'key':key,'drop':drop,'rows':new,'after':after,'gain':score-original,'long':long_gain,'best':max(gains,key=gains.get),'targets':[c for c in focus if gains[c]>0]})
    results.sort(key=lambda r:r['gain'] if mode=='本週對局' else r['long'],reverse=True)
    chosen=[];seen=set()
    for r in results:
        if r['key'] not in seen:chosen.append(r);seen.add(r['key'])
        if len(chosen)==5:break
    st.markdown('### 推薦方案')
    if not chosen:st.info('候選在剩餘賽程沒有可排入的場次，暫不建議消耗 add。');return
    def apply_plan(rows,key,count):
        save_team(entries,team,rows)
        st.session_state[key]=count-1
    for i,r in enumerate(chosen):
        key=r['key'];p=pool[key];after=r['after'];confirmed=key in league['free']
        with st.container(border=True,key='planner_plan_'+str(i)):
            import html
            drop_label='釋出 '+pool[r['drop']]['PLAYER_NAME'] if r['drop'] else '使用空位'
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
