"""Private, shared league rosters. Changes are local records, never Yahoo actions."""
import json,copy,re
from pathlib import Path
import streamlit as st
from app_storage import private_path
from ninecat_model import norm
ROOT=Path(__file__).resolve().parent
FILE=ROOT/'league_rosters.json'

def identity(row):
    return str(row['id']) if row.get('id') is not None else 'name:'+norm(row['name'])

def state(entries):
    if '_league' not in st.session_state:
        teams={}
        for e in entries:
            m=re.match(r'\((\w+)\s*-\s*([^)]*)',e.get('position',''))
            teams.setdefault(e['fantasyTeam'],[]).append({'id':str(e['playerId']) if e.get('playerId') is not None else None,
                'name':e['name'],'team':m.group(1) if m else '', 'eligible':m.group(2).split(',') if m else [],'status':'active','games':1})
        data={'teams':teams,'free':[],'capacity':14,'revision':0,'roster_sources':{t:{'kind':'draft'} for t in teams}}
        try:
            saved=json.loads(private_path(FILE).read_text())
            if set(saved.get('teams',{}))==set(teams): data.update(saved)
        except (OSError,ValueError):pass
        st.session_state['_league']=data
        # Migrate the user's existing custom roster once, without overwriting a saved league.
        if not private_path(FILE).exists():
            try:
                legacy=st.session_state.get('nc_roster') or json.loads(private_path(ROOT/'ninecat_state.json').read_text()).get('roster',[])
                if legacy:
                    historical=json.loads((ROOT/'ninecat_assets/data.json').read_text())['players']
                    by_name={norm(p['PLAYER_NAME']):p for p in historical}
                    known={norm(r['name']):r for rs in teams.values() for r in rs}
                    migrated=[]
                    for row in legacy:
                        r=dict(known.get(norm(row['name']),{}),**row)
                        p=by_name.get(norm(row['name']))
                        if p:
                            if r.get('id') is None:r['id']=str(p['PLAYER_ID'])
                            r.setdefault('team',p['TEAM_ABBREVIATION'])
                        migrated.append(r)
                    data['capacity']=max(14,sum(r.get('status')!='IL' for r in migrated))
                    save_team(entries,next(iter(teams)),migrated)
            except (OSError,ValueError,KeyError,TypeError):pass
    return st.session_state['_league']

def persist(data):
    data['revision']=data.get('revision',0)+1
    path=private_path(FILE);temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(data,ensure_ascii=False));temp.replace(path)

def roster(entries,team):return copy.deepcopy(state(entries)['teams'].get(team,[]))

def active_team(entries):
    teams=list(state(entries)['teams'])
    if st.session_state.get('_my_team') not in teams:st.session_state['_my_team']=teams[0]
    return st.session_state['_my_team']

def team_label(team):
    """Private display name; stable internal keys survive team renames."""
    data=st.session_state.get('_league',{})
    name=data.get('team_names',{}).get(team)
    if name:return name
    if not re.fullmatch(r'球隊\s*\d+',str(team)):return team
    rows=data.get('teams',{}).get(team,[])
    return '待同步隊名'+(' · '+rows[0]['name'] if rows else '')

def team_formatter():
    labels={t:team_label(t) for t in st.session_state.get('_league',{}).get('teams',{})}
    return lambda t:labels.get(t,t)

def choose_team(entries,key,label='我的球隊'):
    current=active_team(entries)
    if st.session_state.get(key)!=current:st.session_state[key]=current
    def changed():st.session_state['_my_team']=st.session_state[key]
    return st.selectbox(label,list(state(entries)['teams']),key=key,on_change=changed,format_func=team_formatter())

def save_team(entries,team,rows):
    data=state(entries)
    known={identity(r):r for rs in data['teams'].values() for r in rs}
    rows=[dict(known.get(identity(r),{}),**r) for r in rows]
    if len({identity(r) for r in rows})!=len(rows):raise ValueError('名單有重複球員。')
    if sum(r.get('status')=='IL' for r in rows)>3:raise ValueError('IL 最多 3 席。')
    if sum(r.get('status')!='IL' for r in rows)>data['capacity']:raise ValueError(f"一般名單最多 {data['capacity']} 席，請釋出球員或調整席次。")
    # An explicitly applied roster edit transfers any incoming player in this private league copy.
    incoming={identity(r) for r in rows}
    for other in data['teams']:
        if other!=team:data['teams'][other]=[r for r in data['teams'][other] if identity(r) not in incoming]
    data['teams'][team]=copy.deepcopy(rows)
    from datetime import datetime,timezone
    data.setdefault('roster_sources',{})[team]={'kind':'manual','updated_at':datetime.now(timezone.utc).isoformat()}
    data['free']=[k for k in data['free'] if k not in incoming]
    st.session_state['nc_roster']=copy.deepcopy(rows)
    st.session_state['sim_my_players']=[r['name'] for r in rows if r.get('status')!='IL']
    persist(data)

