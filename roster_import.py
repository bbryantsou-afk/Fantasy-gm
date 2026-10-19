"""Preview and atomically apply user-exported Fantasy Helper rosters."""
import copy,io,json,re,zipfile,hashlib
from datetime import datetime,timezone
import streamlit as st
from ninecat_model import norm
from roster_store import state,identity,persist,team_label,team_formatter

def read_export(raw):
    if len(raw)>5_000_000:raise ValueError('檔案過大。')
    if raw.startswith(b'PK'):
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            files=[x for x in z.infolist() if x.filename.lower().endswith('.json')]
            if len(files)!=1 or files[0].file_size>5_000_000:raise ValueError('ZIP 必須只有一個小於 5MB 的 JSON。')
            raw=z.read(files[0])
    d=json.loads(raw.decode('utf-8-sig'))
    required=['ID','First Name','Last Name','Team ID','Position','Eligible Positions']
    if isinstance(d,dict):
        if any(not isinstance(d.get(k),list) for k in required):raise ValueError('請選 Fantasy Helper 的 Roster 報表。')
        n=len(d['ID'])
        if any(len(d[k])!=n for k in required):raise ValueError('欄位長度不一致。')
        d=[{k:v[i] for k,v in d.items() if isinstance(v,list) and len(v)==n} for i in range(n)]
    if not isinstance(d,list) or not d or len(d)>1000:raise ValueError('名單格式不符或沒有球員。')
    seen=set()
    for r in d:
        if not isinstance(r,dict) or any(k not in r for k in required):raise ValueError('缺少名單欄位。')
        if not re.fullmatch(r'\d+\.p\.\d+',str(r['ID'])) or not re.fullmatch(r'\d+\.l\.\d+\.t\.\d+',str(r['Team ID'])):raise ValueError('Yahoo 球員／球隊 ID 格式不符。')
        if r['ID'] in seen:raise ValueError('檔案包含重複球員。')
        seen.add(r['ID'])
        if not str(r['First Name'] or '').strip() or not str(r['Last Name'] or '').strip():raise ValueError('球員姓名不完整。')
        if str(r['Position']) not in ['PG','SG','G','SF','PF','F','C','Util','UTIL','BN','IL','IL+','IR','IR+']:raise ValueError('無法辨識名單位置。')
    if len({str(r['Team ID']).split('.t.')[0] for r in d})!=1:raise ValueError('請勿混合不同聯盟。')
    return d

def name_key(s):
    return re.sub(r'(?:jr|sr|iii|ii|iv)$','',re.sub(r'[^a-z0-9]','',norm(s)))

def match_rows(rows,players,entries):
    pool={str(p['PLAYER_ID']):{'id':str(p['PLAYER_ID']),'name':p['PLAYER_NAME'],'team':p['TEAM_ABBREVIATION']} for p in players}
    for e in entries:
        if e.get('playerId') is not None:continue
        m=re.match(r'\((\w+)',e.get('position',''))
        pool['name:'+norm(e['name'])]={'id':None,'name':e['name'],'team':m.group(1) if m else ''}
    index={}
    for k,p in pool.items():index.setdefault(name_key(p['name']),[]).append(k)
    # Yahoo sometimes shows a first initial; accept only a unique full-surname match.
    abbreviated={}
    for k,p in pool.items():
        first,_,last=p['name'].partition(' ')
        if first and last:abbreviated.setdefault((first[0].lower(),name_key(last)),[]).append(k)
    result=[]
    for r in rows:
        name=str(r['First Name']).strip()+' '+str(r['Last Name']).strip()
        hits=index.get(name_key(name),[])
        first=str(r['First Name']).strip()
        if not hits and re.fullmatch(r'[A-Za-z]\.?',first):
            hits=abbreviated.get((first[0].lower(),name_key(str(r['Last Name']))),[])
        p=pool[hits[0]] if len(hits)==1 else {'id':None,'name':name,'team':''}
        pos=str(r['Position']);eligible=[x for x in str(r['Eligible Positions']).split(',') if x in ['PG','SG','SF','PF','C']]
        result.append(dict(p,eligible=eligible,status='IL' if pos in ['IL','IL+','IR','IR+'] else 'bench' if pos=='BN' else 'active',games=1,
            yahoo_id=r['ID'],source_team=r['Team ID'],source_name=r.get('Team Name',r['Team ID']),matched=len(hits)==1))
    return result,pool

