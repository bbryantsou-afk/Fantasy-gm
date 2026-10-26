from page_guidance import caption as page_caption
from app_storage import private_path
"""Native Streamlit version of the approved 9-Cat baseline lab."""
import json,re
from pathlib import Path

import pandas as pd
import streamlit as st

from ninecat_model import (CATS, KEYS, LABELS, norm, player_key, roster_key, cohort_ids, baseline,
                          aggregate, value, gap, utility, weighted_z, zscore, bundle, apply_bundle, validate_backup)

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / 'ninecat_assets'
STATE = ROOT / 'ninecat_state.json'


@st.cache_data
def load_data():
    snapshot = json.loads((ASSETS / 'data.json').read_text(encoding='utf-8'))
    draft_path = ASSETS / 'draft.json'
    draft = json.loads(draft_path.read_text(encoding='utf-8'))['entries']
    return snapshot, draft


def number(v, cat=None):
    return '—' if v is None else (f'{v:.2%}' if cat in ('FG', 'FT') else f'{v:.3f}')


def percent(v):
    return '—' if v is None else f'{v:+.2%}'


def save_state():
    data = {'version': 2, 'roster': st.session_state.nc_roster, 'weekHistory': st.session_state.nc_weeks}
    try:
        temp = private_path(STATE).with_suffix('.json.tmp')
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        temp.replace(private_path(STATE))
    except OSError as exc:
        st.warning(f'本機儲存失敗，請下載備份：{exc}')


def reset_package():
    st.session_state.nc_adds = []
    st.session_state.nc_drops = []


def replace_roster(rows):
    from roster_store import save_team, active_team
    _, entries=load_data()
    save_team(entries,active_team(entries),rows)
    st.session_state.nc_roster = rows
    st.session_state.nc_revision += 1
    reset_package()
    save_state()


def package_rows(result):
    return [{'項目': LABELS[c], '原本每場平均': number(p['before'], c), '換入後平均': number(p['after'], c),
             '原本對母體差距': percent(p['before_gap']), '換入後差距': percent(p['after_gap']),
             '適配分貢獻': round(p['delta'], 3)} for c, p in result['parts'].items()]


