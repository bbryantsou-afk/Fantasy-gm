from page_guidance import caption as page_caption
from app_storage import private_path
"""Shared roster selection, persistent watch stars, and public news."""
import json,re,html
from pathlib import Path
from urllib.parse import quote
import xml.etree.ElementTree as ET
import requests
import streamlit as st
from ninecat_strategy import load_data,STATE
from ninecat_model import norm
from dashboard_model import draft_roster

ROOT=Path(__file__).resolve().parent
WATCH=ROOT/'player_watchlist.json'

def load_stars():
    try:
        return json.loads(private_path(WATCH).read_text()).get('ids',[])
    except (OSError,ValueError):
        return []

def save_stars(ids):
    temp=private_path(WATCH).with_suffix('.tmp')
    temp.write_text(json.dumps({'ids':list(dict.fromkeys(ids))},ensure_ascii=False))
    temp.replace(private_path(WATCH))

def star_picker(players,key,show_help=True):
    ids={str(p['PLAYER_ID']):p['PLAYER_NAME'] for p in players}
    def changed():
        selected=list(st.session_state[key]);save_stars(selected)
        for other in ('watch_stars','nc_watch_stars'):
            if other!=key:st.session_state[other]=selected
        if st.session_state.get('_account_loaded'):
            from account_store import persist_account
            try:persist_account()
            except (ValueError,KeyError,TypeError) as exc:st.session_state['_account_save_error']='星號尚未上傳：'+str(exc)
    selected=st.multiselect('⭐ 加星追蹤球員（輸入姓名，可多選）',sorted(ids,key=lambda k:norm(ids[k])),default=[k for k in load_stars() if k in ids],format_func=ids.get,key=key,on_change=changed)

    return selected

def choose_roster(entries,key):
    from roster_store import choose_team,roster
    return roster(entries,choose_team(entries,key))

def profiles(players,entries):
    draft={str(e['playerId']):e for e in entries if e.get('playerId') is not None}
    out={}
    for p in players:
        e=draft.get(str(p['PLAYER_ID']),{})
        match=re.search(r'\((\w+)\s*-\s*([^)]*)',e.get('position',''))
        positions=set(match.group(2).split(',')) if match else set()
        out[str(p['PLAYER_ID'])]={**p,'team':match.group(1) if match else p['TEAM_ABBREVIATION'],
                                  'eligible':positions,'fantasyTeam':e.get('fantasyTeam','未在原始選秀名單'),'draft_round':e.get('round')}
    from roster_store import state, identity
    league=state(entries)
    for k,meta in league.get('player_meta',{}).items():
        if k in out:
            out[k]['team']=meta.get('team') or out[k]['team']
            out[k]['eligible']=set(meta.get('eligible',out[k]['eligible']))
    for team,rows in league['teams'].items():
        for r in rows:
            k=identity(r)
            if k in out:
                out[k]['team']=r.get('team') or out[k]['team']
                out[k]['fantasyTeam']=team
                if r.get('eligible'):out[k]['eligible']=set(r['eligible'])
    return out

def news_time(value):
    from email.utils import parsedate_to_datetime
    from zoneinfo import ZoneInfo
    try:
        return parsedate_to_datetime(value).astimezone(ZoneInfo('Asia/Taipei')).strftime('%d/%m/%Y %H:%M')
    except (ValueError,TypeError,OverflowError):
        return ''

@st.cache_data(ttl=604800,show_spinner=False)
def chinese_headline(title):
    # Translate public headlines only; no account or league data is sent.
    if not re.search(r'[A-Za-z]{3}',title):return title
    response=requests.get('https://translate.googleapis.com/translate_a/single',params={'client':'gtx','sl':'auto','tl':'zh-TW','dt':'t','q':title},timeout=5)
    response.raise_for_status()
    translated=''.join(part[0] for part in response.json()[0] if part and part[0])
    if not translated:raise ValueError('Empty translation')
    return translated

def translated_news(items):
    from concurrent.futures import ThreadPoolExecutor
    def translate(item):
        result=dict(item)
        try:result['title']=chinese_headline(item['title'])
        except (requests.RequestException,ValueError,TypeError,IndexError,KeyError):
            result['translation_failed']=True
        return result
    with ThreadPoolExecutor(max_workers=6) as executor:
        return list(executor.map(translate,items))

@st.cache_data(ttl=1800,show_spinner=False)
def player_news(name):
    query=quote('"'+name+'" NBA basketball when:14d')
    r=requests.get('https://news.google.com/rss/search?q='+query+'&hl=en-US&gl=US&ceid=US:en',timeout=8)
    r.raise_for_status()
    root=ET.fromstring(r.content)
    return [{'title':i.findtext('title',''),'url':i.findtext('link',''),
             'published':i.findtext('pubDate',''),'source':i.findtext('source','')} for i in root.findall('./channel/item')[:6]]

@st.cache_data(ttl=86400,show_spinner=False)
def player_bio(pid):
    from nba_api.stats.endpoints.commonplayerinfo import CommonPlayerInfo
    frames=CommonPlayerInfo(player_id=pid,timeout=12).get_data_frames()
    return frames[0].to_dict('records')[0] if not frames[0].empty else {}

