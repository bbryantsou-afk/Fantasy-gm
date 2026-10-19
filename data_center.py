"""Private weekly evidence store. NBA live reads never imply Yahoo settlement."""
import copy,json,math
from datetime import date,datetime,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd
import requests
import streamlit as st
from app_storage import private_path
from ninecat_model import KEYS,CATS,LABELS
from roster_store import state,team_label,team_formatter
from ninecat_strategy import load_data

FILE=Path(__file__).parent/'league_results.json'
ACTIVE={'PG','SG','G','SF','PF','F','C','Util','UTIL'}

def validate_totals(row):
    out={}
    for k in KEYS:
        x=float(row[k])
        if not math.isfinite(x) or x<0:raise ValueError('數據必須為非負有限數字。')
        out[k]=x
    if out['FGM']>out['FGA'] or out['FTM']>out['FTA']:raise ValueError('命中數不可大於出手數。')
    return out

def checked_week(rows,teams):
    if len(rows)!=len(teams) or {r['team'] for r in rows}!=set(teams):raise ValueError('需要每隊各一筆資料。')
    checked={r['team']:{'opponent':r['opponent'],'totals':validate_totals(r)} for r in rows}
    for t,r in checked.items():
        o=r['opponent']
        if o==t or o not in checked or checked[o]['opponent']!=t:raise ValueError('對戰必須雙向配對，且不能和自己比賽。')
    return checked

def category_result(a,b):
    out=[]
    for c in CATS:
        def value(x):
            return x[c+'M']/x[c+'A'] if c in ('FG','FT') and x[c+'A'] else 0 if c in ('FG','FT') else x[c]
        x,y=value(a),value(b)
        delta=(y-x) if c=='TOV' else (x-y)
        out.append(0 if abs(delta)<1e-10 else 1 if delta>0 else -1)
    return out

def standings(weeks,teams):
    scores={t:{'team':t,'W':0,'L':0,'T':0,'weeks':0} for t in teams}
    for week in weeks.values():
        if not week.get('final'):continue
        rows=week['teams']
        for t,r in rows.items():
            if t not in scores or r['opponent'] not in rows:continue
            result=category_result(r['totals'],rows[r['opponent']]['totals']);s=scores[t]
            s['W']+=result.count(1);s['L']+=result.count(-1);s['T']+=result.count(0);s['weeks']+=1
    for s in scores.values():
        n=s['W']+s['L']+s['T'];s['pct']=(s['W']+.5*s['T'])/n if n else 0
    return sorted(scores.values(),key=lambda s:(-s['pct'],-s['W'],s['team']))

def store():
    if '_results' not in st.session_state:
        try:st.session_state['_results']=json.loads(private_path(FILE).read_text())
        except (ValueError,OSError):st.session_state['_results']={'weeks':{},'days':{}}
    return st.session_state['_results']

def save(data):
    path=private_path(FILE);temp=path.with_suffix('.tmp');temp.write_text(json.dumps(data,ensure_ascii=False));temp.replace(path)

def fetch_live(day):
    """Read NBA's current scoreboard and boxscores, rejecting date mismatch."""
    base='https://cdn.nba.com/static/json/liveData/'
    def get(url):
        response=requests.get(url,timeout=15);response.raise_for_status();return response.json()
    scoreboard=get(base+'scoreboard/todaysScoreboard_00.json')['scoreboard']
    if scoreboard['gameDate']!=str(day):raise ValueError('官方即時比分目前不是所選美東日期，未覆寫舊資料。')
    players={};statuses=[]
    fields={'PTS':'points','FG3M':'threePointersMade','REB':'reboundsTotal','AST':'assists','STL':'steals','BLK':'blocks','TOV':'turnovers','FGM':'fieldGoalsMade','FGA':'fieldGoalsAttempted','FTM':'freeThrowsMade','FTA':'freeThrowsAttempted'}
    for game in scoreboard['games']:
        statuses.append({'比賽':game['awayTeam']['teamTricode']+' @ '+game['homeTeam']['teamTricode'],'狀態':game['gameStatusText']})
        if game['gameStatus']==1:continue
        box=get(base+'boxscore/boxscore_'+game['gameId']+'.json')['game']
        for side in ('homeTeam','awayTeam'):
            for p in box[side]['players']:
                stats=p.get('statistics',{})
                if p.get('played')!='1':continue
                players[str(p['personId'])]={k:float(stats[field]) for k,field in fields.items()}
    return players,statuses

def lineup_totals(teams,players):
    totals={};unknown=[]
    for team,roster in teams.items():
        total=dict.fromkeys(KEYS,0.)
        for r in roster:
            if r.get('slot') not in ACTIVE:continue
            if not r.get('id'):unknown.append(r['name']);continue
            for k,v in players.get(str(r['id']),{}).items():total[k]+=v
        totals[team]=total
    return totals,unknown

def totals_table(totals):
    return [{'隊伍':team_label(t),**{LABELS[c]:(r[c+'M']/r[c+'A'] if r[c+'A'] else 0) if c in ('FG','FT') else r[c] for c in CATS}} for t,r in totals.items()]

