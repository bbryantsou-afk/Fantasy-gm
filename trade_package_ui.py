from app_storage import private_path
"""League-wide, protected-player aware shortlist of two-sided trade ideas."""
import hashlib,json
from pathlib import Path
import pandas as pd
import streamlit as st
from ninecat_model import CATS,LABELS,baseline,cohort_ids,bundle
from ninecat_strategy import package_rows

ROOT=Path(__file__).resolve().parent
PREFS=ROOT/'trade_preferences.json'

def protection_picker(label,ids,pool,key):
    try:
        saved=json.loads(private_path(PREFS).read_text())
    except (OSError,ValueError):
        saved={}
    if key in st.session_state:
        st.session_state[key]=[k for k in st.session_state[key] if k in ids]
    else:
        st.session_state[key]=[k for k in saved.get(key,[]) if k in ids]
    def persist():
        try: data=json.loads(private_path(PREFS).read_text())
        except (OSError,ValueError): data={}
        data[key]=st.session_state[key]
        temp=private_path(PREFS).with_suffix('.tmp')
        temp.write_text(json.dumps(data,ensure_ascii=False))
        temp.replace(private_path(PREFS))
    return st.multiselect(label,sorted(ids,key=lambda k:pool[k]['PLAYER_NAME']),
                          format_func=lambda k:pool[k]['PLAYER_NAME'],key=key,on_change=persist)

def balanced_picker(label,options,**kwargs):
    key=kwargs['key']
    if key in st.session_state:
        st.session_state[key]=[k for k in st.session_state[key] if k in options][:kwargs.get('max_selections',len(options))]
    return st.multiselect(label,options,**kwargs)

def select_quality(candidates,limit=5,league=False,prefer_middle=True):
    scored=[]
    for r in candidates:
        if min(r['my_gain'],r['their_gain'],r.get('my_focus',0),r.get('their_focus',0))<=1e-8:
            continue
        r=dict(r)
        r['quality']=r['my_gain']+r['their_gain']+2*min(r['my_gain'],r['their_gain'])-.5*r['gap']+(.05 if prefer_middle and r['middle_rounds'] else 0)
        scored.append(r)
    scored.sort(key=lambda r:(-r['quality'],r['gap']))
    selected=[]
    for r in scored:
        if league and sum(s['partner']==r['partner'] for s in selected)>=2:
            continue
        if sum(set(s['send'])==set(r['send']) for s in selected)>=2:
            continue
        duplicate=False
        for s in selected:
            if s['partner']!=r['partner']: continue
            lhs=set(r['send']+r['receive']);rhs=set(s['send']+s['receive'])
            # 2-for-2 packages differing in only one player overlap by 60%.
            if len(lhs&rhs)/len(lhs|rhs)>=.59:
                duplicate=True;break
        if not duplicate:
            selected.append(r)
        if len(selected)>=limit: break
    return selected