def render_watchroom():
    from roster_store import active_team,ownership,availability,editor,identity
    snapshot,entries=load_data();players=snapshot['players']
    with st.container(key='watch_controls'):
        controls=st.columns([1.1,1.1,2])
        with controls[0]:roster=choose_roster(entries,'watch_team')
        with controls[1]:view=st.radio('觀察範圍',['全部','我的球員','星號追蹤'],horizontal=True,key='watch_scope')
        with controls[2]:star_picker(players,'watch_stars',show_help=False)
    team=active_team(entries);pool=profiles(players,entries)
    mine={identity(r):r['name'] for r in roster};stars=load_stars()
    with st.expander('名單管理／備份'):
        editor(entries,players,team,'watch_roster')
        st.download_button('下載加星名單備份',json.dumps({'ids':stars}),'player_watchlist.json','application/json')
    ids=list(dict.fromkeys(list(mine)+stars)) if view=='全部' else list(mine) if view=='我的球員' else stars
    names={**{str(p['PLAYER_ID']):p['PLAYER_NAME'] for p in players},**mine}
    if not ids:st.info('目前沒有球員；可先選擇球隊或加星追蹤。');return
    mobile=st.session_state.get('device_view')=='手機版'
    per_row=4 if mobile else 10
    def open_player(player):st.session_state['watch_open']=player
    st.markdown(f'<style>.st-key-watch_grid{{grid-template-columns:repeat({per_row},minmax(0,1fr))!important}}</style>',unsafe_allow_html=True)
    with st.container(key='watch_grid'):
        for i,k in enumerate(ids):
            p=pool.get(k);name=names.get(k,'未知球員')
            with st.container(border=True,key='watch_card_'+str(i)):
                from player_portraits import portrait_id
                photo_id=portrait_id({'name':name,'id':k})
                portrait=(f'<img src="https://cdn.nba.com/headshots/nba/latest/260x190/{photo_id}.png" alt="">' if photo_id.isdigit() else '🏀')
                meta=(p['team']+' · '+('/'.join(sorted(p['eligible'])) or '位置待確認')) if p else '新秀／資料待補'
                extra='' if mobile else '<div class="watch-availability">'+html.escape(availability(entries,team,k))+'</div>'
                st.markdown('<div class="watch-card-content"><div class="watch-portrait">'+portrait+'</div><div class="watch-name">'+html.escape(name+(' ⭐' if k in stars else ''))+'</div><div class="watch-meta">'+html.escape(meta)+'</div>'+extra+'</div>',unsafe_allow_html=True)
                st.button('⋯' if mobile else '⋯ 展開',use_container_width=True,help='展開 '+name+' 的新聞與資料',key='watch_expand_'+k,on_click=open_player,args=(k,))
            # Insert details immediately after the row containing the selected card.
            if (i+1)%per_row==0 or i==len(ids)-1:
                selected=st.session_state.get('watch_open')
                row_start=(i//per_row)*per_row
                if selected in ids[row_start:i+1]:
                    with st.container(border=True,key='watch_detail_'+str(i//per_row)):
                        if st.button('收起',key='watch_collapse'):
                            st.session_state.pop('watch_open',None);st.rerun()
                        show_player_detail(selected,pool,names)


def show_player_detail(selected,pool,names):
    p=pool.get(selected)
    name=p['PLAYER_NAME'] if p else names.get(selected,'')
    st.markdown('### '+name)
    from player_portraits import portrait_id
    photo_id=portrait_id({'name':name,'id':selected})
    if photo_id.isdigit():
        cols=st.columns([1,1])
        cols[0].markdown(f'<div class="watch-detail-portrait"><img src="https://cdn.nba.com/headshots/nba/latest/260x190/{photo_id}.png" alt="球員頭像"></div>',unsafe_allow_html=True)
        cols[1].link_button('NBA 官方球員頁',f'https://www.nba.com/player/{photo_id}')
        if p:
            st.markdown('<div class="watch-detail-stats">2025–26｜'+' · '.join([f"FG% {p['FGM']/p['FGA']:.1%}" if p['FGA'] else 'FG% —',f"FT% {p['FTM']/p['FTA']:.1%}" if p['FTA'] else 'FT% —',f"3PT {p['FG3M']}",f"PTS {p['PTS']}",f"REB {p['REB']}",f"AST {p['AST']}",f"ST {p['STL']}",f"BLK {p['BLK']}",f"TO {p['TOV']}"])+'</div>',unsafe_allow_html=True)
        if st.button('基本資料'):
            try:
                b=player_bio(selected)
                labels={'POSITION':'NBA位置','HEIGHT':'身高（英尺／英吋）','WEIGHT':'體重（磅）','BIRTHDATE':'生日','COUNTRY':'國家','SCHOOL':'學校','DRAFT_YEAR':'選秀年份','DRAFT_ROUND':'輪次','DRAFT_NUMBER':'順位','TEAM_NAME':'官方球隊'}
                st.table([{'基本資料':label,'內容':str(b.get(k) or '—')} for k,label in labels.items()])
            except Exception:
                st.info('官方基本資料暫時無法連線，請使用官方球員頁。')
    st.markdown('#### 近14天新聞')
    def refresh_news():
        player_news.clear(name)
        st.session_state['_watch_news_refreshed']=selected
    st.button('更新新聞',key='watch_refresh_news_'+selected,on_click=refresh_news)
    try:
        with st.spinner('整理新聞…'):
            news=translated_news(player_news(name))
        if st.session_state.pop('_watch_news_refreshed',None)==selected:
            st.success('新聞已重新讀取。')
        if not news:
            st.info('近14天未找到相關新聞。')
        for n in news:
            st.link_button(n['title'],n['url'])
            st.caption(news_time(n['published']))
            if n.get('translation_failed'):st.caption('翻譯暫時無法連線，先顯示原標題。')
    except Exception:
        st.warning('新聞來源暫時無法讀取。')
        st.link_button('開啟新聞搜尋','https://news.google.com/search?q='+quote(name+' NBA'))
