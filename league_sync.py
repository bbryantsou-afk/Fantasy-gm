"""Private browser-assisted roster snapshots. No Yahoo credentials on the server."""
import copy,io,json,re,zipfile,hashlib
from pathlib import Path
from datetime import date,datetime,timedelta
from zoneinfo import ZoneInfo
import streamlit as st
import streamlit.components.v1 as components
from ninecat_strategy import load_data
from ninecat_model import norm
from roster_store import state,persist,identity,team_label,team_formatter
from roster_import import match_rows,build_import,name_key
ROOT=Path(__file__).resolve().parent
bridge=components.declare_component('league_sync',path=str(ROOT/'sync_bridge'))
phone_bridge=components.declare_component('mobile_roster',path=str(ROOT/'mobile_roster_bridge'))
POSITIONS={'PG','SG','G','SF','PF','F','C','Util','UTIL','BN','IL','IL+','IR','IR+'}

def validate_snapshot(payload,league,day,expected_teams):
    if not isinstance(payload,dict) or len(json.dumps(payload))>1_000_000:raise ValueError('同步資料格式或大小不符。')
    if payload.get('schema')!=1 or payload.get('league')!=league or payload.get('date')!=str(day):raise ValueError('聯盟／日期不符，未套用。')
    try:
        stamp=datetime.fromisoformat(payload['capturedAt'].replace('Z','+00:00'))
        if stamp.tzinfo is None or stamp.timestamp()>datetime.now().timestamp()+300:raise ValueError()
    except (KeyError,TypeError,ValueError,AttributeError):raise ValueError('同步時間不符。')
    teams=payload.get('teams')
    if not isinstance(teams,list) or len(teams)!=expected_teams:raise ValueError(f'需要完整 {expected_teams} 隊，資料不完整時不覆寫。')
    seen=set();team_ids=set();result=[]
    for t in teams:
        if not isinstance(t,dict) or not re.fullmatch(r'\d{1,5}',str(t.get('id',''))) or t.get('date')!=str(day):raise ValueError('隊伍日期／ID 不符。')
        source=f"{league}:{t['id']}"
        if source in team_ids:raise ValueError('來源隊伍重複。')
        team_ids.add(source)
        rows=t.get('rows')
        if not isinstance(rows,list) or not 1<=len(rows)<=28:raise ValueError('球員人數不符。')
        for r in rows:
            if not isinstance(r,dict) or not re.fullmatch(r'\d{1,10}',str(r.get('yahooPlayerId',''))):raise ValueError('球員 ID 不符。')
            if r['yahooPlayerId'] in seen:raise ValueError('不同隊伍出現相同球員，請重新同步。')
            seen.add(r['yahooPlayerId'])
            if not isinstance(r.get('name'),str) or not 1<=len(r['name'].strip())<=100:raise ValueError('姓名不符。')
            if r.get('position') not in POSITIONS:raise ValueError('先發／板凳位置不符。')
            if not isinstance(r.get('eligible'),list) or not r['eligible'] or any(p not in ['PG','SG','SF','PF','C'] for p in r['eligible']):raise ValueError('球員位置資格不符。')
            if not re.fullmatch(r'[A-Z]{2,3}',str(r.get('nbaTeam',''))):raise ValueError('NBA 隊伍不符。')
            r=copy.deepcopy(r)
            if payload.get('statsScope')=='day':
                if 'daily_stats' not in r:r.update(daily_stats=None,_daily_stats_missing=True)
                if r['daily_stats'] is not None:
                    from data_center import validate_totals
                    validate_totals(r['daily_stats'])
            result.append(dict(r,source_team=source,source_name=str(t.get('name') or t['id'])[:100]))
    return result

def match_snapshot(rows,players,entries):
    exported=[]
    for r in rows:
        first,_,last=r['name'].partition(' ')
        exported.append({'ID':r['yahooPlayerId'],'First Name':first,'Last Name':last,'Team ID':r['source_team'],
                         'Team Name':r['source_name'],'Position':r['position'],'Eligible Positions':','.join(r['eligible'])})
    matched,pool=match_rows(exported,players,entries)
    for r,source in zip(matched,rows):
        r.update(team=source['nbaTeam'],slot=source['position'])
        if 'daily_stats' in source:r.update(daily_stats=source['daily_stats'],game_status=source.get('game_status',''))
    return matched,pool

