from page_guidance import caption as page_caption
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
    light = st.session_state.get('visual_theme') == '簡約淺色'
    chart_bg = '#f7f8fa' if light else '#0b1020'
    arcs = base.mark_arc(innerRadius=alt.ExprRef(expr='min(width/2-5,66)*0.5'),outerRadius=alt.ExprRef(expr='min(width/2-5,66)'),stroke=chart_bg,strokeWidth=1).encode(tooltip=tooltip)
    labels = base.mark_text(radius=alt.ExprRef(expr='min(width/2-5,66)*0.77'),size=9,color='#ffffff',fontWeight=600).encode(
        text=alt.condition('datum.占比 >= 0.08',alt.Text('占比:Q',format='.0%'),alt.value('')),color=alt.value('#ffffff'))
    center = value(totals(rows),cat) if cat in ('FG','FT') else total
    text = f'{center:.1%}' if cat in ('FG','FT') else f'{total:,.1f}'
    middle = alt.Chart(pd.DataFrame([{'text':text}])).mark_text(color='#243746' if light else '#f1f5f9',fontSize=12,fontWeight=700).encode(text='text:N')
    return (arcs+labels+middle).properties(height=150).configure_view(stroke=None).configure(background='transparent')


def mobile_pie(rows,cat,ref,names):
    """Static SVG has no floating Vega tooltip or touch menu to leave behind."""
    import math
    column=cat+'M' if cat in ('FG','FT') else cat
    total=sum(r['tot'][column] for r in rows)
    if total<=0:return None
    circ=2*math.pi*42;offset=0;parts=[]
    for r in rows:
        amount=r['tot'][column]
        if amount<=0:continue
        share=amount/total;length=circ*share
        color=COLORS[names.index(r['name'])%len(COLORS)]
        parts.append(f'<circle cx="60" cy="60" r="42" fill="none" stroke="{color}" stroke-width="20" stroke-dasharray="{length} {circ-length}" stroke-dashoffset="{-offset}" transform="rotate(-90 60 60)"/>')
        offset+=length
    center=value(totals(rows),cat) if cat in ('FG','FT') else total
    text=f'{center:.1%}' if cat in ('FG','FT') else f'{total:,.1f}'
    return '<svg viewBox="0 0 120 120" role="img" aria-label="'+html.escape(LABELS[cat]+' 全隊 '+text)+'" style="display:block;width:100%;max-width:145px;margin:auto">'+''.join(parts)+'<text x="60" y="64" text-anchor="middle" fill="currentColor" font-size="12" font-weight="600">'+text+'</text></svg>'

def pie_details(rows,cat,ref):
    column=cat+'M' if cat in ('FG','FT') else cat
    total=sum(r['tot'][column] for r in rows)
    result=[]
    for r in rows:
        amount=r['tot'][column]
        if amount<=0:continue
        item={'球員':r['name'],'產量':round(amount,1),'占比':f'{amount/total:.1%}','計分場次':r['gp']}
        if cat in ('FG','FT'):
            att=r['tot'][cat+'A']
            item.update({'命中／出手':f'{amount:g}/{att:g}','命中率':f'{amount/att:.1%}' if att else '—','Impact':round(amount-ref[cat]['mean']*att,3)})
        result.append(item)
    return sorted(result,key=lambda x:x['產量'],reverse=True)