def build_import(league,rows,mapping):
    if len(set(mapping.values()))!=len(mapping):raise ValueError('不同來源球隊不能配到同一隊。')
    if set(mapping)!=set(r['source_team'] for r in rows):raise ValueError('請配對所有來源球隊。')
    new=copy.deepcopy(league)
    names=new.setdefault('team_names',{})
    for r in rows:
        name=str(r.get('source_name','')).strip()
        if name and name!=r['source_team']:names[mapping[r['source_team']]]=name
    for t in mapping.values():
        if t not in new['teams']:raise ValueError('目標球隊不存在。')
        new['teams'][t]=[]
    for r in rows:
        new['teams'][mapping[r['source_team']]].append({k:v for k,v in r.items() if k not in ['source_team','source_name','matched']})
    owned={identity(r) for rs in new['teams'].values() for r in rs}
    new['free']=[k for k in new['free'] if k not in owned]
    from league_settings import validate_backup
    new=validate_backup(new,league['teams'])
    new['roster_sources']=copy.deepcopy(league.get('roster_sources',{}))
    for t in mapping.values():new['roster_sources'][t]={'kind':'file','updated_at':datetime.now(timezone.utc).isoformat()}
    new['imported_at']=datetime.now(timezone.utc).isoformat()
    new['import_source']='Fantasy Helper Roster'
    return new

def render_import(players,entries):
    st.markdown('### 匯入 Fantasy Helper 聯盟名單')
    st.caption('Fantasy Helper → Data → 右上資料庫圖示 → Roster → Json → Download。直接上傳下載的 ZIP 即可；只匯入本次工作階段，不會更新 Yahoo 或公開名單。')
    uploaded=st.file_uploader('上傳 Roster ZIP／JSON',type=['zip','json'],key='helper_roster_file')
    if not uploaded:return
    raw=uploaded.getvalue();tag=hashlib.sha256(raw).hexdigest()[:12]
    try:rows,pool=match_rows(read_export(raw),players,entries)
    except (ValueError,TypeError,KeyError,zipfile.BadZipFile,UnicodeError) as exc:st.error(str(exc));return
    league=state(entries);sources=list(dict.fromkeys(r['source_team'] for r in rows));teams=list(league['teams'])
    if len(sources)>len(teams):st.error('來源隊伍多於目前聯盟，無法匯入。');return
    st.info(f'讀到 {len(sources)} 隊、{len(rows)} 位球員。請確認隊伍配對；只有來源列出的隊伍會被取代。')
    # Greedy overlap matching suggests team identities; never assumes Yahoo numbering equals local numbering.
    choices=[]
    for source in sources:
        names={name_key(r['name']) for r in rows if r['source_team']==source}
        for t,rs in league['teams'].items():choices.append((len(names & {name_key(r['name']) for r in rs}),source,t))
    defaults={};used=set()
    for score,source,t in sorted(choices,reverse=True):
        if source not in defaults and t not in used:defaults[source]=t;used.add(t)
    mapping={}
    with st.expander('確認來源球隊 → App 球隊',expanded=True):
        for source in sources:
            label=next(str(r['source_name']) for r in rows if r['source_team']==source)
            mapping[source]=st.selectbox(label+' · '+source,teams,index=teams.index(defaults[source]),key='helper_map_'+tag+source,format_func=team_formatter())
    with st.expander('球員配對／無資料球員'):
        st.caption('Yahoo ID 與 NBA ID 不同，依姓名配對；未配對者保留姓名，不會套用其他球員數據。受傷狀態不等於 IL，只有原名單 IL 席次才匯入為 IL。')
        for r in rows:
            if not r['matched']:
                pick=st.selectbox(r['name']+'（未自動配對）',['']+list(pool),format_func=lambda k:pool[k]['name'] if k else '保留姓名，不估算數據',key='helper_player_'+tag+r['yahoo_id'])
                if pick:r.update(pool[pick]);r['matched']=True
        st.dataframe([{'球員':r['name'],'位置':'/'.join(r['eligible']),'席次':r['status'],'配對':'已配對' if r['matched'] else '無數據'} for r in rows],hide_index=True)
    try:new=build_import(league,rows,mapping)
    except (ValueError,TypeError,KeyError) as exc:st.error('尚不能套用：'+str(exc));return
    changes=[]
    for source,t in mapping.items():
        before={identity(r):r['name'] for r in league['teams'][t]};after={identity(r):r['name'] for r in new['teams'][t]}
        changes.append({'App 球隊':team_label(t),'人數':len(after),'加入':'、'.join(after[k] for k in after.keys()-before.keys()) or '—','移除':'、'.join(before[k] for k in before.keys()-after.keys()) or '—'})
    st.dataframe(changes,hide_index=True)
    st.download_button('先下載目前名單備份',json.dumps(league,ensure_ascii=False,indent=2),'league_before_import.json','application/json')
    confirmed=st.checkbox('我已確認隊伍配對，以上名單將取代對應隊伍',key='helper_confirm_'+tag)
    if st.button('確認匯入並同步所有頁面',disabled=not confirmed,key='helper_apply_'+tag):
        st.session_state['_league']=new;persist(new)
        st.session_state.pop('nc_roster',None)
        st.success('已匯入。可切換至其他功能查看；重要名單請下載備份。')
