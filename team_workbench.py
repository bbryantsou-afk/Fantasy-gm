"""Weekly lineup-aware add/drop estimates and multi-player trade review."""
from datetime import date,timedelta
import pandas as pd
import streamlit as st
from ninecat_model import CATS,KEYS,LABELS,baseline,cohort_ids,weighted_z,utility
from ninecat_strategy import load_data,package_rows
from ninecat_model import bundle,roster_key
from dashboard_model import week_bounds,regular_schedule
from player_hub import choose_roster,profiles,ROOT
import json

SLOTS=['PG','SG','G','PF','SF','F','C','C','UTIL','UTIL']

def eligible(p,slot):
    pos=p.get('eligible',set())
    return slot=='UTIL' or slot in pos or slot=='G' and bool(pos & {'PG','SG'}) or slot=='F' and bool(pos & {'SF','PF'})

def lineup_week(roster,pool,schedule,days,weights,ref):
    total=dict.fromkeys(KEYS,0.0)
    counts={}
    excluded=[]
    for day in days:
        candidates=[]
        for r in roster:
            if r.get('status')=='IL':
                continue
            p=pool.get(str(r.get('id')))
            if not p:
                if r['name'] not in excluded: excluded.append(r['name'])
                continue
            if day in schedule.get(p['team'],set()):
                candidates.append(p)
        candidates.sort(key=lambda p:weighted_z(p,ref,weights),reverse=True)
        assigned={}
        def place(i,seen):
            for slot in range(len(SLOTS)):
                if slot in seen or not eligible(candidates[i],SLOTS[slot]):
                    continue
                seen.add(slot)
                if slot not in assigned or place(assigned[slot],seen):
                    assigned[slot]=i
                    return True
            return False
        for i in range(len(candidates)):
            place(i,set())
        for i in assigned.values():
            p=candidates[i]
            key=str(p['PLAYER_ID'])
            counts[key]=counts.get(key,0)+1
            for c in KEYS:
                total[c]+=p[c]
    return {'g':sum(counts.values()),'tot':total,'counts':counts,'missing':excluded}

def team_value(a,c):
    if c in ('FG','FT'):
        return a['tot'][c+'M']/a['tot'][c+'A'] if a['tot'][c+'A'] else None
    return a['tot'][c]

def matchup_score(a,b,weights,scale):
    denominator=sum(weights.values()) or 1
    out={}
    for c in CATS:
        x,y=team_value(a,c),team_value(b,c)
        delta=(x-y)/scale[c] if x is not None and y is not None and scale[c] else 0
        if c in ('TO','TOV'):delta=-delta
        out[c]=100*weights[c]*utility(delta,.5)/denominator
    return sum(out.values()),out

def render_streaming():
    from weekly_planner import render_planner
    render_planner()

def render_trades():
    st.subheader('🤝 交易分析室')
    snapshot,entries=load_data()
    players=snapshot['players']; pool=profiles(players,entries)
    roster=choose_roster(entries,'trade_team')
    lookup={str(p['PLAYER_ID']):p for p in players}
    review_mode=st.radio('分析方式',['模擬交易包','手動比較'],horizontal=True,key='trade_review_mode')
    if review_mode=='模擬交易包':
        from trade_package_ui import render_package_finder
        render_package_finder(roster,pool,players,entries)
        return
    owned={str(r.get('id')) for r in roster}
    send=st.multiselect('送出球員（可多選）',list(owned),format_func=lambda k:next(r['name'] for r in roster if str(r.get('id'))==k),key='trade_send')
    receive=st.multiselect('換入球員（可多選）',[k for k in pool if k not in owned],format_func=lambda k:pool[k]['PLAYER_NAME'],key='trade_receive')
    st.caption('使用共用名單；用相同每人1場比較陣容結構；傷病、成長性、薪資及市場成交價格由使用者判斷。不會送出交易。')
    if not send or not receive:
        st.info('選擇送出與換入球員，查看適配與整體數據價值。')
        return
    ref=baseline(players,cohort_ids(players,entries,'draft'))
    weights={c:st.session_state.get('nc_weight_'+c,1.0) for c in CATS}
    normalized=[dict(r,games=1) for r in roster]
    result=bundle(normalized,lookup,[pool[k] for k in receive],send,ref,weights)
    if result is None:
        st.warning('我方缺少可計算數據，無法估算。')
        return
    st.metric('球隊適配變化',f"{result['total']:+.3f}")
    equal={c:1 for c in CATS}
    sent=sum(weighted_z(pool[k],ref,equal) for k in send if k in pool)
    got=sum(weighted_z(pool[k],ref,equal) for k in receive)
    st.write(f'等權Weighted Z合計：送出 {sent:+.3f} → 換入 {got:+.3f}')
    st.caption('不同人數的Z合計不代表公平價值，尚未加入釋出／補進替補球員成本；請連同席位變化評估。')
    st.write(f'名單席位：{len(roster)} → {len(roster)-len(send)+len(receive)}')
    st.dataframe(pd.DataFrame(package_rows(result)),hide_index=True,width='stretch')
    st.dataframe([{'球員':pool[k]['PLAYER_NAME'],'方向':'送出' if k in send else '換入','位置（對照）':','.join(sorted(pool[k]['eligible'])) or '未知'} for k in send+receive if k in pool],hide_index=True,width='stretch')