def ownership(entries,my_team):
    return {identity(r):('我的球員' if team==my_team else team_label(team)) for team,rows in state(entries)['teams'].items() for r in rows}

def availability(entries,my_team,key):
    owner=ownership(entries,my_team).get(key)
    return owner or ('已確認自由球員' if key in state(entries)['free'] else '歸屬未確認')

def editor(entries,players,team,key='shared'):
    data=state(entries);rows=roster(entries,team)
    pool={str(p['PLAYER_ID']):{'id':str(p['PLAYER_ID']),'name':p['PLAYER_NAME'],'team':p['TEAM_ABBREVIATION'],'eligible':[],'status':'active','games':1} for p in players}
    for ts in data['teams'].values():
        for r in ts:pool[identity(r)]=r
    with st.expander('編輯共用名單／3 席 IL'):
        st.caption('儲存後同步總覽、9-Cat、觀察室、補強、交易與模擬。若加入其他隊球員，會更新這份私人聯盟紀錄；不會操作 Yahoo。')
        chosen=st.multiselect('名單球員（輸入姓名搜尋）',list(pool),default=[identity(r) for r in rows],format_func=lambda k:pool[k]['name'],key=key+'_members_'+str(data['revision']))
        il=st.multiselect('IL（最多 3 位）',chosen,default=[identity(r) for r in rows if r.get('status')=='IL' and identity(r) in chosen],format_func=lambda k:pool[k]['name'],max_selections=3,key=key+'_il_'+str(data['revision']))
        if st.button('儲存共用名單',key=key+'_save'):
            try:
                save_team(entries,team,[dict(pool[k],status='IL' if k in il else 'active') for k in chosen]);st.rerun()
            except ValueError as exc:st.error(str(exc))
        unknown=[r for r in rows if not r.get('eligible')]
        if unknown:st.caption('新增球員位置若尚未確認，補強引擎只排 UTIL；請於下方補齊資格。')
        with st.form(key+'_positions'):
            updated=[]
            for r in rows:
                pos=st.multiselect(r['name']+' · 位置',['PG','SG','SF','PF','C'],default=[p for p in r.get('eligible',[]) if p in ['PG','SG','SF','PF','C']],key=key+'_pos_'+identity(r)+'_'+str(data['revision']))
                updated.append(dict(r,eligible=pos))
            if st.form_submit_button('儲存位置資格'):
                save_team(entries,team,updated);st.rerun()


def render_roster_source():
    from ninecat_strategy import load_data
    from datetime import datetime
    from zoneinfo import ZoneInfo
    _,entries=load_data();league=state(entries);team=active_team(entries)
    rows=roster(entries,team);source=league.get('roster_sources',{}).get(team,{})
    kind=source.get('kind','draft')
    count=f"{len(rows)} 人／IL {sum(r.get('status')=='IL' for r in rows)} 人"
    if kind=='draft':
        st.warning(f'{team_label(team)} · {count} · 目前仍是選秀初始名單，尚未套用 Yahoo 最新名單。請到「聯盟同步」同步或完成首次配對。')
    else:
        label={'yahoo':'Yahoo 同步','manual':'手動調整','file':'檔案匯入'}.get(kind,'私人名單')
        stamp=source.get('updated_at','')
        try:stamp=datetime.fromisoformat(stamp.replace('Z','+00:00')).astimezone(ZoneInfo('Asia/Taipei')).strftime('%m/%d %H:%M')+' 台灣時間'
        except (ValueError,AttributeError):pass
        source_team=source.get('source_team','').split(':')[-1]
        display_name=team_label(team)
        st.caption(f"名單來源：{label} · {display_name} · {count} · 陣容日期 {source.get('date','未指定')} · 最後套用 {stamp or '未記錄'}")
