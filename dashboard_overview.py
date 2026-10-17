from app_storage import private_path
"""Roster overview with calendar, nine pies and explainable period MVP."""
import html
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import altair as alt
import pandas as pd
import streamlit as st

from dashboard_model import week_bounds, regular_schedule, draft_roster, production, totals, mvp_scores, aggregate_logs, trend
from ninecat_model import CATS, KEYS, LABELS, norm, cohort_ids, baseline, value
from ninecat_strategy import load_data, STATE

ROOT = Path(__file__).resolve().parent
COLORS = ['#5b9ff5','#ed8958','#59c4a4','#bf91ef','#f0c66b','#ef8fb0','#7fd1e2',
          '#a5c46b','#dc786d','#8eaae0','#c5aa88','#8fd2b4','#c390c4','#dbc56b','#78b7b9','#c6b0f0']


@st.cache_data(ttl=3600)
def load_schedule():
    return regular_schedule(json.loads((ROOT/'nba_schedule_2026_27.json').read_text(encoding='utf-8')))


@st.cache_data(ttl=1800)
def fetch_actual(season, start, end):
    from nba_api.stats.endpoints import leaguedashplayerstats
    frame = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season, season_type_all_star='Regular Season', per_mode_detailed='Totals',
        date_from_nullable=start.strftime('%m/%d/%Y'), date_to_nullable=end.strftime('%m/%d/%Y'), timeout=15).get_data_frames()[0]
    if frame.empty:
        return []
    if frame['PLAYER_ID'].duplicated().any():
        raise ValueError('官方回傳重複球員，暫停加總以避免重複計分。')
    fields = ['PLAYER_ID','PLAYER_NAME','TEAM_ABBREVIATION','GP',*KEYS]
    return json.loads(frame[fields].to_json(orient='records'))


def actual_period(start, end, force=False):
    cache = ROOT/'dashboard_weekly_cache'/f'2026-27_{start}_{end}.json'
    if force:
        fetch_actual.clear()
    try:
        records = fetch_actual('2026-27', start, end)
        stamp = datetime.now(ZoneInfo('Asia/Singapore')).isoformat()
        if records:
            try:
                cache.parent.mkdir(exist_ok=True)
                temp = cache.with_suffix('.tmp')
                temp.write_text(json.dumps({'season':'2026-27','start':str(start),'end':str(end),
                                             'fetched_at':stamp,'players':records}, ensure_ascii=False), encoding='utf-8')
                temp.replace(cache)
            except OSError:
                st.caption('本次實績已取得，但本機快取無法寫入。')
        return records, stamp, False
    except Exception as exc:
        if cache.exists():
            saved = json.loads(cache.read_text(encoding='utf-8'))
            st.warning(f"NBA暫時無法連線，使用本機實績快取（{saved['fetched_at']}）。")
            return saved['players'], saved['fetched_at'], True
        st.warning(f'無法取得NBA實績：{type(exc).__name__}。不以估算冒充實績，請稍後重試。')
        return [], '', True


def pie_chart(rows, cat, names, ref):
    column = cat+'M' if cat in ('FG','FT') else cat
    total = sum(r['tot'][column] for r in rows)
    if total <= 0:
        return None
    records = []
    for r in rows:
        amount = r['tot'][column]
        if amount <= 0:
            continue
        item = {'球員':r['name'],'產量':amount,'占比':amount/total,'計分場次':r['gp']}
        if cat in ('FG','FT'):
            att = r['tot'][cat+'A']
            item['命中率'] = amount/att if att else 0
            item['命中率Impact'] = amount-ref[cat]['mean']*att
        records.append(item)
    base = alt.Chart(pd.DataFrame(records)).encode(
        theta=alt.Theta('產量:Q',stack=True),
        color=alt.Color('球員:N',scale=alt.Scale(domain=names,range=[COLORS[i % len(COLORS)] for i in range(len(names))]),legend=None),
        order=alt.Order('球員:N',sort='ascending'))
    tooltip = [alt.Tooltip('球員:N'),alt.Tooltip('產量:Q',format='.1f'),alt.Tooltip('占比:Q',format='.1%'),alt.Tooltip('計分場次:Q')]
    if cat in ('FG','FT'):
        tooltip += [alt.Tooltip('命中率:Q',format='.1%'),alt.Tooltip('命中率Impact:Q',format='+.2f')]
    arcs = base.mark_arc(innerRadius=48,outerRadius=95,stroke='#0b1020',strokeWidth=1).encode(tooltip=tooltip)
    labels = base.mark_text(radius=73,size=11,color='#ffffff',fontWeight=600).encode(
        text=alt.condition('datum.占比 >= 0.08',alt.Text('占比:Q',format='.0%'),alt.value('')),color=alt.value('#ffffff'))
    center = value(totals(rows),cat) if cat in ('FG','FT') else total
    text = f'{center:.1%}' if cat in ('FG','FT') else f'{total:,.1f}'
    middle = alt.Chart(pd.DataFrame([{'text':text}])).mark_text(color='#f1f5f9',fontSize=17,fontWeight=700).encode(text='text:N')
    return (arcs+labels+middle).properties(height=220).configure_view(stroke=None).configure(background='#0b1020')