def suggested_mapping(rows,league):
    pairs=[]
    for source in dict.fromkeys(r['source_team'] for r in rows):
        names={name_key(r['name']) for r in rows if r['source_team']==source}
        for target,rs in league['teams'].items():pairs.append((len(names & {name_key(r['name']) for r in rs}),source,target))
    mapping={};used=set()
    for score,source,target in sorted(pairs,reverse=True):
        if source not in mapping and target not in used:mapping[source]=target;used.add(target)
    return mapping

def apply_snapshot(league,rows,mapping,payload,today):
    if payload.get('history'):
        history=payload['history']
        if not isinstance(history,list) or len(history)>6:raise ValueError('歷史日期包格式不符。')
        main=date.fromisoformat(payload['date']);begin=main-timedelta(days=main.weekday());seen={payload['date']}
        snapshot,entries=load_data();prepared=[]
        for h in history:
            d=date.fromisoformat(h['date'])
            if h.get('history') or h['date'] in seen or not begin<=d<=min(begin+timedelta(days=6),today):raise ValueError('歷史日期包週次不符。')
            seen.add(h['date']);raw=validate_snapshot(h,payload['league'],d,len(league['teams']))
            matched,_=match_snapshot(raw,snapshot['players'],entries);prepared.append((h,matched))
        primary={k:v for k,v in payload.items() if k!='history'}
        prepared.append((primary,rows));new=league
        for p,rs in sorted(prepared,key=lambda x:x[0]['date']):new=apply_snapshot(new,rs,mapping,p,today)
        return new
    new=build_import(league,rows,mapping)
    captured=payload['capturedAt'];day=payload['date'];source=payload['league']
    archives=copy.deepcopy(league.get('daily_rosters',{}))
    if archives and league.get('sync_league')!=source:raise ValueError('此工作階段已有另一個聯盟快照，請先下載備份並重開工作階段。')
    archive={'captured_at':captured,'source':'Yahoo browser snapshot','teams':copy.deepcopy(new['teams'])}
    if payload.get('statsScope')=='day':archive['stats_scope']='day'
    archives[day]=archive
    new['daily_rosters']=archives;new['sync_mapping']=dict(mapping);new['sync_league']=source
    new['sync_updated_at']=captured
    # Only today's roster becomes the shared current roster; history never changes ownership today.
    if day!=str(today):new['teams']=copy.deepcopy(league['teams']);new['free']=copy.deepcopy(league['free'])
    if day==str(today):
        new['roster_sources']={t:{'kind':'yahoo','updated_at':captured,'date':day,'league':source,'source_team':k} for k,t in mapping.items()}
    if 'matchupSchedule' in payload:
        from fantasy_schedule import import_schedule
        incoming=import_schedule(payload['matchupSchedule'],mapping,source,captured)
        if incoming['weeks']:new['matchup_schedule']=incoming
    elif league.get('matchup_schedule'):
        new['matchup_schedule']=copy.deepcopy(league['matchup_schedule'])
    new['import_source']='Yahoo browser snapshot';return new

def extension_zip():
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted((ROOT/'browser_sync_extension').iterdir()):
            if p.is_file() and p.suffix in ['.json','.js','.md']:z.write(p,'fantasy-gm-sync/'+p.name)
    return buf.getvalue()