def render_dashboard():
    mobile=st.session_state.get('device_view')=='手機版'
    snapshot, entries = load_data()
    players = snapshot['players']
    ref = baseline(players,cohort_ids(players,entries,'draft'))
    with st.container(key='dashboard_controls'):
        controls=st.columns([.8,1.6,1.1,1])
    season = controls[0].selectbox('賽季', ['2026-27','2025-26'], key='dash_season')
    logs = json.loads((ROOT/'ninecat_assets/game_logs_2025_26.json').read_text()) if season == '2025-26' else []
    first = date(2025,10,21) if logs else date(2026,10,20)
    last = date(2026,4,12) if logs else date(2027,4,11)
    schedule = {}
    today = datetime.now(ZoneInfo('America/New_York')).date()
    default_day=first if logs else max(first,min(last,today))
    from roster_store import choose_team,roster as shared_roster,editor,state
    with controls[1]:choice=choose_team(entries,'dash_team','球隊')
    roster=shared_roster(entries,choice)
    if not roster:
        st.info('目前沒有名單；請先到9-Cat分頁載入或建立我的球隊。')
        return
    day = controls[2].date_input('小月曆 · 選擇日期',value=default_day,
                                 min_value=week_bounds(first)[0],max_value=week_bounds(last)[1],key='dash_date_'+season,format='YYYY/MM/DD')
    granularity = controls[3].radio('查看範圍',['當週','單日'],horizontal=True,key='dash_range')
    editor(entries,players,choice,'dashboard_roster')
    monday,sunday = week_bounds(day)
    week = (monday-week_bounds(first)[0]).days//7+1
    start,end = (monday,sunday) if granularity == '當週' else (day,day)
    league=state(entries)
    if not logs and start<=today<=end:
        from daily_evidence import refresh_live_page
        refresh_live_page()
        st.caption('今日實績約每 30 秒檢查可用來源。')
    st.markdown(f'**{season} · Week {week}｜{start:%m/%d}–{end:%m/%d}**')
    score_slot=st.empty()
    live=None
    excluded=[]
    unverified=[];reference_mode=False
    if logs:
        records = aggregate_logs(logs,start,end)
        week_records = aggregate_logs(logs,monday,sunday)
        previous_records = aggregate_logs(logs,monday-timedelta(days=7),monday-timedelta(days=1))
        st.caption(f'已載入 2025–26 例行賽 {len(logs):,} 筆單場紀錄；2025/10/21–2026/04/12。')
    elif start > today:
        records,week_records,previous_records = [],[],[]
        st.info('所選期間尚未開始，沒有實績。')
    else:
        from daily_evidence import fantasy_period,nba_today
        refresh=st.button('更新當期實績',key='dash_refresh')
        if refresh:nba_today.clear()
        # Fetch each elapsed date, not just today: a completed game remains visible tomorrow.
        days=[max(monday,first)+timedelta(days=i) for i in range(max(0,(min(sunday,today)-max(monday,first)).days+1))]
        if refresh:nba_today.clear()
        by_date={str(d):nba_today(str(d)) for d in days}
        live={'by_date':by_date,'error':'／'.join(sorted({v.get('error','') for v in by_date.values() if v.get('error')}))}

        today_feed=by_date.get(str(today),{})
        if start<=today<=end and today_feed.get('phase')=='pregame':
            st.caption(f'美東 {today:%m/%d} 賽事尚未開始；目前顯示所選期間已發生的實績，開賽後自動檢查更新。')
        elif start<=today<=end and today_feed.get('phase')=='no_games':
            st.caption(f'美東 {today:%m/%d} 沒有 NBA 賽程；目前顯示所選期間已發生的實績。')
        records,missing,source,stamp=fantasy_period(league,choice,max(start,first),end,today,live)
        from daily_evidence import unverified_period
        unverified=unverified_period(league,choice,max(start,first),end,today,by_date)
        if unverified:
            with st.expander('已取得 NBA 實績 · Fantasy 先發尚未確認',expanded=True):
                st.info('以下是目前名單球員的 NBA 真實數據；該日先發尚未同步，因此尚未計入 Fantasy 結算；若無先發實績，下方會顯示清楚標記的 NBA 名單參考及暫定 MVP。先發確認請至聯盟同步。')
                if mobile:
                    from mobile_stat_cards import player_rows
                    st.markdown(player_rows(unverified),unsafe_allow_html=True)
                else:st.dataframe(pd.DataFrame(unverified).rename(columns={'FG3M':'3PM','TOV':'TO'}),hide_index=True,width='stretch')
        week_records,_,_,_=fantasy_period(league,choice,monday,sunday,today,live)
        previous_records,_,_,_=fantasy_period(league,choice,max(monday-timedelta(days=7),first),monday-timedelta(days=1),today)
        if missing:st.warning('缺少部分日期的 Fantasy 排陣／單日數據：'+', '.join(missing)+ '。更新請至聯盟同步。')
        if source:st.caption('資料來源：'+source+' · 最近更新 '+stamp)
        if live and live.get('error'):st.info('即時比分來源暫時未完整取得；顯示 Yahoo 最近同步的單日數據。缺漏數據不會以賽季平均推算。')
        # Historical additions/drops remain visible even if absent from the current roster.
        known={str(r.get('id')) for r in roster};known_names={norm(r['name']) for r in roster}
        for r in records+week_records+previous_records:
            if str(r['PLAYER_ID']) not in known and norm(r['PLAYER_NAME']) not in known_names:
                roster.append({'id':str(r['PLAYER_ID']),'name':r['PLAYER_NAME'],'team':r['TEAM_ABBREVIATION'],'status':'active'});known.add(str(r['PLAYER_ID']));known_names.add(norm(r['PLAYER_NAME']))
    if not logs:
        from dashboard_matchup import render_weekly_score
        from data_center import store as results_store
        with score_slot.container():render_weekly_score(league,results_store(),choice,monday,sunday,today,live)
    if not logs and not records and unverified:
        # NBA roster reference is explicit; never claim these were Fantasy starters.
        reference_mode=True
        from daily_evidence import unverified_period
        ids={norm(r['name']):r.get('id') for r in roster}
        def reference_records(items):
            return [{'PLAYER_ID':ids.get(norm(r['球員'])) or 'reference:'+norm(r['球員']),'PLAYER_NAME':r['球員'],'TEAM_ABBREVIATION':r['NBA球隊'],'GP':r['場次'],**{k:r[k] for k in KEYS}} for r in items]
        records=reference_records(unverified)
        week_records=reference_records(unverified_period(league,choice,max(monday,first),sunday,today,by_date))
        st.warning('NBA 名單參考模式：尚未取得這些日期的 Fantasy 先發。以下圓餅圖、產量及暫定 MVP 使用目前名單的 NBA 實績，不代表聯盟計分結果；完成該週排陣同步後會自動改用先發貢獻。')
    rows=production(roster,players,schedule,start,end,excluded,actual=records)
    if not logs and not reference_mode and start<=today and not source and missing:
        for r in rows:r.update(covered=False,reason='無實績/未開賽')
    weekly=production(roster,players,schedule,monday,sunday,excluded,actual=week_records)
    prev=production(roster,players,schedule,monday-timedelta(days=7),monday-timedelta(days=1),excluded,actual=previous_records)
    previous={r['name']:r for r in prev}
    trends={r['name']:trend(r,previous.get(r['name']),ref) for r in weekly}
    if reference_mode:
        trends={r['name']:'前週 Fantasy 資料未確認' for r in weekly}
        for r in rows:
            if r['gp']>0:r['reason']='NBA實績・先發未確認'
    record_map={norm(r['PLAYER_NAME']):r for r in records}
    if not logs:
        for r in rows:
            if not r['excluded'] and norm(r['name']) not in record_map:r.update(covered=False,reason='無實績/未開賽')
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
        statline=' · '.join(LABELS[c]+' '+(f"{winner_row['tot'][c+'M']/winner_row['tot'][c+'A']:.1%}" if winner_row['tot'][c+'A'] else '—') if c in ('FG','FT') else f"{LABELS[c]} {winner_row['tot'][c]:g}" for c in CATS)
        photo_record=record_map.get(norm(winner['name']))
        photo_id=str(photo_record['PLAYER_ID']) if photo_record else ''
        with st.expander('MVP 評分與趨勢說明',expanded=False):
            page_caption('MVP採當期九項等權累積標準化貢獻；TO反向、FG/FT以出手量Impact計算。標準化尺度仍使用2025–26選秀母體；所有產量均為所選期間實績。')
            page_caption('📈／📉：整週每場九項綜合貢獻對比前週，➖為持平；🆕為前週未出賽。單日檢視也顯示所屬整週趨勢；未完賽週僅比較目前已發生場次。')
        photo_url=f'https://cdn.nba.com/headshots/nba/latest/1040x760/{photo_id}.png' if photo_id.isdigit() else ''
        photo_html=(f'<div class="mvp-photo"><img class="portrait" src="{html.escape(photo_url,quote=True)}" alt="{html.escape(winner['name'],quote=True)} MVP 球員照"></div>' if photo_url else '')
        hero=f"""<style>
.mvp-body{{display:flex;align-items:center;gap:16px;justify-content:space-between}}
.mvp-copy{{flex:1;min-width:0}}
.mvp-photo{{flex:0 0 30%;max-width:210px;align-self:stretch;display:flex;align-items:center;overflow:hidden}}
.mvp-photo img{{width:100%;height:148px;object-fit:contain;border-radius:10px}}
@media(max-width:600px){{.mvp-body{{gap:8px}}.mvp-photo{{flex-basis:30%;min-width:85px}}.mvp-photo img{{height:130px}}}}
</style><div style="background:linear-gradient(120deg,#17243e,#183d42);border:1px solid #c8ad61;border-radius:14px;padding:16px 18px;margin:8px 0;color:#f3f6fc"><div class="mvp-body"><div class="mvp-copy">
<div style="color:#edcd79;font-size:10px;letter-spacing:2px">🏆 {'暫定 MVP · NBA 名單實績' if reference_mode else 'PLAYER OF THE '+('WEEK' if granularity=='當週' else 'DAY')}</div>
<div style="font-size:25px;font-weight:800;margin:6px 0;overflow-wrap:anywhere">{html.escape(winner['name'])}</div>
<div style="color:#c8e6e3;font-size:12px">{html.escape(statline)}</div>
<div style="margin-top:8px;color:#f3d987;font-size:12px">貢獻分 {winner['score']:+.3f}　｜　{winner['gp']} 場　｜　全隊 {total['g']} 球員出賽場次</div>
<div style="margin-top:6px;color:#d4dfed;font-size:12px">週場均趨勢 {html.escape(trends[winner['name']])}</div></div>{photo_html}</div></div>"""
        st.markdown(hero,unsafe_allow_html=True)
        if len(scores)>1:
            st.caption('追趕者：'+'　 · 　'.join(f"{i+2}. {r['name']}（{r['score']:+.3f}）" for i,r in enumerate(scores[1:3])))
    else:
        st.info('🏆 本期尚無可評選的出賽紀錄。')
    legend_color = '#465a6a' if st.session_state.get('visual_theme') == '簡約淺色' else '#edf3fb'
    color_index={r['name']:i for i,r in enumerate(rows)}
    top_names=[r['name'] for r in scores[:3]]
    remaining=[r['name'] for r in rows if r['name'] not in top_names]
    def legend_markup(names):
        return ' '.join('<span style="display:inline-flex;align-items:center;gap:5px;margin:3px 12px 3px 0;color:'+legend_color+';font-size:12px"><span style="background:'+COLORS[color_index[name]%len(COLORS)]+';width:9px;height:9px;border-radius:50%;display:inline-block"></span>'+html.escape(name)+'</span>' for name in names)
    if top_names:st.markdown(legend_markup(top_names),unsafe_allow_html=True)
    if remaining:
        with st.expander(f'其餘球員顏色圖例（{len(remaining)}）',expanded=False):st.markdown(legend_markup(remaining),unsafe_allow_html=True)
    chart_names=[r['name'] for r in rows]
    mobile=st.session_state.get('device_view')=='手機版'
    charts_per_row=5 if mobile else 3
    for offset in range(0,9,charts_per_row):
        with st.container(key='pie_row_'+str(offset)):
            columns=st.columns(charts_per_row)
            for container,cat in zip(columns,CATS[offset:offset+charts_per_row]):
                with container:
                    title=LABELS[cat]+({} if mobile else {'FG':' · 投籃命中占比','FT':' · 罰球命中占比','TOV':' · 失誤負擔'}).get(cat,'')
                    st.markdown('**'+title+'**')
                    chart=mobile_pie(rows,cat,ref,chart_names) if mobile else pie_chart(rows,cat,chart_names,ref)
                    if chart is None:
                        st.caption('—' if mobile else '本期沒有可計算的產量。')
                    elif mobile:
                        st.markdown(chart,unsafe_allow_html=True)
                    else:
                        st.altair_chart(chart,width='stretch',theme=None)
                    if not mobile and cat=='TOV':
                        st.caption('占比越大＝失誤負擔越多；MVP評分會反向計算。')
                    elif not mobile and cat in ('FG','FT'):
                        st.caption('圓心為全隊命中率；扇形為命中數占比。'+('下方可展開數據明細。' if mobile else '滑鼠移上可看個人命中率及Impact。'))
    if mobile:
        with st.expander('查看圓餅圖數據 · 點開／收起'):
            selected_cat=st.selectbox('數據項目',list(CATS),format_func=LABELS.get,key='mobile_pie_category')
            details=pie_details(rows,selected_cat,ref)
            if details:st.dataframe(pd.DataFrame(details),hide_index=True,width='stretch')
            else:st.caption('本期沒有可計算的產量。')
    with st.expander('MVP票選依據 · 各項貢獻分'):
        st.dataframe(pd.DataFrame([{'球員':s['name'],'場次':s['gp'],'綜合分':round(s['score'],3),
                                    **{LABELS[c]:round(s['parts'][c],3) for c in CATS}} for s in scores]),hide_index=True,width='stretch')
    st.markdown('#### 本期球員名單與產量')
    score_map={r['name']:r['score'] for r in scores}
    table=[]
    roster_by_name={r['name']:r for r in roster}
    injured_names={r['name'] for r in roster if r.get('status')=='IL'}
    for r in rows:
        item={'球員':r['name'],'NBA球隊':r['team'],'場次':r['gp'] if r['covered'] else None,'狀態':r['reason'] if r['gp'] else '無實績/未開賽',
              **{LABELS[c]:round(r['tot'][c],1) if r['covered'] else None for c in CATS if c not in ('FG','FT')}}
        for c in ('FG','FT'):
            item[LABELS[c]]=f"{r['tot'][c+'M']/r['tot'][c+'A']:.1%}" if r['covered'] and r['tot'][c+'A'] else '—'
        item['位置']='/'.join(roster_by_name.get(r['name'],{}).get('eligible',[])) or '—'
        item={**{k:item[k] for k in ('球員','位置','NBA球隊','場次','狀態')},**{LABELS[c]:item[LABELS[c]] for c in CATS}}
        item['週場均趨勢']=trends[r['name']] if r['covered'] else '— 資料待確認'
        item['MVP分']=round(score_map[r['name']],3) if r['name'] in score_map else None
        table.append(item)
    active_table=[item for item in table if item['球員'] not in injured_names]
    injured_table=[item for item in table if item['球員'] in injured_names]
    def show_production(items):
        if mobile:
            from mobile_stat_cards import player_rows
            st.markdown(player_rows([dict(item,_nba_id=roster_by_name.get(item['球員'],{}).get('id')) for item in items]),unsafe_allow_html=True)
        else:st.dataframe(pd.DataFrame(items),hide_index=True,width='stretch')
    show_production(active_table)
    if injured_table:
        with st.expander(f'傷兵／IL（{len(injured_table)}）',expanded=False):show_production(injured_table)
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
        if mobile:
            from mobile_stat_cards import player_rows
            st.markdown(player_rows([dict(r,場次=r['本週場次']) for r in comparison]),unsafe_allow_html=True)
        else:st.dataframe(pd.DataFrame(comparison),hide_index=True,width='stretch')
        page_caption('每項以本週總數÷實際出賽場次；FG/FT為總命中÷總出手。TO越低越好。pp代表百分點。')
    st.download_button('下載本期名單與貢獻CSV',pd.DataFrame(table).to_csv(index=False).encode('utf-8-sig'),f'overview_{start}_{end}.csv','text/csv')
