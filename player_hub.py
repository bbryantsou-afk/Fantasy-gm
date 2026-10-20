from app_storage import private_path
"""Shared roster selection, persistent watch stars, and public news."""
import json,re
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

def star_picker(players,key):
    ids={str(p['PLAYER_ID']):p['PLAYER_NAME'] for p in players}
    selected=st.multiselect('⭐ 加星追蹤球員（輸入姓名，可多選）',sorted(ids,key=lambda k:norm(ids[k])),default=[k for k in load_stars() if k in ids],format_func=ids.get,key=key)
    if st.button('儲存加星名單',key=key+'_save'):
        save_stars(selected)
        st.success('已儲存在本機；觀察室會一起顯示我的球員與加星球員。')
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

def news_tone(title):
    """Conservative headline hints, not an injury or availability assessment."""
    text=title.lower()
    if re.search(r'\b(could|may|might|unlikely|rumou?r|not ruled out|potential)\b',text):
        return '⚪', '中性／待確認'
    positive=bool(re.search(r'\b(career[- ]high|season[- ]high|cleared to play|available to play|returns to action|full practice|will play|breakout)\b|復出|獲准出賽|生涯新高|傷癒',text))
    negative=bool(re.search(r'\b(ruled out|will miss|injury|injured|surgery|suspended|suspension|setback|out for|doubtful)\b|受傷|缺席|手術|禁賽',text))
    if positive and not negative:return '🟢','正面訊號'
    if negative and not positive:return '🔴','負面訊號'
    return '⚪','中性／待確認'

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
    st.subheader('⭐ 球員觀察室')
    snapshot,entries=load_data();players=snapshot['players']
    roster=choose_roster(entries,'watch_team');team=active_team(entries)
    editor(entries,players,team,'watch_roster')
    pool=profiles(players,entries)
    with st.expander('管理加星名單'):
        star_picker(players,'watch_stars')
        st.download_button('下載加星名單備份',json.dumps({'ids':load_stars()}),'player_watchlist.json','application/json')
    mine={identity(r):r['name'] for r in roster};stars=load_stars()
    view=st.radio('觀察範圍',['全部','我的球員','星號追蹤'],horizontal=True,key='watch_scope')
    ids=list(dict.fromkeys(list(mine)+stars)) if view=='全部' else list(mine) if view=='我的球員' else stars
    names={**{str(p['PLAYER_ID']):p['PLAYER_NAME'] for p in players},**mine}
    st.caption('頭像卡只顯示重點；按「⋯ 展開」才讀取新聞與完整資料。歸屬依這份共用聯盟紀錄，不代表已與 Yahoo 同步。')
    if not ids:st.info('目前沒有球員；可先選擇球隊或加星追蹤。');return
    with st.container(key='watch_grid'):
        for i,k in enumerate(ids):
            p=pool.get(k);name=names.get(k,'未知球員')
            with st.container(border=True,key="watch_card_"+str(i)):
                if k.isdigit():st.image(f'https://cdn.nba.com/headshots/nba/latest/260x190/{k}.png',width=85)
                else:st.markdown('### 🏀')
                st.markdown('**'+name+(' ⭐' if k in stars else '')+'**')
                st.caption((p['team']+' · '+('/'.join(sorted(p['eligible'])) or '位置待確認')) if p else '新秀／資料待補')
                st.caption(availability(entries,team,k))
                if st.button('⋯ 展開',key='watch_expand_'+k):st.session_state['watch_open']=k
    selected=st.session_state.get('watch_open')
    if selected in ids:
        with st.container(border=True):
            if st.button('收起詳細資料',key='watch_collapse'):
                st.session_state.pop('watch_open',None);st.rerun()
            show_player_detail(selected,pool,names)


def show_player_detail(selected,pool,names):
    p=pool.get(selected)
    name=p['PLAYER_NAME'] if p else names.get(selected,'')
    st.markdown('### '+name)
    if selected.isdigit():
        cols=st.columns([1,3])
        cols[0].image(f'https://cdn.nba.com/headshots/nba/latest/260x190/{selected}.png',width=130)
        cols[1].link_button('NBA 官方球員頁',f'https://www.nba.com/player/{selected}')
        if p:
            cols[1].write(f"2025–26｜PTS {p['PTS']} · REB {p['REB']} · AST {p['AST']} · STL {p['STL']} · BLK {p['BLK']}")
        if st.button('載入官方基本資料（身高、年齡、選秀）'):
            try:
                b=player_bio(selected)
                labels={'POSITION':'NBA位置','HEIGHT':'身高（英尺／英吋）','WEIGHT':'體重（磅）','BIRTHDATE':'生日','COUNTRY':'國家','SCHOOL':'學校','DRAFT_YEAR':'選秀年份','DRAFT_ROUND':'輪次','DRAFT_NUMBER':'順位','TEAM_NAME':'官方球隊'}
                st.table([{'基本資料':label,'內容':str(b.get(k) or '—')} for k,label in labels.items()])
            except Exception:
                st.info('官方基本資料暫時無法連線，請使用官方球員頁。')
    st.markdown('#### 近14天新聞')
    st.caption('🟢 正面訊號 · 🔴 負面訊號 · ⚪ 中性／待確認。依標題關鍵字初步標示，請點原文確認，不代表確定出賽狀態。')
    if st.button('更新這位球員的新聞',key='watch_refresh_news'):
        player_news.clear()
    try:
        with st.spinner('整理新聞…'):
            news=player_news(name)
        if not news:
            st.info('近14天未找到相關新聞。')
        for n in news:
            emoji, tone = news_tone(n['title'])
            st.link_button(emoji+' '+n['title'],n['url'])
            st.caption(tone+' · '+n['source']+' · '+n['published'])
    except Exception:
        st.warning('新聞來源暫時無法讀取。')
        st.link_button('開啟新聞搜尋','https://news.google.com/search?q='+quote(name+' NBA'))