def render_sync_connection(full=False):
    """Always mounted before every analysis page so a fresh cloud session restores its private cache."""
    snapshot,entries=load_data();league=state(entries)
    if full:st.caption('0.3.0：一次讀取所選整週已發生的每日排陣與單日實績；包含正在進行的比賽。需更新擴充功能或手機書籤。')
    today=datetime.now(ZoneInfo('America/New_York')).date()
    if full:
        with st.expander('手機直接同步（不需電腦）',expanded=bool(st.query_params.get('phone_sync'))):
            from mobile_roster import render_mobile_setup
            render_mobile_setup()
        st.subheader('🔄 聯盟同步 · 每日陣容')
        source=st.text_input('Yahoo 聯盟 ID',value=str(st.session_state.get('_sync_requested_league',league.get('sync_league','71585'))),key='sync_league_input').strip()
        st.session_state['_sync_requested_league']=source
        if st.session_state.get('_sync_requested_day'):st.session_state['sync_roster_day']=st.session_state.pop('_sync_requested_day')
        day=st.date_input('陣容日期（美東）',value=None if 'sync_roster_day' in st.session_state else today,min_value=date(2025,1,1),max_value=today,key='sync_roster_day')
        st.caption('今天的資料可能隨排陣改變；歷史日期只保存快照，不取代目前持有名單。')
        with st.expander('首次安裝／同步說明',expanded=False):
            st.download_button('下載同步擴充功能 ZIP',extension_zip(),'fantasy-gm-sync.zip','application/zip')
            st.markdown('1. 解壓縮 ZIP。\n2. 在桌面 Chrome 開啟 `chrome://extensions`，開啟「開發人員模式」。\n3. 按「載入未封裝項目」，選取含 manifest.json 的 fantasy-gm-sync 資料夾。\n4. 在同一個 Chrome 登入 Yahoo，再開啟這個 App，重新整理後按同步。')
            st.caption('目前版本 0.3.0：新增整週每日先發、單日實績及進行中數據。下載新版替換原資料夾，在 chrome://extensions 按重新載入，再重新整理 App。開啟自動檢查後約每分鐘更新一次。')
            st.caption('本機保存最近 14 個日期。網站重開後會自動讀取此瀏覽器已保存的今天名單；若沒有今天快照，請按同步。')
        if re.fullmatch(r'\d{1,10}',source):st.link_button('先登入／查看 Yahoo 聯盟',f'https://basketball.fantasysports.yahoo.com/nba/{source}')
    else:
        source=str(st.session_state.get('_sync_requested_league',league.get('sync_league','71585')))
        day=today
    if not re.fullmatch(r'\d{1,10}',source):
        if full:st.info('請輸入 Yahoo 網址 /nba/ 後方的數字聯盟 ID。')
        return
    ack=st.session_state.get('_sync_mapping_ack') or (league.get('sync_mapping') if league.get('sync_league')==source else None)
    args=dict(league=source,date=str(day),mapping=ack,compact=not full,applied=st.session_state.get('_sync_browser_ack'),key='yahoo_browser_bridge',default=None)
    phone_result=phone_bridge(enabled=bool(st.query_params.get('phone_sync')),showStatus=full,mapping=ack,key='phone_roster_receiver',default=None)
    if full:result=bridge(**args)
    else:
        with st.expander('名單同步狀態／立即更新',expanded=False):
            st.caption('全站共用同一個同步接收器。已在此瀏覽器完成配對後，重新連線會自動載入已保存的今天名單。')
            result=bridge(**args)
    if phone_result and st.query_params.get('phone_sync'):
        result=phone_result
        incoming=result.get('snapshot',{}).get('league')
        if isinstance(incoming,str) and re.fullmatch(r'\d{1,10}',incoming):
            source=incoming;st.session_state['_sync_requested_league']=source
    if isinstance(result,dict) and result.get('snapshot'):
        st.session_state['_sync_pending_result']=copy.deepcopy(result)
    if not result:
        pending=st.session_state.get('_sync_pending_result',{})
        if pending.get('snapshot',{}).get('league')==source and pending.get('snapshot',{}).get('date')==str(day):result=pending
    if result and isinstance(result,dict) and result.get('snapshot',{}).get('date')!=str(day):
        if phone_result and full:
            try:
                incoming_day=date.fromisoformat(result['snapshot']['date'])
                if date(2025,1,1)<=incoming_day<=today:
                    st.session_state['_sync_requested_day']=incoming_day;st.rerun()
            except (ValueError,KeyError,TypeError):pass
        result=None  # Previous component value while the date selector changes.
    if result:
        try:
            payload=result['snapshot']
            token=hashlib.sha256(('name-match-v2:'+json.dumps(payload,sort_keys=True)).encode()).hexdigest()
            if token!=st.session_state.get('_sync_applied_token'):
                raw=validate_snapshot(payload,source,day,len(league['teams']))
                missing_stats=sum(bool(r.get('_daily_stats_missing')) for r in raw)
                if missing_stats:st.warning(f'有 {missing_stats} 位球員未提供單日數據；名單可同步，缺少的實績留空，不當作 0。觀察名單保存不受影響。')
                rows,pool=match_snapshot(raw,snapshot['players'],entries)
                remembered=league.get('sync_mapping') if league.get('sync_league')==source else None
                valid_mapping=(isinstance(remembered,dict) and set(remembered)==set(r['source_team'] for r in rows) and set(remembered.values())==set(league['teams']) and len(remembered)==len(league['teams']))
                if valid_mapping:
                    new=apply_snapshot(league,rows,remembered,payload,today)
                    st.session_state['_league']=new;persist(new);st.session_state['_sync_applied_token']=token;st.session_state.pop('nc_roster',None)
                    st.success(f'已同步 {len(rows)} 人 · {day}。'+('今天名單已更新。' if day==today else '已保存歷史日期，今天名單未變更。'))
                    st.session_state['_sync_browser_ack']={'capturedAt':payload['capturedAt'],'date':str(day),'message':f'網站已套用：{len(rows)} 人 · {day}'}
                    league=new
                    st.session_state['_sync_mapping_ack']=remembered
                else:
                    st.info('首次同步請確認隊伍配對，之後按同步即可自動套用。')
                    defaults=suggested_mapping(rows,league);mapping={};targets=list(league['teams'])
                    for team in payload['teams']:
                        k=source+':'+team['id'];mapping[k]=st.selectbox(team['name']+' → App 球隊',targets,index=targets.index(defaults[k]),key='sync_map_'+source+'_'+team['id'],format_func=team_formatter())
                    st.dataframe([{'球員':r['name'],'來源隊伍':r['source_name'],'席次':r['slot'],'數據':'已配對' if r['matched'] else '無數據／保留姓名'} for r in rows],hide_index=True)
                    unique=len(set(mapping.values()))==len(targets)
                    if not unique:st.warning('每一隊必須配對到不同 App 球隊，請調整重複的選項。')
                    st.download_button('先備份現有名單',json.dumps(league,ensure_ascii=False,indent=2),'league_before_sync.json','application/json')
                    if st.button('確認隊伍配對並完成首次同步',disabled=not unique):
                        preview=apply_snapshot(league,rows,mapping,payload,today)
                        st.session_state['_league']=preview;persist(preview);st.session_state['_sync_mapping_ack']=mapping
                        st.session_state['_sync_applied_token']=token;st.session_state['_sync_browser_ack']={'capturedAt':payload['capturedAt'],'date':str(day),'message':f'網站已套用：{len(rows)} 人 · {day}'};st.session_state.pop('nc_roster',None);st.rerun()
        except (ValueError,TypeError,KeyError,AttributeError) as exc:
            st.error('同步未套用：'+str(exc))
            st.session_state['_sync_browser_ack']={'date':str(day),'message':'網站未套用：'+str(exc)}

    return state(entries)