def render_ninecat_strategy():
    if st.session_state.get('visual_theme')!='簡約淺色':st.markdown('<style>\n/* Keep the native dark page legible even if a browser is using the light theme. */\n.stApp { color:#edf3fb; --text-color:#edf3fb; color-scheme:dark; }\n[data-testid="stWidgetLabel"] p,\n[data-testid="stRadio"] label p,\n[data-testid="stCheckbox"] label p,\n[data-testid="stMetricLabel"] p,\n[data-testid="stMetricValue"],\n[data-testid="stExpander"] summary p,\n[data-testid="stSlider"] label p { color:#edf3fb !important; }\n[data-testid="stCaptionContainer"] p { color:#bdcadd !important; }\n[data-testid="stMarkdownContainer"] { color:#edf3fb; }\n[data-testid="stBaseButton-secondary"],\n[data-testid="stBaseButton-secondaryFormSubmit"],\n[data-testid="stDownloadButton"] button,\n[data-testid="stButton"] button[kind="secondary"] {\n background:#e8eff8 !important; color:#152b45 !important;\n border:1px solid #93a9c1 !important; }\n[data-testid="stBaseButton-secondary"] *,\n[data-testid="stBaseButton-secondaryFormSubmit"] *,\n[data-testid="stDownloadButton"] button *,\n[data-testid="stButton"] button[kind="secondary"] * { color:#152b45 !important; }\n[data-testid="stBaseButton-primary"] {\n background:#167366 !important; border-color:#39b6a2 !important; color:#ffffff !important; }\n[data-testid="stBaseButton-primary"] * { color:#ffffff !important; }\n[data-testid="stButton"] button:disabled,\n[data-testid="stDownloadButton"] button:disabled {\n background:#293449 !important; color:#a7b6cc !important; border-color:#45516a !important; opacity:1 !important; }\n[data-testid="stButton"] button:disabled *,\n[data-testid="stDownloadButton"] button:disabled * { color:#a7b6cc !important; }\n[data-baseweb="select"] > div { background:#edf2f8 !important; color:#162c45 !important; }\n[data-baseweb="select"] input { color:#162c45 !important; caret-color:#162c45 !important; }\n[data-baseweb="select"] svg { fill:#29415e !important; }\n[data-baseweb="tag"] { background:#244460 !important; }\n[data-baseweb="tag"] * { color:#f3f7ff !important; fill:#f3f7ff !important; }\n[data-testid="stTextInput"] input,\n[data-testid="stNumberInput"] input {\n background:#edf2f8 !important; color:#162c45 !important; caret-color:#162c45 !important; }\ninput::placeholder { color:#5a6b80 !important; opacity:1 !important; }\n[data-baseweb="popover"] [role="option"],\n[data-baseweb="popover"] [role="listbox"] { background:#edf2f8 !important; color:#162c45 !important; }\n[data-baseweb="popover"] [role="option"] * { color:#162c45 !important; }\n.nc-baseline-strip {\n display:grid; grid-template-columns:repeat(9,minmax(62px,1fr));\n overflow-x:auto; background:#151e33; border:1px solid #34425b;\n border-radius:8px; margin:4px 0 10px; padding:7px 3px; gap:0; }\n.nc-baseline-stat { display:flex; flex-direction:column; align-items:center; justify-content:center; gap:2px;\n white-space:nowrap; padding:1px 4px; border-right:1px solid #34425b; }\n.nc-baseline-stat:last-child { border-right:0; }\n.nc-baseline-label { color:#bbcadf; font-size:11px; font-weight:500; }\n.nc-baseline-value { color:#f4f8ff; font-size:14px; font-weight:650; font-variant-numeric:tabular-nums; }\n</style>', unsafe_allow_html=True)
    page_caption('原生 App 整合版 · 歷史場均與球隊適配分析 · 不會操作 Yahoo 加入、釋出或交易')
    try:
        snapshot, entries = load_data()
    except (OSError, ValueError) as exc:
        st.error(f'無法載入本機資料：{exc}')
        return
    season=st.selectbox('數據賽季',['2026-27','blended-25','2025-26'],format_func=lambda v:'上季最後25場＋本季全部' if v=='blended-25' else v,key='nc_data_season')
    from strategy_season import strategy_snapshot
    with st.spinner('載入場均…'):snapshot=strategy_snapshot(season)
    if st.session_state.get('_nc_filter_season')!=season:
        st.session_state['nc_min_gp']=0
        st.session_state['nc_search']=''
        st.session_state['nc_only_ref']=False
        st.session_state['_nc_filter_season']=season
    players = snapshot['players']
    lookup = {str(p['PLAYER_ID']): p for p in players}
    pool = {player_key(p): p for p in players}
    for e in entries:
        if e['playerId'] is None:
            p = {'PLAYER_ID': None, 'PLAYER_NAME': e['name']}
            pool[player_key(p)] = p
    if 'nc_roster' not in st.session_state:
        st.session_state.nc_roster, st.session_state.nc_weeks = [], []
        if private_path(STATE).exists():
            try:
                rows, weeks = validate_backup(json.loads(private_path(STATE).read_text(encoding='utf-8')))
                st.session_state.nc_roster, st.session_state.nc_weeks = rows, weeks
            except (ValueError, OSError, TypeError, AttributeError):
                st.warning('本機名單檔格式有誤，原檔未覆寫；請匯入備份。')
    from roster_store import choose_team, roster as shared_roster
    selected_team=choose_team(entries,'nc_shared_team')
    st.session_state.nc_roster=shared_roster(entries,selected_team)
    st.session_state.setdefault('nc_revision', 0)
    st.session_state.setdefault('nc_custom', {})
    pool.update(st.session_state.nc_custom)
    for r in st.session_state.nc_roster:
        if r.get('id') is None:
            pool.setdefault(roster_key(r), {'PLAYER_ID': None, 'PLAYER_NAME': r['name']})

    kinds = {'第三組 · 聯盟選秀名單': 'draft', '第二組 · 六項前100名': '100'}
    if st.session_state.get('nc_cohort') not in kinds:
        st.session_state['nc_cohort'] = next(iter(kinds))
    chosen = st.radio('參考母體', list(kinds), horizontal=True, key='nc_cohort')
    kind = kinds[chosen]
    default_ref = cohort_ids(players, entries, kind)
    ref_key = 'nc_ref_' + kind
    st.session_state.setdefault(ref_key, sorted(default_ref))
    ref_ids = set(st.session_state[ref_key])
    if not ref_ids:
        st.warning('參考母體不可為空，已還原預設。')
        st.session_state[ref_key] = sorted(default_ref)
        ref_ids = default_ref
    ref = baseline(players, ref_ids)
    st.caption(f"{snapshot['season']} 例行賽快照 · 母體 {ref['n']} 人")
    strip = '<div class="nc-baseline-strip" aria-label="九項母體平均">' + ''.join(
        '<div class="nc-baseline-stat" title="' + LABELS[c] + ' 母體標準差 ' + f"{ref[c]['std']:.3f}" + '">'
        + '<span class="nc-baseline-label">' + LABELS[c] + '</span>'
        + '<span class="nc-baseline-value">' + number(ref[c]['mean'], c) + '</span></div>'
        for c in CATS) + '</div>'
    st.markdown(strip, unsafe_allow_html=True)
    small = sum(p['GP'] < 20 for p in players if str(p['PLAYER_ID']) in ref_ids)
    st.caption(f'本組有 {small} 位出賽未滿20場。各項前N名恰取N人，同分依球員ID；命中率用總場均命中／總場均出手。')
    with st.expander('展開母體平均、標準差及編輯參考名單'):
        st.caption(f"資料取得時間：{snapshot['fetchedAt']} · 全資料 {len(players)} 人")
        st.dataframe(pd.DataFrame([{'項目': LABELS[c], '平均': number(ref[c]['mean'], c),
                                   '標準差': round(ref[c]['std'], 6), '標準差單位': 'Impact' if c in ('FG', 'FT') else '場均數值',
                                   '原始百分比標準差': percent(ref[c].get('pct_std'))} for c in CATS]), hide_index=True, width='stretch')
        st.multiselect('輸入球員姓名，編輯納入／排除', options=sorted(lookup), format_func=lambda k: lookup[k]['PLAYER_NAME'], key=ref_key)
        st.button('還原目前母體', key='nc_reset_ref', on_click=lambda: st.session_state.update({ref_key: sorted(default_ref)}))
        missing = [e['name'] for e in entries if e['playerId'] is None]
        st.caption('原始選秀182人，171人有數據。缺少該季數據，不納入母體：' + '、'.join(missing))
        st.download_button('下載參考名單CSV', pd.DataFrame([p for p in players if str(p['PLAYER_ID']) in ref_ids]).to_csv(index=False).encode('utf-8-sig'), 'ninecat_reference.csv', 'text/csv')

    st.divider()
    st.subheader('我的球隊 · 每次計分出賽貢獻')
    st.caption('目前使用上方所選球隊的共用名單；可在總覽編輯名單、位置及 IL。')
    page_caption('預設有資料者各1場。可改成預期實際計入的場次；板凳、IL及缺資料者不進入歷史估算。這不是本週實績。')
    roster = st.session_state.nc_roster
    with st.expander('編輯名單、IL及計分場次', expanded=not bool(roster)):
        if roster:
            table = pd.DataFrame([{'保留': True, '球員': r['name'], '狀態': r['status'], '計分場次': r['games'],
                                   '資料': '有歷史數據' if str(r.get('id')) in lookup else '無該季數據'} for r in roster])
            edited = st.data_editor(table, disabled=['球員', '資料'], hide_index=True, width='stretch',
                                    column_config={'狀態': st.column_config.SelectboxColumn(options=['active', 'bench', 'IL'], required=True),
                                                   '計分場次': st.column_config.NumberColumn(min_value=0, max_value=82, step=1, required=True)},
                                    key=f'nc_editor_{st.session_state.nc_revision}')
            if st.button('儲存名單設定', key='nc_save_editor'):
                updated = [{**r, 'status': edited.iloc[i]['狀態'], 'games': int(edited.iloc[i]['計分場次'])} for i, r in enumerate(roster) if edited.iloc[i]['保留']]
                replace_roster(updated)
                st.rerun()
        else:
            st.info('先載入一隊，或在下方有空位模式加入球員。')
    agg = aggregate(roster, lookup)
    st.caption(f"名單 {len(roster)} 人 · 計分出賽 {agg['g']} 場次 · 缺資料 {sum(str(r.get('id')) not in lookup for r in roster)} 人。10位球員各3場＝30個計分出賽場次。")
    st.dataframe(pd.DataFrame([{'項目': LABELS[c], '我的球隊每場平均': number(value(agg, c), c), '母體平均': number(ref[c]['mean'], c),
                               '對母體差距': '—' if value(agg, c) is None else (f"{(value(agg,c)-ref[c]['mean'])*100:+.2f} 個百分點" if c in ('FG', 'FT') else f"{(value(agg,c)-ref[c]['mean'])*(-1 if c=='TOV' else 1):+.3f}"),
                               '差距÷母體平均': percent(gap(value(agg, c), ref[c]['mean'], c))} for c in CATS]), hide_index=True, width='stretch')

    with st.expander('名單備份／匯入測試網站備份'):
        payload = {'version': 2, 'roster': roster, 'weekHistory': st.session_state.nc_weeks}
        st.download_button('下載名單與週資料備份', json.dumps(payload, ensure_ascii=False, indent=2), 'ninecat_roster.json', 'application/json')
        upload = st.file_uploader('選擇測試網站的 JSON 備份', type='json', key='nc_backup')
        if st.button('匯入並取代本機名單', disabled=upload is None):
            try:
                rows, weeks = validate_backup(json.loads(upload.getvalue()))
                st.session_state.nc_weeks = weeks
                replace_roster(rows)
                st.rerun()
            except (ValueError, TypeError, AttributeError) as exc:
                st.error(str(exc))
        page_caption('儲存在本機 ninecat_state.json；雲端磁碟可能不持久，請下載備份。')

    st.subheader('策略權重')
    with st.form('nc_weight_form',border=False):
        wc = st.columns(3)
        weights = {c: wc[i % 3].slider(LABELS[c]+' 權重', 0.0, 2.0, 1.0, .1, key='nc_weight_'+c) for i, c in enumerate(CATS)}
        st.form_submit_button('套用權重',type='primary')
    st.caption('0＝不計、1＝正常、2＝優先。適配分會依目前優劣勢遞減；不是對局勝率。')

    st.subheader('球員大名單 · Perfect Match')
    mode = st.radio('排名方式', ['我的球隊適配', '原始加權 Z-score'], horizontal=True, key='nc_mode')
    owned = {roster_key(r) for r in roster}
    owned_names = {norm(r['name']) for r in roster}
    add_options = sorted([k for k, p in pool.items() if k not in owned and norm(p['PLAYER_NAME']) not in owned_names], key=lambda k: norm(pool[k]['PLAYER_NAME']))
    from roster_store import state as league_state
    current_league=league_state(entries)
    position_meta={str(k):v.get('eligible',[]) for k,v in current_league.get('player_meta',{}).items()}
    for rows in current_league.get('teams',{}).values():
        for r in rows:
            if r.get('id') and r.get('eligible'):position_meta[str(r['id'])]=r['eligible']
    for e in entries:
        if e.get('playerId') is not None:
            position_meta[str(e['playerId'])]=position_meta.get(str(e['playerId'])) or re.findall(r'\b(?:PG|SG|SF|PF|C)\b',e.get('position',''))
    def reset_strategy_filters():
        st.session_state.update(nc_position_filter=[],nc_min_gp=0,nc_search='',nc_only_ref=False)
    st.button('重設篩選',on_click=reset_strategy_filters,key='nc_reset_filters')
    selected_positions=st.multiselect('指定位置',['PG','SG','SF','PF','C'],key='nc_position_filter',placeholder='全部位置')
    def position_matches(p):return not selected_positions or bool(set(position_meta.get(str(p.get('PLAYER_ID')),[])) & set(selected_positions))
    drop_options = [roster_key(r) for r in roster]
    names = {roster_key(r): r['name'] for r in roster}
    for key, valid in [('nc_adds', set(add_options)), ('nc_drops', set(drop_options))]:
        st.session_state[key] = [k for k in st.session_state.get(key, []) if k in valid]
    left, right = st.columns(2)
    drops = left.multiselect('釋出', drop_options, format_func=lambda k: names[k], key='nc_drops', placeholder='輸入我方球員姓名…')
    adds = right.multiselect('加入', [k for k in add_options if position_matches(pool[k]) or k in st.session_state.get('nc_adds',[])],
                             format_func=lambda k: pool[k]['PLAYER_NAME'] + (' · 無歷史資料' if pool[k].get('PLAYER_ID') is None else ''),
                             key='nc_adds', placeholder='輸入球員姓名…')
    controls = st.columns(3)
    games = controls[0].number_input('每位加入球員計分場次', 1, 7, 1, key='nc_games')
    if not st.session_state.get('nc_vacancy_default_v2'):
        st.session_state.nc_vacancy = True
        st.session_state.nc_vacancy_default_v2 = True
    vacancy = controls[1].checkbox('有空位，允許非等人數加入', key='nc_vacancy')
    controls[2].button('清空比較包裹', on_click=reset_package, key='nc_clear')
    extra_controls = st.columns(2)
    with extra_controls[0].expander('加入無數據球員'):
        custom = st.text_input('球員姓名', key='nc_custom_name')
        def add_custom():
            name = custom.strip()
            if not name or norm(name) in owned_names:
                return
            existing = next((k for k, p in pool.items() if norm(p['PLAYER_NAME']) == norm(name)), None)
            p = {'PLAYER_ID': None, 'PLAYER_NAME': name}
            key = existing or player_key(p)
            if not existing:
                st.session_state.nc_custom[key] = p
            st.session_state.nc_adds = list(dict.fromkeys(st.session_state.nc_adds + [key]))
        st.button('加入比較包裹', on_click=add_custom, key='nc_custom_add')
    with extra_controls[1].expander('適配分計算方式'):
        scale = st.select_slider('差距敏感範圍', options=[.1, .2, .4], value=.2, format_func=lambda v: f'{v:.0%}', key='nc_scale')
        page_caption('r＝（我方平均−母體平均）÷母體平均，TO反向。U(r)＝1/(1+exp(−r/s))；適配分＝100×加權平均(U換入後−U原本)。此曲線尚未經勝率校準。')
    additions = [pool[k] for k in adds]
    ready = bool(drops) or vacancy
    st.write(f'釋出 **{len(drops)} 人** → 加入 **{len(adds)} 人**；名單 **{len(roster)} → {len(roster)-len(drops)+len(adds)} 人**。')
    error = '請選擇加入球員。' if not adds else '先選擇釋出球員，或勾選有空位。' if not ready else '滿員時加入與釋出人數必須相同。' if not vacancy and len(adds) != len(drops) else ''
    st.caption(error or '可套用整包；所有操作只修改本機分析名單。')
    def commit():
        try:
            updated = apply_bundle(st.session_state.nc_roster, additions, drops, games, vacancy)
            replace_roster(updated)
            st.session_state.nc_notice = '已套用整包：釋出 '+ '、'.join(names[k] for k in drops) + '；加入 '+ '、'.join(p['PLAYER_NAME'] for p in additions)
        except ValueError as exc:
            st.session_state.nc_notice = str(exc)
    st.button('套用整包加入／釋出', disabled=bool(error), type='primary', on_click=commit, key='nc_apply')
    if st.session_state.get('nc_notice'):
        st.success(st.session_state.pop('nc_notice'))
    result = bundle(roster, lookup, additions, drops, ref, weights, games, scale) if ready and additions else None
    if result:
        st.metric('整包適配提升分', f"{result['total']:.3f}")
        if result['missing']:
            st.warning(f"不完整估算：{result['missing']} 位加入球員沒有歷史數據，未納入分子或場次分母。")
        st.dataframe(pd.DataFrame(package_rows(result)), hide_index=True, width='stretch')
    if ready and not agg['g']:
        st.info('目前沒有可計算的原始球隊產量，仍可套用名單；加入有資料球員後再計算適配。')

    with st.expander('⭐ 加星球員 · 同步至球員觀察室'):
        from player_hub import star_picker
        star_picker(players,'nc_watch_stars')

    filters = st.columns(3)
    query = filters[0].text_input('搜尋排名球員或球隊', key='nc_search')
    min_gp = filters[1].number_input('最低出賽場次', 0, 82, 0, key='nc_min_gp')
    only_ref = filters[2].checkbox('只看參考母體', key='nc_only_ref')
    include_owned=st.toggle('包含我的球員',key='nc_include_owned')
    show_z = st.checkbox('顯示各項 Z-score', key='nc_show_z')
    from roster_store import team_label
    fantasy_owners={roster_key(r):team_label(t) for t,rows in current_league['teams'].items() for r in rows}
    fit_ranking = mode == '我的球隊適配' and bool(agg['g'])
    if mode == '我的球隊適配' and not agg['g']:
        st.info('目前沒有可計算的球隊數據，先顯示原始加權 Z-score 大名單；載入我的球隊後會自動切換適配排名。')
    if fit_ranking:
        st.caption('未選釋出球員時，直接比較加入誰最適合目前球隊；不用先勾選或釋出球員。')
    records = []
    for p in players:
        key = player_key(p)
        if not position_matches(p) or p['GP'] < min_gp or (only_ref and key not in ref_ids):
            continue
        if fit_ranking and ((key in owned and not include_owned) or key in adds):
            continue
        candidate_roster=[r for r in roster if roster_key(r)!=key] if key in owned else roster
        fitted = bundle(candidate_roster, lookup, additions+[p], drops, ref, weights, games, scale) if fit_ranking else None
        score = fitted['total'] if fitted else weighted_z(p, ref, weights)
        rec = {'球員': p['PLAYER_NAME'], 'NBA球隊': p['TEAM_ABBREVIATION'], 'GP': p['GP'],
               ('包裹＋此人適配分' if additions or drops else '加入適配分') if fit_ranking else 'Weighted Z': score,
               '原始Weighted Z': weighted_z(p, ref, weights)}
        if st.session_state.get('device_view')!='手機版':rec['Fantasy 球隊']=fantasy_owners.get(key,'歸屬待確認')
        rec.update({LABELS[c]: number(p[c+'M']/p[c+'A'] if p[c+'A'] else None, c) if c in ('FG', 'FT') else p[c] for c in CATS})
        if show_z:
            rec.update({LABELS[c]+' Z': round(zscore(p, c, ref), 3) for c in CATS})
        records.append((score, int(p['PLAYER_ID']), rec))
    records.sort(key=lambda r: (-r[0], r[1]))
    ranked = [{'排名': i+1, **rec} for i, (_, _, rec) in enumerate(records) if norm(query) in norm(rec['球員']+' '+rec['NBA球隊'])]
    if not ranked:st.info('沒有符合篩選的球員。請按「重設篩選」恢復名單。')
    if fit_ranking:
        page_caption('每列比較加入該球員對現有球隊的幫助；若選了加入／釋出包裹，則一併試算。排名可直接瀏覽，套用名單才檢查人數。缺資料者不排名。')
    if st.session_state.get('device_view')=='手機版':
        score_key=('包裹＋此人適配分' if additions or drops else '加入適配分') if fit_ranking else 'Weighted Z'
        import html
        summary='<div class="mobile-rank-list"><div><b>排名</b><b>球員</b><b>適配分</b></div>'
        for r in ranked:
            summary+='<div><span>'+str(r['排名'])+'</span><span>'+html.escape(r['球員'])+'</span><b>'+f"{r[score_key]:.3f}"+'</b></div>'
        st.markdown(summary+'</div>',unsafe_allow_html=True)
        with st.expander('查看球員九項數據'):
            if ranked:
                detail=st.selectbox('球員',range(len(ranked)),format_func=lambda i:ranked[i]['球員'],key='nc_mobile_detail')
                from mobile_stat_cards import player_rows
                st.markdown(player_rows([ranked[detail]]),unsafe_allow_html=True)
    else:st.dataframe(pd.DataFrame(ranked), hide_index=True, width='stretch', height=min(563,38+35*len(ranked)),row_height=35)

    with st.expander('進階：輸入某週實際總數'):
        page_caption('七項計數總數÷球員計分出賽場次；FG/FT用總命中÷總出手。此區僅紀錄與比較，不取代上方歷史估算。')
        label = st.text_input('週次名稱', key='nc_week_label')
        inputs = st.columns(3)
        raw = {c: inputs[i % 3].number_input('本週 '+('計分出賽場次' if c == 'GP' else c), 0, value=0, step=1, key='nc_week_'+c) for i, c in enumerate(('GP', *KEYS))}
        if raw['GP'] > 0 and raw['FGM'] <= raw['FGA'] and raw['FTM'] <= raw['FTA'] and raw['FG3M'] <= raw['FGM'] and raw['PTS'] >= 3*raw['FG3M']:
            actual = {'g': raw['GP'], 'tot': {c: raw[c] for c in KEYS}}
            st.dataframe(pd.DataFrame([{'項目': LABELS[c], '每計分出賽平均': number(value(actual, c), c), '差距÷母體平均': percent(gap(value(actual, c), ref[c]['mean'], c))} for c in CATS]), hide_index=True)
            if st.button('儲存此週', disabled=not label.strip()):
                st.session_state.nc_weeks = [w for w in st.session_state.nc_weeks if w['label'] != label.strip()] + [{'label': label.strip(), 'values': raw}]
                save_state()
                st.success('已儲存')
        else:
            page_caption('請填入大於0的場次；命中不可大於出手，三分命中不可大於投籃命中，得分不可小於三分總得分。')
        history = st.session_state.nc_weeks
        if history:
            st.dataframe(pd.DataFrame([{'週次': w['label'], '場次': w['values']['GP'], 'PTS/場': w['values']['PTS']/w['values']['GP']} for w in history]), hide_index=True)