def render_package_finder(roster,pool,players,entries):
    from trade_packages import near_value_trades
    from roster_store import roster as shared_roster,team_label,team_formatter
    st.markdown('### ✨ 精選模擬交易包')
    st.caption('先篩選滾動交易價值接近，再要求雙方數據適配改善；選秀代表本聯盟偏好，不是客觀價格或接受機率。')
    from trade_market import current_logs,market_model
    from datetime import datetime
    from zoneinfo import ZoneInfo
    asof=datetime.now(ZoneInfo('America/New_York')).date()
    ref=baseline(players,cohort_ids(players,entries,'draft'))
    with st.expander('滾動價值依據 · 選秀／歷史／本季實績',expanded=False):
        if st.button('更新本季交易依據',key='market_refresh'):
            current_logs.clear()
        logs,status,stamp=current_logs(asof.isoformat())
        market_values,market_details,pool=market_model(pool,entries,ref,logs,asof)
        st.caption('開季前：選秀30%＋歷史70%。本季實績比重＝球員實際出賽場次÷（場次＋20），其餘維持選秀：歷史＝3：7；選秀不是永久定價。')
        st.caption('例如5場：24%／56%／20%；20場：15%／35%／50%；60場：7.5%／17.5%／75%（選秀／歷史／本季）。沒有新資料不依日曆衰減。')
        st.caption('選秀價值以順位的平滑遞減曲線換算，再對齊歷史Z分尺度；不直接相加順位。未入選者暫用替補基準，並非真實市場價格。20場與30%均為可修正的起始假設。')
        st.caption('適配數據另以歷史場均和本季場均漸進混合；FG/FT仍依命中及出手重算。尚未考量傷病、角色變動與市場交易。')
        if status: st.caption(status)
        if stamp: st.caption('本季實績取得時間：'+stamp)
    actual_count=sum(d['gp']>0 for d in market_details.values())
    st.caption(f'交易依據截至美東 {asof}｜'+('目前尚無本季樣本：選秀30%＋歷史70%。' if not actual_count else f'{actual_count} 位球員有本季樣本；每人依出賽場次調整比重。'))
    teams=list(dict.fromkeys(e['fantasyTeam'] for e in entries))
    partner=st.selectbox('交易對象',['全部球隊']+teams,index=min(2,len(teams)),key='auto_partner',format_func=team_formatter())
    league=partner=='全部球隊'
    mine={str(r.get('id')) for r in roster if str(r.get('id')) in pool}
    fmt=lambda k:pool[k]['PLAYER_NAME']
    targets={}
    skipped=[]
    for team in teams if league else [partner]:
        rows=shared_roster(entries,team)
        ids={str(r.get('id')) for r in rows if str(r.get('id')) in pool}
        if not ids or ids & mine:
            skipped.append(team)
        else:
            targets[team]=rows
    if not mine or not targets:
        st.info('請選擇與我方不同、且有數據的球隊。')
        return
    if league:
        st.caption(f'逐隊比較 {len(targets)} 隊，不會把多隊球員混成同一筆交易。重複我方球員的原始球隊自動略過。')
    missing=[r['name'] for r in roster if str(r.get('id')) not in pool]
    if missing: st.caption('我方無歷史資料，暫不估算：'+'、'.join(missing))
    own_key='auto_protect_my_'+hashlib.sha256(str(st.session_state.get('trade_team','my_roster')).encode()).hexdigest()[:10]
    my_protected=protection_picker('🔒 我方非賣品（不送出，也不額外釋出）',mine,pool,own_key)
    protections={}
    with st.expander('🔒 對方非賣品 · 每隊獨立保存',expanded=not league):
        for team,rows in targets.items():
            ids={str(r.get('id')) for r in rows if str(r.get('id')) in pool}
            key='auto_protect_opp_'+hashlib.sha256(team.encode()).hexdigest()[:10]
            protections[team]=protection_picker(team_label(team),ids,pool,key)
    st.caption('非賣品設定自動保存在本機；對方設定是你的判斷，非對方GM的已知意願。')
    auto_sizes=st.checkbox("自動搜尋不同人數組合（每方1–4人）",value=True,key="auto_flexible_sizes")
    cols=st.columns(3)
    n_send=cols[0].number_input('我方送出人數',1,4,2,key='auto_n_send',disabled=auto_sizes)
    n_receive=cols[1].number_input('對方送出人數',1,4,2,key='auto_n_receive',disabled=auto_sizes)
    tolerance=cols[2].slider('滾動價值差上限（基準化）',0.0,1.0,.25,.05,key='auto_tolerance')
    with st.expander('雙方九項偏好權重',expanded=False):
        a,b=st.columns(2)
        a.markdown('**我方偏好**')
        b.markdown('**對方偏好（自行推估）**')
        mw={c:a.slider(LABELS[c]+' · 我方',0.0,2.0,float(st.session_state.get('nc_weight_'+c,1.0)),.1,key='auto_m_'+c) for c in CATS}
        tw={c:b.slider(LABELS[c]+' · 對方',0.0,2.0,1.0,.1,key='auto_t_'+c) for c in CATS}
        st.caption('0＝放棄、1＝一般、2＝優先。全聯盟模式暫將右側權重作為各隊共用假設；選定單隊可細調，不會自動推測其戰術。')
    positions=st.multiselect('我方換入包裹必須包含的位置',['PG','SG','SF','PF','C'],key='auto_positions')
    st.caption('每個勾選位置至少一人涵蓋，留空不限；位置依選秀對照。')
    prefer_middle=st.checkbox('價值與適配接近時，優先第2–8輪組合',value=True,key='auto_middle')
    st.caption('選秀只作輔助：樣本不足20場時，若等人數包裹每個對應順位都同方向落後、平均差至少一輪，略過這種整包降級；順位交錯或差距很小仍可搜尋。')
    count=st.select_slider('精選數量',options=[3,5,8],value=5,key='auto_shortlist_count')
    st.caption('依雙方提升、較弱一方的收益及價值差排序；相似包裹去重。全聯盟每隊最多2組，同一送出組合最多2次；符合條件不足時不湊數。')
    configs={}
    auto_config={}
    if auto_sizes:
        with st.expander('不等人數交易 · 補人及額外釋出',expanded=False):
            st.caption('自動搜尋1–4人各種組合。以下名單依選擇順序取前N人補齊席位；未填齊的非等人數方案不搜尋，仍會搜尋1換1、2換2等方案。補人不當作0價值。')
            global_fill=balanced_picker('我方可補進的自由球員（依優先順序）',sorted(set(pool)-mine,key=fmt),format_func=fmt,max_selections=3,key='flex_my_fill')
            global_release=balanced_picker('我方可額外釋出的球員（依優先順序）',sorted(mine-set(my_protected)),format_func=fmt,max_selections=3,key='flex_my_release')
            for team,rows in targets.items():
                ids={str(r.get('id')) for r in rows if str(r.get('id')) in pool}
                suffix=hashlib.sha256(team.encode()).hexdigest()[:10]
                external=sorted(set(pool)-mine-ids,key=fmt)
                fill=balanced_picker('對方可補進的自由球員 · '+team,external,format_func=fmt,max_selections=3,key='flex_their_fill_'+suffix)
                release=balanced_picker('對方可額外釋出 · '+team,sorted(ids-set(protections[team])),format_func=fmt,max_selections=3,key='flex_their_release_'+suffix)
                auto_config[team]=(global_fill,global_release,fill,release)
            st.caption('尚無自由市場名單，請自行確認可取得。交易包每方最多4人，補進／額外釋出另計成本。')
    else:
        configs={}
        with st.expander('不等人數交易 · 補人及額外釋出',expanded=n_send!=n_receive):
            if n_send==n_receive: st.caption('等人數交換，不需額外補人或釋出。')
            for team,rows in targets.items():
                ids={str(r.get('id')) for r in rows if str(r.get('id')) in pool}
                suffix=hashlib.sha256(team.encode()).hexdigest()[:10]
                external=sorted(set(pool)-mine-ids,key=fmt)
                config={'my_fill':[],'their_fill':[],'my_release':[],'their_release':[]}
                if n_send!=n_receive:
                    st.markdown('**'+team+'**')
                    delta=abs(n_send-n_receive)
                    if n_send>n_receive:
                        config['my_fill']=balanced_picker(f'我方補進 {delta} 人 · {team_label(team)}',external,format_func=fmt,max_selections=delta,key='auto_my_fill_'+suffix)
                        config['their_release']=balanced_picker(f'對方額外釋出 {delta} 人 · {team_label(team)}',sorted(ids-set(protections[team])),format_func=fmt,max_selections=delta,key='auto_their_release_'+suffix)
                    else:
                        config['their_fill']=balanced_picker(f'對方補進 {delta} 人 · {team_label(team)}',external,format_func=fmt,max_selections=delta,key='auto_their_fill_'+suffix)
                        config['my_release']=balanced_picker(f'我方額外釋出 {delta} 人 · {team_label(team)}',sorted(mine-set(my_protected)),format_func=fmt,max_selections=delta,key='auto_my_release_'+suffix)
                configs[team]=config
            if n_send!=n_receive:
                st.caption('假設原本滿員；自行確認自由球員可取得。尚未填齊的隊伍不搜尋，不會把補人價值算成0。')
    common=dict(own=roster,pool=pool,ref=ref,my_weights=mw,their_weights=tw,n_send=n_send,n_receive=n_receive,
                tolerance=tolerance,both_improve=True,positions=positions,prefer_middle=False,limit=200,my_protected=my_protected,market_values=market_values,draft_picks={k:d["pick"] for k,d in market_details.items()},draft_guard_samples={k:d["gp"] for k,d in market_details.items()})
    signature=hashlib.sha256(json.dumps([common,targets,protections,configs,count,prefer_middle,asof.isoformat(),market_details,auto_sizes,auto_config],sort_keys=True,default=list).encode()).hexdigest()
    if st.button('尋找近值交易包',type='primary',key='auto_find'):
        if not sum(mw.values()) or not sum(tw.values()):
            st.warning('雙方至少保留一項非0權重。')
        else:
            found=[];errors=[]
            with st.spinner('逐隊比較非賣品、雙方收益與完整席位成本…'):
                for team,rows in targets.items():
                    try:
                        sizes=[(ns,nr) for ns in range(1,5) for nr in range(1,5)] if auto_sizes else [(n_send,n_receive)]
                        for ns,nr in sizes:
                            options=dict(common,n_send=ns,n_receive=nr)
                            if auto_sizes:
                                mf,mr,tf,tr=auto_config[team]
                                delta=abs(ns-nr)
                                config={'my_fill':mf[:delta] if ns>nr else [],'their_fill':tf[:delta] if nr>ns else [],
                                        'my_release':mr[:delta] if nr>ns else [],'their_release':tr[:delta] if ns>nr else []}
                                if (ns>nr and (len(mf)<delta or len(tr)<delta)) or (nr>ns and (len(tf)<delta or len(mr)<delta)):
                                    continue
                            else:
                                config=configs[team]
                            try:
                                results=near_value_trades(other=rows,their_protected=protections[team],**options,**config)
                                found.extend(dict(r,partner=team,opponent=rows,config=config,shape=f'{ns}換{nr}') for r in results)
                            except ValueError as exc:
                                errors.append(team+f' {ns}換{nr}：'+str(exc))
                    except ValueError as exc:
                        errors.append(team+'：'+str(exc))
            shortlist=select_quality(found,count,league,prefer_middle)
            st.session_state.auto_packages={'fingerprint':signature,'results':shortlist,'errors':errors,'candidates':len(found)}
    saved=st.session_state.get('auto_packages',{})
    if saved.get('fingerprint')!=signature:
        st.info('設定完成後點「尋找近值交易包」；修改條件請重新搜尋。')
        return
    if saved.get('errors'):
        with st.expander('未搜尋隊伍與原因'):
            for error in saved['errors']: st.caption(error)
    found=saved['results']
    if not found:
        st.info('沒有同時滿足條件的優質包裹。可調整非賣品、價值差、位置或權重，不強行推薦。')
        return
    st.caption(f"從 {saved.get('candidates',0)} 組近值候選中保留 {len(found)} 組。只有此兩隊交換；不同對手的方案互相獨立。")
    st.dataframe(pd.DataFrame([{'方案':i+1,'對手球隊':team_label(r['partner']),'形式':r.get('shape',''),'我方送出':'＋'.join(fmt(k) for k in r['send']),
            '對方送出':'＋'.join(fmt(k) for k in r['receive']),'我方提升':round(r['my_gain'],3),
            '對方提升':round(r['their_gain'],3),'滾動價值差':round(r['gap'],3),'純數據價值差':round(r.get('statistical_gap',0),3)} for i,r in enumerate(found)]),hide_index=True,width='stretch')
    selected=st.selectbox('研究交易包',range(len(found)),format_func=lambda i:f"方案 {i+1} · {team_label(found[i]['partner'])}",key='auto_detail_'+signature[:10])
    r=found[selected];config=r['config']
    st.markdown('**值得研究的原因**：雙方適配與最高權重項目合計皆提升，滾動交易價值差在設定內，且不動非賣品。')
    with st.expander('本包球員的價值依據',expanded=True):
        info=[]
        for k in list(dict.fromkeys(r['send']+r['receive']+config['my_fill']+config['their_fill']+config['my_release']+config['their_release'])):
            d=market_details[k]
            info.append({'球員':fmt(k),'選秀順位':str(d['pick']) if d['pick'] else '未入選（替補基準）',
                         '本季場次':d['gp'],'選秀比重':f"{d['draft_weight']:.0%}",'歷史比重':f"{d['historical_weight']:.0%}",
                         '本季比重':f"{d['actual_weight']:.0%}",'滾動價值':round(d['value'],3)})
        st.dataframe(pd.DataFrame(info),hide_index=True,width='stretch')
    a,b=st.columns(2)
    for container,side,sent,received,fill,release,weights in (
        (a,roster,r['send'],r['receive'],config['my_fill'],config['my_release'],mw),
        (b,r['opponent'],r['receive'],r['send'],config['their_fill'],config['their_release'],tw)):
        with container:
            st.markdown('**'+('我方' if container is a else '對方')+'九項變化**')
            if fill: st.write('額外補進：'+'、'.join(fmt(k) for k in fill))
            if release: st.write('額外釋出：'+'、'.join(fmt(k) for k in release))
            normalized=[dict(x,games=1,status='active') for x in side if str(x.get('id')) in pool]
            result=bundle(normalized,pool,[pool[k] for k in received+fill],sent+release,ref,weights)
            if result:
                st.dataframe(pd.DataFrame(package_rows(result)),hide_index=True,width='stretch')
                improvements=sorted(result['parts'],key=lambda c:result['parts'][c]['delta'],reverse=True)
                st.caption('主要改善：'+'、'.join(LABELS[c] for c in improvements[:3] if result['parts'][c]['delta']>0))
    with st.expander('一起校準：你覺得這包值得談嗎？'):
        verdict=st.radio('你的判斷',['值得研究','不合理','需要更多資訊'],horizontal=True,key='auto_feedback_verdict')
        reason=st.text_input('理由（例如主力價值、位置缺口或對方不會願意）',key='auto_feedback_reason')
        if st.button('儲存這包評語',key='auto_feedback_save'):
            path=private_path(ROOT/'trade_feedback.json')
            try: feedback=json.loads(path.read_text())
            except (OSError,ValueError): feedback=[]
            feedback.append({'partner':r['partner'],'send':r['send'],'receive':r['receive'],'verdict':verdict,'reason':reason,
                             'my_weights':mw,'their_weights':tw,'balancing':config,'value_gap':r['gap'],'market_asof':str(asof),'market_details':{k:market_details[k] for k in r['send']+r['receive']},'my_gain':r['my_gain'],'their_gain':r['their_gain']})
            temp=path.with_suffix('.tmp');temp.write_text(json.dumps(feedback,ensure_ascii=False,indent=2));temp.replace(path)
            st.success('已儲存供後續一起檢討；目前不會自動改動排名模型。')
    st.caption('適配按每位球員同樣1場，FG/FT按出手重算、TO反向。交易價值採滾動依據，仍未判斷傷病、發展、每日位置排程、即時市場行情或對方真實意願；各重點項目仍可能有得有失，請查看明細。')
