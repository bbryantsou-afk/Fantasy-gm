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
        out[c]=100*weights[c]*utility(delta,.5)/denominator
    return sum(out.values()),out

def render_streaming():
    st.subheader('📅 每週補強 · 實際可排場次')
    snapshot,entries=load_data()
    players=snapshot['players']; pool=profiles(players,entries)
    roster=choose_roster(entries,'stream_team')
    teams=list(dict.fromkeys(e['fantasyTeam'] for e in entries))
    opponent=st.selectbox('對手球隊',teams,index=min(1,len(teams)-1),key='stream_opponent')
    from dashboard_model import draft_roster
    opp=draft_roster(entries,opponent)
    day=st.date_input('規劃起日（美東）',date(2026,10,20),min_value=date(2026,10,20),max_value=date(2027,4,11),key='stream_day')
    monday,sunday=week_bounds(day)
    days=[day+timedelta(days=i) for i in range((sunday-day).days+1)]
    schedule,_=regular_schedule(json.loads((ROOT/'nba_schedule_2026_27.json').read_text()))
    st.caption(f'{day}–{sunday}剩餘賽程｜2025–26場均 × 可排入先發場次；不是實績或勝率。假設球員皆可出賽。')
    remaining=st.number_input('本週剩餘 add 次數',0,4,4)
    st.caption('每列是一次 add 的獨立方案，不是把前幾名依序加入的多步計畫。')
    weights={c:st.session_state.get('nc_weight_'+c,1.0) for c in CATS}
    st.caption('沿用9-Cat Strategy的九項權重；每日10席 PG/SG/G/PF/SF/F/C/C/UTIL/UTIL，IL排除。未知位置僅放UTIL，請確認位置資格。')
    owned={str(r.get('id')) for r in roster}
    options=[k for k in pool if k not in owned]
    available=st.multiselect('指定可加入的自由球員（尚未連線Yahoo，請自行確認）',options,format_func=lambda k:pool[k]['PLAYER_NAME'],key='stream_available')
    drops=st.multiselect('可考慮釋出的球員（留空＝有空位）',[str(r.get('id')) for r in roster],format_func=lambda k:next(r['name'] for r in roster if str(r.get('id'))==k),key='stream_drops')
    ref=baseline(players,cohort_ids(players,entries,'draft'))
    before=lineup_week(roster,pool,schedule,days,weights,ref)
    enemy=lineup_week(opp,pool,schedule,days,weights,ref)
    scale={c:abs(team_value(enemy,c) or 0) or (ref[c]['mean'] if c in ('FG','FT') else 1) for c in CATS}
    original,parts=matchup_score(before,enemy,weights,scale)
    st.write(f"原陣容可計分 {before['g']} 場；對手 {enemy['g']} 場。")
    if before['missing']:
        st.warning('無歷史數據未估算：'+'、'.join(before['missing']))
    if not available or not remaining:
        st.info('選擇自由球員後即可比較補強方案。' if remaining else '本週已無add次數，暫不產生加入方案。')
        return
    records=[]; details={}
    for key in available:
        p=pool[key]
        for drop in drops or [None]:
            new=[r for r in roster if str(r.get('id'))!=drop]+[{'id':key,'name':p['PLAYER_NAME'],'status':'active'}]
            after=lineup_week(new,pool,schedule,days,weights,ref)
            score,contributions=matchup_score(after,enemy,weights,scale)
            gain={c:contributions[c]-parts[c] for c in CATS}
            best=max(gain,key=gain.get)
            label=p['PLAYER_NAME']+' / '+(next(r['name'] for r in roster if str(r.get('id'))==drop) if drop else '有空位')
            records.append({'方案':label,'適配提升分':score-original,'候選可排場次':after['counts'].get(key,0),
                            '全隊淨增場次':after['g']-before['g'],'改善最多':LABELS[best] if gain[best]>0 else '無',
                            **{LABELS[c]+'淨增':after['tot'][c]-before['tot'][c] for c in CATS if c not in ('FG','FT')}})
            details[label]=after
    records.sort(key=lambda r:r['適配提升分'],reverse=True)
    st.dataframe(pd.DataFrame(records),hide_index=True,width='stretch')
    selected=st.selectbox('查看方案九項變化',[r['方案'] for r in records])
    after=details[selected]
    st.dataframe([{'項目':LABELS[c],'原本':team_value(before,c),'補強後':team_value(after,c),'對手':team_value(enemy,c)} for c in CATS],hide_index=True,width='stretch')
    st.caption('適配提升分：九項與對手差距的平滑加權指標；不是預測勝率。只規劃起日之後，未加入已結束日比分。雙方採相同位置分配規則，未預測傷病、輪休或實際先發決策。')

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
    st.caption('用相同每人1場比較陣容結構；傷病、成長性、薪資及市場成交價格由使用者判斷。不會送出交易。')
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