def render_data_center():
    _,entries=load_data();league=state(entries);teams=list(league['teams']);data=store()
    st.subheader('📚 Data Source · 資料中心')
    st.caption('選秀為原始紀錄；週結果與積分榜使用已保存實績。雲端資料屬於目前工作階段，請下載備份。')
    draft_tab,weekly_tab,rank_tab,live_tab=st.tabs(['選秀結果','每週比賽結果','積分排名','當週即時數據'])
    with draft_tab:
        st.caption('原始選秀結果不隨交易或加人改動；隊名沿用目前同步名稱。')
        selected=st.selectbox('選秀球隊',['全部球隊']+teams,format_func=team_formatter(),key='ds_draft_team')
        records=[{'總順位':i+1,'輪次':e['round'],'隊伍':team_label(e['fantasyTeam']),'球員':e['name'],'位置':e.get('position','')} for i,e in enumerate(entries) if selected=='全部球隊' or selected==e['fantasyTeam']]
        frame=pd.DataFrame(records);st.dataframe(frame,hide_index=True,width='stretch')
        st.download_button('下載選秀結果 CSV',frame.to_csv(index=False).encode('utf-8-sig'),'draft_results.csv','text/csv')
    with weekly_tab:
        st.markdown('#### 保存／核對一週結果')
        day=st.date_input('選擇對戰週內任一天',value=date(2026,10,20),key='ds_week')
        start=day-timedelta(days=day.weekday());end=start+timedelta(days=6);key=str(start)
        st.caption(f'{start} ～ {end}（美東）。每隊填九項總數；命中率以命中／出手重算。TO 越低越好。')
        existing=data['weeks'].get(key,{})
        defaults=[]
        for i,t in enumerate(teams):
            old=existing.get('teams',{}).get(t,{})
            defaults.append({'team':t,'opponent':old.get('opponent',teams[i^1] if i^1<len(teams) else t),**old.get('totals',dict.fromkeys(KEYS,0.))})
        display=[{'隊伍':team_label(r['team']),'對手':team_label(r['opponent']),**{k:r[k] for k in KEYS}} for r in defaults]
        labels={team_label(t):t for t in teams}
        if len(labels)!=len(teams):st.warning('有相同隊名，請先在 Yahoo 區分隊名後同步。');return
        edited=st.data_editor(pd.DataFrame(display),disabled=['隊伍'],hide_index=True,width='stretch',column_config={'對手':st.column_config.SelectboxColumn(options=list(labels),required=True)},key='ds_edit_'+key)
        final=st.checkbox('已和 Yahoo 核對，標記為已結算（納入積分榜）',value=existing.get('final',False),key='ds_final_'+key)
        if st.button('儲存此週結果',key='ds_save_week'):
            try:
                rows=[{'team':labels[r['隊伍']],'opponent':labels[r['對手']],**{k:r[k] for k in KEYS}} for r in edited.to_dict('records')]
                checked=checked_week(rows,teams)
                if final and end>=datetime.now(ZoneInfo('America/New_York')).date():raise ValueError('此週尚未結束，請先儲存為進行中。')
                data['weeks'][key]={'teams':checked,'final':final,'updated_at':datetime.now().astimezone().isoformat()};save(data);st.success('已儲存。')
            except (ValueError,KeyError,TypeError) as exc:st.error(str(exc))
        if data['weeks']:
            st.markdown('#### 已保存週次')
            st.dataframe([{'週開始':k,'狀態':'已結算' if v['final'] else '進行中','更新':v['updated_at']} for k,v in sorted(data['weeks'].items(),reverse=True)],hide_index=True)
        st.download_button('下載週結果／即時資料備份',json.dumps(data,ensure_ascii=False,indent=2),'league_results.json','application/json')
        uploaded=st.file_uploader('還原資料中心備份',type=['json'],key='ds_restore_file')
        if uploaded and st.button('還原週結果（取代目前紀錄）'):
            try:
                restored=json.loads(uploaded.getvalue());clean={'weeks':{},'days':{}}
                for k,w in restored['weeks'].items():
                    date.fromisoformat(k);rows=[{'team':t,'opponent':r['opponent'],**r['totals']} for t,r in w['teams'].items()]
                    clean['weeks'][k]={'teams':checked_week(rows,teams),'final':w['final'] is True,'updated_at':str(w['updated_at'])}
                for k,d in restored.get('days',{}).items():
                    date.fromisoformat(k)
                    if set(d['totals'])!=set(teams):raise ValueError('備份球隊不符。')
                    clean['days'][k]={'totals':{t:validate_totals(r) for t,r in d['totals'].items()},'updated_at':str(d['updated_at']),'statuses':d.get('statuses',[]),'unknown':d.get('unknown',[])}
                st.session_state['_results']=clean;save(clean);st.rerun()
            except (ValueError,KeyError,TypeError) as exc:st.error('無法還原：'+str(exc))
    with rank_tab:
        st.caption('H2H Each Category：每項各算勝敗，勝率＝（勝＋0.5×和）÷總項數。僅計入已結算週；同勝率暫同名次，未套用 Yahoo 額外同分規則。')
        scores=standings(data['weeks'],teams);records=[];last=None;rank=0
        for i,s in enumerate(scores):
            if s['pct']!=last:rank=i+1;last=s['pct']
            records.append({'排名':rank,'隊伍':team_label(s['team']),'勝':s['W'],'敗':s['L'],'和':s['T'],'勝率':s['pct'],'已結算週':s['weeks']})
        st.dataframe(records,hide_index=True,width='stretch',column_config={'勝率':st.column_config.NumberColumn(format='%.3f')})
        if not any(w.get('final') for w in data['weeks'].values()):st.info('尚無已結算週；目前沒有排名依據。')
    with live_tab:
        st.caption('NBA 官方即時 boxscore × 各日已同步先發。按更新抓取當日數據；不是 Yahoo 官方計分，不會自動結算。')
        today=datetime.now(ZoneInfo('America/New_York')).date()
        start=today-timedelta(days=today.weekday());days=[start+timedelta(days=i) for i in range((today-start).days+1)]
        st.write(f'本週 {start} ～ {start+timedelta(days=6)} · 美東今天 {today}')
        if st.button('更新今天 NBA 即時數據',key='ds_refresh_live'):
            archive=league.get('daily_rosters',{}).get(str(today))
            if not archive:st.warning('先到「聯盟同步」同步美東今天的 roster，才能辨認當日先發。')
            else:
                try:
                    with st.spinner('讀取 NBA 官方比分…'):players,statuses=fetch_live(today)
                    totals,unknown=lineup_totals(archive['teams'],players)
                    data['days'][str(today)]={'totals':totals,'unknown':unknown,'source':'NBA 官方即時比分','statuses':statuses,'updated_at':datetime.now().astimezone().isoformat()};save(data)
                    st.success('已更新；比賽進行中數字仍會變動。')
                except (ValueError,KeyError,TypeError,requests.RequestException) as exc:st.error('本次更新失敗，保留既有數據：'+str(exc))
        with st.expander('官方連線不可用時：填入／匯入當日實績'):
            manual_day=st.date_input('實績日期（美東）',value=today,max_value=today,key='ds_manual_day')
            old=data['days'].get(str(manual_day),{}).get('totals',{})
            frame=pd.DataFrame([{'隊伍':team_label(t),**old.get(t,dict.fromkeys(KEYS,0.))} for t in teams])
            st.caption('請填各隊當日計分先發的實際總數；不要填球員場均或整週累計。可補存本週較早日期。')
            st.download_button('下載當日 CSV 範本',frame.to_csv(index=False).encode('utf-8-sig'),'daily_totals.csv','text/csv')
            uploaded=st.file_uploader('匯入已填妥的當日 CSV',type=['csv'],key='ds_daily_csv')
            try:
                if uploaded:frame=pd.read_csv(uploaded)
                manual=st.data_editor(frame,hide_index=True,disabled=['隊伍'],width='stretch',key='ds_daily_edit_'+str(manual_day))
                if st.button('保存當日手動實績',key='ds_save_day'):
                    labels={team_label(t):t for t in teams}
                    if len(labels)!=len(teams) or len(manual)!=len(teams) or set(manual['隊伍'])!=set(labels):raise ValueError('CSV 必須包含每隊各一筆，隊名需和範本一致。')
                    values={labels[r['隊伍']]:validate_totals(r) for r in manual.to_dict('records')}
                    data['days'][str(manual_day)]={'totals':values,'unknown':[],'statuses':[{'來源':'手動輸入／CSV，待 Yahoo 核對'}],'updated_at':datetime.now().astimezone().isoformat()};save(data);st.success('已保存，週累積已更新。')
            except (ValueError,KeyError,TypeError) as exc:st.error('未保存：'+str(exc))
        missing=[str(d) for d in days if str(d) not in data['days']]
        if missing:st.warning('週累積缺少日期：'+ '、'.join(missing)+'。下表只加總已保存日期，不能當成完整週結果。')
        totals={t:dict.fromkeys(KEYS,0.) for t in teams}
        for d in days:
            saved=data['days'].get(str(d))
            if saved:
                for t,r in saved['totals'].items():
                    if t in totals:
                        for k in KEYS:totals[t][k]+=r[k]
        st.dataframe(totals_table(totals),hide_index=True,width='stretch',column_config={'FG%':st.column_config.NumberColumn(format='%.3f'),'FT%':st.column_config.NumberColumn(format='%.3f')})
        saved=data['days'].get(str(today))
        if saved:
            st.caption('今天最後更新：'+saved['updated_at'])
            st.dataframe(saved['statuses'],hide_index=True)
            if saved['unknown']:st.warning('未配對 NBA ID，未計入：'+'、'.join(saved['unknown']))
        st.caption('此版需在各日按更新保存；過去日期可用上方手動實績補存。名單快照可能在賽前改動，請以 Yahoo 最終結算核對。')
        if data['days']:st.dataframe([{'實績日期':d,'來源':v.get('source','手動輸入／CSV'),'更新時間':v['updated_at']} for d,v in sorted(data['days'].items(),reverse=True)],hide_index=True)