def render_dashboard():
    st.subheader('球隊總覽 · 九項貢獻')
    snapshot, entries = load_data()
    players = snapshot['players']
    ref = baseline(players,cohort_ids(players,entries,'draft'))
    season = st.selectbox('賽季', ['2025-26','2026-27'], key='dash_season')
    logs = json.loads((ROOT/'ninecat_assets/game_logs_2025_26.json').read_text()) if season == '2025-26' else []
    first = date(2025,10,21) if logs else date(2026,10,20)
    last = date(2026,4,12) if logs else date(2027,4,11)
    default_day = first
    schedule = {}
    today = datetime.now(ZoneInfo('America/New_York')).date()
    teams = list(dict.fromkeys(e['fantasyTeam'] for e in entries))
    choice = st.selectbox('查看球隊',teams+['我的9-Cat自訂名單'],key='dash_team')
    if choice == '我的9-Cat自訂名單':
        custom = st.session_state.get('nc_roster')
        if custom is None and private_path(STATE).exists():
            try:
                custom = json.loads(private_path(STATE).read_text(encoding='utf-8')).get('roster',[])
            except (OSError,ValueError):
                custom = []
        team_by_name = {norm(r['name']):r['team'] for t in teams for r in draft_roster(entries,t)}
        old_team = {norm(p['PLAYER_NAME']):p['TEAM_ABBREVIATION'] for p in players}
        roster = [{**r,'team':team_by_name.get(norm(r['name']),old_team.get(norm(r['name']),''))} for r in custom or []]
    else:
        roster = draft_roster(entries,choice)
    if not roster:
        st.info('目前沒有名單；請先到9-Cat分頁載入或建立我的球隊。')
        return
    calendars = st.columns([1,1,2])
    day = calendars[0].date_input('小月曆 · 選擇日期',value=default_day,
                                 min_value=week_bounds(first)[0],max_value=week_bounds(last)[1],key='dash_date_'+season,format='YYYY/MM/DD')
    granularity = calendars[1].radio('查看範圍',['當週','單日'],horizontal=True,key='dash_range')
    calendars[2].caption('NBA 真實單場紀錄｜美國比賽日；不使用整季場均推估。')
    monday,sunday = week_bounds(day)
    week = (monday-week_bounds(first)[0]).days//7+1
    start,end = (monday,sunday) if granularity == '當週' else (day,day)
    st.markdown(f'**{season} · Week {week}｜{start:%m/%d}–{end:%m/%d}**')
    with st.expander('手動排除／IL'):
        names=[r['name'] for r in roster]
        excluded=st.multiselect('本期不納入圖表與MVP',names,default=[r['name'] for r in roster if r.get('status') in ('IL','bench')],key='dash_exclude_actual_'+choice)
        st.caption('以目前這份名單回看 NBA 實際出賽；尚未重建歷史交易及每日 Fantasy 先發席位。')
    if logs:
        records = aggregate_logs(logs,start,end)
        week_records = aggregate_logs(logs,monday,sunday)
        previous_records = aggregate_logs(logs,monday-timedelta(days=7),monday-timedelta(days=1))
        st.caption(f'已載入 2025–26 例行賽 {len(logs):,} 筆單場紀錄；2025/10/21–2026/04/12。')
    elif start > today:
        records,week_records,previous_records = [],[],[]
        st.info('所選期間尚未開始，沒有實績。')
    else:
        refresh=st.button('更新NBA實績',key='dash_refresh')
        records,_,_=actual_period(start,min(end,today),refresh)
        week_records,_,_=actual_period(monday,min(sunday,today))
        previous_records,_,_=actual_period(monday-timedelta(days=7),monday-timedelta(days=1))
    rows=production(roster,players,schedule,start,end,excluded,actual=records)
    weekly=production(roster,players,schedule,monday,sunday,excluded,actual=week_records)
    prev=production(roster,players,schedule,monday-timedelta(days=7),monday-timedelta(days=1),excluded,actual=previous_records)
    previous={r['name']:r for r in prev}
    trends={r['name']:trend(r,previous.get(r['name']),ref) for r in weekly}
    record_map={norm(r['PLAYER_NAME']):r for r in records}
    known_names={norm(g['PLAYER_NAME']) for g in logs}
    for r in rows:
        if logs and norm(r['name']) not in known_names and not r['excluded']:
            r.update(covered=False,reason='無2025–26出賽資料')
        if norm(r['name']) in record_map:
            r['team']=record_map[norm(r['name'])]['TEAM_ABBREVIATION']
    total=totals(rows)
    scores=mvp_scores(rows,ref)
    if scores:
        winner=scores[0]
        winner_row=next(r for r in rows if r['name']==winner['name'])
        statline=' · '.join(f"{LABELS[c]} {winner_row['tot'][c]:g}" for c in ('PTS','REB','AST','STL','BLK'))
        photo_record=record_map.get(norm(winner['name']))
        photo_id=str(photo_record['PLAYER_ID']) if photo_record else ''
        with st.expander('MVP 評分與趨勢說明',expanded=False):
            st.caption('MVP採當期九項等權累積標準化貢獻；TO反向、FG/FT以出手量Impact計算。標準化尺度仍使用2025–26選秀母體；所有產量均為所選期間實績。')
            st.caption('📈／📉：整週每場九項綜合貢獻對比前週，➖為持平；🆕為前週未出賽。單日檢視也顯示所屬整週趨勢；未完賽週僅比較目前已發生場次。')
        photo_url=f'https://cdn.nba.com/headshots/nba/latest/1040x760/{photo_id}.png' if photo_id.isdigit() else ''
        photo_html=(f'<div class="mvp-photo"><img class="portrait" src="{html.escape(photo_url,quote=True)}" alt="{html.escape(winner['name'],quote=True)} MVP 球員照"></div>' if photo_url else '')
        hero=f"""<style>
.mvp-body{{display:flex;align-items:center;gap:16px;justify-content:space-between}}
.mvp-copy{{flex:1;min-width:0}}
.mvp-photo{{flex:0 0 30%;max-width:210px;align-self:stretch;display:flex;align-items:center;overflow:hidden}}
.mvp-photo img{{width:100%;height:148px;object-fit:contain;border-radius:10px}}
@media(max-width:600px){{.mvp-body{{gap:8px}}.mvp-photo{{flex-basis:30%;min-width:85px}}.mvp-photo img{{height:130px}}}}
</style><div style="background:linear-gradient(120deg,#17243e,#183d42);border:1px solid #c8ad61;border-radius:14px;padding:16px 18px;margin:8px 0;color:#f3f6fc"><div class="mvp-body"><div class="mvp-copy">
<div style="color:#edcd79;font-size:10px;letter-spacing:2px">🏆 PLAYER OF THE {'WEEK' if granularity=='當週' else 'DAY'}</div>
<div style="font-size:25px;font-weight:800;margin:6px 0;overflow-wrap:anywhere">{html.escape(winner['name'])}</div>
<div style="color:#c8e6e3;font-size:12px">{html.escape(statline)}</div>
<div style="margin-top:8px;color:#f3d987;font-size:12px">貢獻分 {winner['score']:+.3f}　｜　{winner['gp']} 場　｜　全隊 {total['g']} 球員出賽場次</div>
<div style="margin-top:6px;color:#d4dfed;font-size:12px">週場均趨勢 {html.escape(trends[winner['name']])}</div></div>{photo_html}</div></div>"""
        st.markdown(hero,unsafe_allow_html=True)
        if len(scores)>1:
            st.caption('追趕者：'+'　 · 　'.join(f"{i+2}. {r['name']}（{r['score']:+.3f}）" for i,r in enumerate(scores[1:3])))
    else:
        st.info('🏆 本期尚無可評選的出賽紀錄。')
    legend=' '.join('<span style="display:inline-flex;align-items:center;gap:5px;margin:3px 12px 3px 0;color:#edf3fb;font-size:12px"><span style="background:'+COLORS[i%len(COLORS)]+';width:9px;height:9px;border-radius:50%;display:inline-block"></span>'+html.escape(r['name'])+'</span>' for i,r in enumerate(rows))
    st.markdown(legend,unsafe_allow_html=True)
    chart_names=[r['name'] for r in rows]
    for offset in range(0,9,3):
        columns=st.columns(3)
        for container,cat in zip(columns,CATS[offset:offset+3]):
            with container:
                title=LABELS[cat]+({'FG':' · 投籃命中占比','FT':' · 罰球命中占比','TOV':' · 失誤負擔'}.get(cat,''))
                st.markdown('**'+title+'**')
                chart=pie_chart(rows,cat,chart_names,ref)
                if chart is None:
                    st.caption('本期沒有可計算的產量。')
                else:
                    st.altair_chart(chart,width='stretch',theme=None)
                if cat=='TOV':
                    st.caption('占比越大＝失誤負擔越多；MVP評分會反向計算。')
                elif cat in ('FG','FT'):
                    st.caption('圓心為全隊命中率；扇形為命中數占比。滑鼠移上可看個人命中率及Impact。')
    with st.expander('MVP票選依據 · 各項貢獻分'):
        st.dataframe(pd.DataFrame([{'球員':s['name'],'場次':s['gp'],'綜合分':round(s['score'],3),
                                    **{LABELS[c]:round(s['parts'][c],3) for c in CATS}} for s in scores]),hide_index=True,width='stretch')
    st.markdown('#### 本期球員名單與產量')
    score_map={r['name']:r['score'] for r in scores}
    table=[]
    for r in rows:
        item={'球員':r['name'],'NBA球隊':r['team'],'場次':r['gp'] if r['covered'] else None,'狀態':r['reason'],
              **{LABELS[c]:round(r['tot'][c],1) if r['covered'] else None for c in CATS if c not in ('FG','FT')}}
        for c in ('FG','FT'):
            item[LABELS[c]]=f"{r['tot'][c+'M']/r['tot'][c+'A']:.1%}" if r['covered'] and r['tot'][c+'A'] else '—'
        item['週場均趨勢']=trends[r['name']]
        item['MVP分']=round(score_map[r['name']],3) if r['name'] in score_map else None
        table.append(item)
    st.dataframe(pd.DataFrame(table),hide_index=True,width='stretch')
    with st.expander('各項場均與前週比較 📈 / 📉'):
        comparison=[]
        for r in weekly:
            old=previous.get(r['name'])
            item={'球員':r['name'],'本週場次':r['gp'],'前週場次':old['gp'] if old else 0}
            for c in CATS:
                x=value({'g':r['gp'],'tot':r['tot']},c)
                y=value({'g':old['gp'],'tot':old['tot']},c) if old else None
                if x is None:
                    item[LABELS[c]]='—'
                elif y is None:
                    item[LABELS[c]]=(f'{x:.1%}' if c in ('FG','FT') else f'{x:.2f}')+' 🆕'
                else:
                    d=x-y
                    better=-d if c=='TOV' else d
                    icon='📈' if better>0.00001 else '📉' if better < -0.00001 else '➖'
                    item[LABELS[c]]=(f'{x:.1%} ({d*100:+.1f}pp)' if c in ('FG','FT') else f'{x:.2f} ({d:+.2f})')+' '+icon
            comparison.append(item)
        st.dataframe(pd.DataFrame(comparison),hide_index=True,width='stretch')
        st.caption('每項以本週總數÷實際出賽場次；FG/FT為總命中÷總出手。TO越低越好。pp代表百分點。')
    st.download_button('下載本期名單與貢獻CSV',pd.DataFrame(table).to_csv(index=False).encode('utf-8-sig'),f'overview_{start}_{end}.csv','text/csv')