def render_sync():
    # The receiver and first-time mapping UI render globally in app.py before page dispatch.
    _,entries=load_data();league=state(entries)
    archives=league.get('daily_rosters',{})
    if archives:
        st.markdown('### 已同步的每日陣容')
        selected=st.selectbox('查看已保存日期',sorted(archives,reverse=True),key='sync_view_date');saved=archives[selected]
        st.caption('日期以美東比賽日為準。要看當天陣容，先在上方選日期並同步，再在這裡選相同日期。PG～Util 為先發，BN 為板凳，IL 為傷兵。')
        st.caption('讀取時間：'+saved['captured_at']+'。這是當時快照，並非已驗證的最終鎖定紀錄。')
        selected_team=st.selectbox('查看當日球隊',['全部球隊']+list(saved['teams']),format_func=team_formatter(),key='sync_daily_team')
        table=[]
        for team,rows in saved['teams'].items():
            if selected_team!='全部球隊' and team!=selected_team:continue
            for r in rows:table.append({'隊伍':team_label(team),'席次':r.get('slot',r['status']),'球員':r['name'],'NBA':r.get('team',''),'位置':'/'.join(r.get('eligible',[]))})
        st.dataframe(table,hide_index=True,width="stretch")
        st.download_button('下載完整同步備份',json.dumps(league,ensure_ascii=False,indent=2),'league_sync_backup.json','application/json')
