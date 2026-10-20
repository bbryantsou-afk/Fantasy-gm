from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo
import unicodedata
import json
import streamlit as st
from team_schedule import load_team_schedule, get_game_status


def render_matchup_simulator(lite=False):
    if lite:
        st.subheader("🏀 Matchup Simulator Lite")
        st.markdown('<style>[data-testid="stMainBlockContainer"]{padding-top:2rem}</style>',unsafe_allow_html=True)
    else:
        st.title("🏀 Fantasy GM — Matchup Simulator")
    st.caption("過去與今天載入該日 Fantasy 先發及實績；未來可套用上季場均或自訂預測。日期採美東比賽日。")

    today = datetime.now(ZoneInfo("America/New_York")).date()
    PLAYERS = {}
    # Public numbered league rosters; never expose the local private team names.
    from pathlib import Path
    import re
    root_path = Path(__file__).resolve().parent
    draft = json.loads((root_path/'ninecat_assets/draft.json').read_text())['entries']
    from roster_store import choose_team,roster as shared_roster,state,team_label,team_formatter
    from matchup_records import load as load_simulations,save as save_simulations
    saved_simulations=load_simulations()
    with st.expander('開啟已保存模擬（電腦／手機共用）'):
        saved_name=st.selectbox('保存的模擬',['']+sorted(saved_simulations),key='sim_open_name')
        if st.button('載入此模擬',disabled=not saved_name,key='sim_open_saved'):
            payload=saved_simulations[saved_name];context=payload.get('context',{})
            if context.get('my_team') in state(draft)['teams']:st.session_state['_my_team']=context['my_team']
            if context.get('opp_team') in state(draft)['teams']:st.session_state['sim_opp_team']=context['opp_team']
            season=context.get('season','2026-27')
            st.session_state['sim_season']=season
            begin,end=(date(2025,10,21),date(2026,4,12)) if season=='2025-26' else (date(2026,10,20),date(2027,4,11))
            st.session_state['sim_date_'+season]=max(begin,min(end,date.fromisoformat(payload['week_dates'][payload['selected_day']])))
            st.session_state['_sim_restore']=payload
            st.session_state['_sim_restore_name']=saved_name
            st.session_state['_sim_restore_nonce']=__import__('uuid').uuid4().hex
            st.session_state['_sim_manual_restore']=True
    teams=list(state(draft)['teams'])
    recent_sources = st.checkbox("載入本季最近 7／14／30 天場均（需連線）", value=False)


    TEAM_IDS = {
        "ATL":1610612737,"BOS":1610612738,"BKN":1610612751,"CHA":1610612766,
        "CHI":1610612741,"CLE":1610612739,"DAL":1610612742,"DEN":1610612743,
        "DET":1610612765,"GSW":1610612744,"HOU":1610612745,"IND":1610612754,
        "LAC":1610612746,"LAL":1610612747,"MEM":1610612763,"MIA":1610612748,
        "MIL":1610612749,"MIN":1610612750,"NOP":1610612740,"NYK":1610612752,
        "OKC":1610612760,"ORL":1610612753,"PHI":1610612755,"PHX":1610612756,
        "POR":1610612757,"SAC":1610612758,"SAS":1610612759,"TOR":1610612761,
        "UTA":1610612762,"WAS":1610612764,
    }

    selected_season = st.selectbox('模擬賽季', ['2026-27', '2025-26'], key='sim_season')
    season_begin, season_end = (date(2025,10,21),date(2026,4,12)) if selected_season=='2025-26' else (date(2026,10,20),date(2027,4,11))
    @st.cache_data(show_spinner=False)
    def historical_logs():
        return json.loads((root_path/'ninecat_assets/game_logs_2025_26.json').read_text())
    logs = historical_logs() if selected_season=='2025-26' else []
    default_date=season_begin if selected_season=='2025-26' else max(season_begin,min(season_end,today))
    date_key='sim_date_'+selected_season
    current_date=st.session_state.get(date_key,default_date)
    st.session_state['sim_date_mode']='過去' if current_date<today else '今天' if current_date==today else '未來'
    def choose_date_mode():
        mode=st.session_state['sim_date_mode']
        target=today+timedelta(days={'過去':-1,'今天':0,'未來':1}[mode])
        st.session_state[date_key]=max(season_begin,min(season_end,target))
    st.radio('日期類型',['過去','今天','未來'] if selected_season=='2026-27' else ['過去'],horizontal=True,key='sim_date_mode',on_change=choose_date_mode)
    selected_date = st.date_input(
        "📅 Yahoo 比賽日期（美東日期）",
        value=None if date_key in st.session_state else default_date,
        min_value=season_begin, max_value=season_end, key="sim_date_"+selected_season,
    )
    week_start = selected_date - timedelta(days=selected_date.weekday())
    week_dates = [week_start + timedelta(days=i) for i in range(7)]
    st.caption(f"🏀 Matchup Week：{week_dates[0]:%Y-%m-%d} ～ {week_dates[6]:%Y-%m-%d}")

    left, right = st.columns(2)
    with left:my_team=choose_team(draft,'sim_my_team')
    from fantasy_schedule import week_for
    known_week=week_for(state(draft),selected_date) if selected_season=='2026-27' else None
    pairing=known_week.get('opponents',{}).get(my_team) if known_week else None
    context=(selected_season,str(week_start),my_team,(known_week or {}).get('week'),pairing)
    if st.session_state.get('_sim_pairing_context')!=context:
        if pairing and not st.session_state.pop('_sim_manual_restore',False):st.session_state['sim_opp_team']=pairing
        st.session_state['_sim_pairing_context']=context
    opp_team=right.selectbox('對手球隊',teams,index=1,key='sim_opp_team',format_func=team_formatter())
    if pairing:st.caption(f"Yahoo Week {known_week['week']} · 預設對手：{team_label(pairing)}（可自行切換研究）")
    else:st.caption('此週尚無已同步的 Yahoo 對手；請先同步，或自行選擇對手。')
    for side,team in [('my',my_team),('opp',opp_team)]:
        PLAYERS[side]=[]
        for r in shared_roster(draft,team):
            if r.get('status')=='IL':continue
            PLAYERS[side].append(dict(id=f"{side}-{r.get('id') or r['name']}",
                evidence_id=str(r.get('id') or ('fantasy:'+str(r.get('yahoo_id') or r['name']))),
                nba_id=int(r['id']) if r.get('id') and str(r['id']).isdigit() else None,
                name=r['name'],team=r.get('team',''),eligible=r.get('eligible',[]),rank=len(PLAYERS[side])+1,stats={}))
    from daily_evidence import simulator_defaults,observed_day,nba_today
    league_state=state(draft)
    PLAYERS,official_lineups=simulator_defaults(league_state,my_team,opp_team,[d for d in week_dates if d<=today],PLAYERS) if selected_season=='2026-27' else (PLAYERS,{})
    live=nba_today(str(today)) if selected_season=='2026-27' and today in week_dates else None
    if selected_season=='2026-27' and today in week_dates:
        from daily_evidence import refresh_live_page
        refresh_live_page()
    if selected_date<=today and selected_season=='2026-27':
        evidence=observed_day(league_state,selected_date,live if selected_date==today else None)
        stamp=evidence['updated_at']
        st.caption(('今天：即時／最近同步實績' if selected_date==today else '過去：該日 Fantasy 排陣與實績')+' · '+(evidence['source'] or '尚無已同步數據')+(' · 更新 '+stamp if stamp else ''))
        if str(selected_date) not in official_lineups:st.warning('缺少這一天的 Fantasy 排陣；到聯盟同步選該日期，0.3.0 會一併讀取所屬整週。未取得資料前不會用現在名單假裝歷史先發。')
        if live and live.get('error'):st.info('即時比分來源暫時未完整取得；使用 Yahoo 最近同步數據，更新時間如上。可在聯盟同步更新今日資料。')
    elif selected_date>today:st.caption('未來：保留場均套用、自訂預測與排陣模擬。')
    st.caption('雙方使用共用名單，IL 不排入；此頁拖曳與新增屬於模擬，不會自動修改共用名單。')
    st.caption("賽程來源：NBA 例行賽快照；本季可按按鈕更新以反映改期。")
    if selected_season=="2026-27" and st.button("更新 NBA 官方賽程", key="v15_schedule_refresh"):
        try:
            import requests
            response=requests.get("https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json",timeout=20)
            response.raise_for_status()
            league=response.json()["leagueSchedule"]
            if str(league.get("seasonYear")) not in ("2026-27", "2026"):
                raise ValueError("官方回傳的球季不是 2026–27，保留原快照")
            fresh={}
            for group in league["gameDates"]:
                for game in group["games"]:
                    if not game.get("gameDateTimeUTC") or str(game.get("gameStatus")) == "4":
                        continue
                    day=datetime.fromisoformat(game["gameDateTimeUTC"].replace("Z","+00:00")).astimezone(ZoneInfo("America/New_York")).date()
                    for side in ("homeTeam","awayTeam"):
                        code=game[side].get("teamTricode")
                        if code in TEAM_IDS:
                            fresh.setdefault(code,set()).add(day)
            if len(fresh)!=30:
                raise ValueError("官方賽程資料不完整，保留原快照")
            st.session_state.v15_live_schedule=fresh
            st.success("本工作階段已更新 NBA 官方賽程")
        except Exception as exc:
            st.warning(f"更新失敗，沿用最近可用賽程：{exc}")
    schedule = st.session_state.get("v15_live_schedule") or load_team_schedule()
    if selected_season=='2025-26':
        schedule = {}
        for r in logs:
            schedule.setdefault(r['TEAM_ABBREVIATION'],set()).add(date.fromisoformat(r['GAME_DATE'][:10]))
        st.caption('上季賽程與單場實績使用已保存的 2025–26 NBA 例行賽紀錄；沿用目前聯盟名單回測，並非歷史 Fantasy 名單。')
    weekly_counts = [(team, sum(day in dates for day in week_dates)) for team, dates in schedule.items()]
    max_games = max((games for _, games in weekly_counts), default=0)
    top_teams = sorted((team, games) for team, games in weekly_counts if games == max_games)

    from contextlib import nullcontext
    with st.expander('📅 本週賽程摘要', expanded=False) if lite else nullcontext():
        from matchup_schedule_summary import schedule_summary, CSS as summary_css
        cards, calendar, leaders = schedule_summary(schedule,week_dates,TEAM_IDS)
        st.markdown(summary_css,unsafe_allow_html=True)
        summary_left, summary_right = st.columns([1,2])
        with summary_left:
            st.markdown("**🏆 本週出賽最多 · 含並列**")
            if leaders:
                st.markdown(cards,unsafe_allow_html=True)
            else:
                st.info("本週沒有排定比賽。")
        with summary_right:
            st.markdown("**📅 B2B 週曆**")
            st.markdown(calendar,unsafe_allow_html=True)
            st.caption("✓ 連兩天出賽的日期 · * 跨週 B2B · 滑鼠移上可看相鄰日期。表內可捲動。")
        st.caption("日期採美東。B2B 依球隊賽程判定，不代表球員確定出場；下方球員綠／紅格分別代表有／無賽程。")

    # NBA 球員資料庫：包含不在目前兩隊名單中的球員（例如 Seth Curry）。
    # NBA Stats 有時會限制連線；失敗時顯示狀態，絕不填入虛構統計。
    try:
        from nba_api.stats.static import players as nba_players
        from nba_api.stats.endpoints import leaguedashplayerstats, commonallplayers
        NBA_API_READY = True
    except ImportError:
        NBA_API_READY = False

    @st.cache_data(ttl=86400, show_spinner=False)
    def load_directory():
        if not NBA_API_READY:
            return []
        return nba_players.get_players()

    @st.cache_data(ttl=21600, show_spinner=False)
    def load_nba_stats(season, date_from=None, date_to=None):
        kwargs = dict(season=season, season_type_all_star="Regular Season",
                      per_mode_detailed="PerGame", timeout=20)
        if date_from:
            kwargs["date_from_nullable"] = date_from
        if date_to:
            kwargs["date_to_nullable"] = date_to
        frame = leaguedashplayerstats.LeagueDashPlayerStats(**kwargs).get_data_frames()[0]
        return frame.to_dict(orient="records")

    STAT_FIELDS = ["PTS", "REB", "AST", "STL", "BLK", "FG3M", "FGM", "FGA", "FTM", "FTA", "TOV"]

    def normalize_name(name):
        return "".join(ch for ch in unicodedata.normalize("NFKD", name).lower()
                       if not unicodedata.combining(ch) and ch.isalnum())

    def row_stats(row):
        if not row or int(row.get("GP", 0) or 0) < 1:
            return None
        if any(row.get(key) is None for key in STAT_FIELDS):
            return None
        return {target: round(float(row[source]), 4) for target, source in {
            "PTS":"PTS", "REB":"REB", "AST":"AST", "STL":"STL", "BLK":"BLK",
            "3PM":"FG3M", "FGM":"FGM", "FGA":"FGA", "FTM":"FTM", "FTA":"FTA", "TO":"TOV"
        }.items()}

    st.caption("📊 2025–26 場均由本機快照載入。本季近 7／14／30 天場均可勾選連線取得；上季模式直接使用單場實績。")
    historical = json.loads((root_path/'ninecat_assets/data.json').read_text())['players']
    profiles_by_id = {}
    errors = []
    if NBA_API_READY:
        with st.spinner("正在讀取 NBA 真實球員名單與統計（首次可能稍久）..."):
            try:
                directory = load_directory()
            except Exception as exc:
                directory = []
                errors.append(f"球員目錄：{type(exc).__name__}")
            asof = min(today, selected_date)
            profiles_by_id['season'] = {int(r['PLAYER_ID']):row_stats(r) for r in historical}
            requests = {}
            if selected_season=="2026-27" and recent_sources and asof >= date(2026, 10, 20):
                for key, days in [("one_week", 7), ("two_weeks", 14), ("month", 30)]:
                    requests[key] = ("2026-27", (asof-timedelta(days=days-1)).strftime("%m/%d/%Y"), asof.strftime("%m/%d/%Y"))
            for key, (season, start_date, end_date) in requests.items():
                try:
                    rows = load_nba_stats(season, start_date, end_date)
                    profiles_by_id[key] = {int(row["PLAYER_ID"]): row_stats(row) for row in rows}
                except Exception as exc:
                    errors.append(f"{key}：{type(exc).__name__}")
    else:
        directory = []
        errors.append("尚未安裝 nba_api，請執行 pip install nba_api")

    if errors:
        st.warning("NBA 統計部分未取得：" + "；".join(errors) + "。缺少數據的球員會顯示 —，不會當作 0。")

    nba_team_by_id = {int(r['PLAYER_ID']):r['TEAM_ABBREVIATION'] for r in historical}
    for e in draft:
        match = re.match(r'\((\w+)\s*-', e.get('position',''))
        if selected_season == '2026-27' and e.get('playerId') and match:
            nba_team_by_id[int(e['playerId'])] = match.group(1)

    name_to_entry = {normalize_name(p["full_name"]): p for p in directory}
    # 官方 NBA 球員名單涵蓋 Stephen Curry 與 Seth Curry，搜尋依部分姓名比對。
    CANDIDATES = []
    for item in directory:
        player_id = int(item["id"])
        if not item.get("is_active") and player_id not in profiles_by_id.get("season", {}):
            continue
        # Keep active players and players present in the historical snapshot.
        CANDIDATES.append({"id": f"nba-{player_id}", "nba_id": player_id,
                           "name": item["full_name"], "team": nba_team_by_id.get(player_id, ""), "eligible": ["UTIL"],
                           "stats": {}, "profiles": {key: mapping.get(player_id) for key, mapping in profiles_by_id.items() if mapping.get(player_id)}})

    # 原始截圖球隊與位置由使用者提供；只用 NBA API 配對球員 ID / 統計，不覆寫 Fantasy 資格。
    for side in PLAYERS:
        for player in PLAYERS[side]:
            entry = name_to_entry.get(normalize_name(player["name"])) or ({"id":player["nba_id"]} if player.get("nba_id") else None)
            if entry:
                player_id = int(entry["id"])
                player["nba_id"] = player_id
                player["profiles"] = {key: mapping[player_id] for key, mapping in profiles_by_id.items()
                                      if mapping.get(player_id)}
                default_key = "season"
                player["profile"] = default_key
                player["stats"] = player["profiles"].get(default_key, {})

    # 已完賽的真實 box score：必須同時有 NBA 官方 Final 狀態及球員該場 game log。
    # 若任一端點失敗，該日標為「未驗證」，絕不假裝是已完賽並鎖定。
    @st.cache_data(ttl=3600, show_spinner=False)
    def fetch_week_finals(week_start_iso):
        from nba_api.stats.endpoints import scoreboardv2, leaguegamelog
        begin = date.fromisoformat(week_start_iso)
        now = today
        final_games = {}
        final_teams = {}
        failures = []
        for offset in range(7):
            d=begin+timedelta(days=offset)
            if d>=now or not any(d in days for days in schedule.values()): continue
            if str(d) in official_lineups:continue
            try:
                frames=scoreboardv2.ScoreboardV2(game_date=d.strftime("%m/%d/%Y"),
                        league_id="00",day_offset=0,timeout=12).get_data_frames()
                header=frames[0]
                id_to_team = {v:k for k,v in TEAM_IDS.items()}
                final_teams[d.isoformat()] = sorted({id_to_team.get(int(row[col]), '')
                    for _,row in header.iterrows() if int(row['GAME_STATUS_ID'])==3
                    for col in ('HOME_TEAM_ID','VISITOR_TEAM_ID')})
                final_games[d.isoformat()] = {
                    str(row["GAME_ID"]) for _,row in header.iterrows()
                    if int(row["GAME_STATUS_ID"])==3
                }
            except Exception as exc:
                failures.append(f"{d.isoformat()}: {type(exc).__name__}")
        game_rows=[]
        if any(final_games.values()):
            try:
                frame=leaguegamelog.LeagueGameLog(season="2026-27",season_type_all_star="Regular Season",
                    player_or_team_abbreviation="P",date_from_nullable=begin.strftime("%m/%d/%Y"),
                    date_to_nullable=(begin+timedelta(days=6)).strftime("%m/%d/%Y"),
                    timeout=20).get_data_frames()[0]
                game_rows=frame.to_dict(orient="records")
            except Exception as exc:
                failures.append(f"Player Game Log: {type(exc).__name__}")
        return final_games, game_rows, failures, final_teams

    final_games={}; game_rows=[]; final_errors=[]; final_teams={}
    if selected_season=='2025-26':
        game_rows = [r for r in logs if week_dates[0].isoformat() <= r['GAME_DATE'][:10] <= week_dates[-1].isoformat()]
        for r in game_rows:
            d=r['GAME_DATE'][:10]
            final_games.setdefault(d,set()).add(str(r['GAME_ID']))
            final_teams.setdefault(d,set()).add(r['TEAM_ABBREVIATION'])
        final_teams={d:sorted(v) for d,v in final_teams.items()}
    elif NBA_API_READY and any(d < today and str(d) not in official_lineups and any(d in days for days in schedule.values()) for d in week_dates):
        with st.spinner("正在確認 NBA 官方已完賽狀態及球員單場 Box Score..."):
            try:
                final_games,game_rows,final_errors,final_teams=fetch_week_finals(week_dates[0].isoformat())
            except Exception as exc:
                final_errors=[f"官方賽事查詢：{type(exc).__name__}"]
    if final_errors:
        st.warning("部分日期無法確認已完賽狀態："+"；".join(final_errors)+"。未確認的比賽不會鎖定。")

    # 將已完賽的官方球員單場數據按 NBA 球員 ID、日期索引。
    # NBA GAME_DATE 是美東 NBA 比賽日期，與週一至週日的選擇一致。
    actual_by_player={}
    for row in game_rows:
        try:
            pid=int(row["PLAYER_ID"])
            day_raw=str(row["GAME_DATE"])
            day=date.fromisoformat(day_raw[:10]).isoformat() if day_raw[:4].isdigit() else __import__("datetime").datetime.strptime(day_raw,"%b %d, %Y").date().isoformat()
            game_id=str(row["GAME_ID"])
            if game_id not in final_games.get(day,set()): continue
            fields={"PTS":"PTS","REB":"REB","AST":"AST","STL":"STL","BLK":"BLK",
                    "3PM":"FG3M","FGM":"FGM","FGA":"FGA","FTM":"FTM","FTA":"FTA","TO":"TOV"}
            values={k:float(row[src] or 0) for k,src in fields.items()}
            actual_by_player.setdefault(pid,{})[day]=values
        except (KeyError,ValueError,TypeError):
            continue

    if selected_season=='2026-27':
        for d in week_dates:
            if d>today:continue
            for pid,row in observed_day(league_state,d,live if d==today else None)['players'].items():
                key=int(pid) if str(pid).isdigit() else pid
                actual_by_player.setdefault(key,{})[str(d)]={('3PM' if k=='FG3M' else 'TO' if k=='TOV' else k):float(row[k]) for k in ['PTS','FG3M','REB','AST','STL','BLK','TOV','FGM','FGA','FTM','FTA']}

    for player in CANDIDATES:
        player['actual_by_day'] = actual_by_player.get(player.get('nba_id'), {})
    for side in PLAYERS:
        for player in PLAYERS[side]:
            player["actual_by_day"]=actual_by_player.get(player.get("nba_id"),{})
            if selected_season=='2025-26':
                player['team'] = nba_team_by_id.get(player.get('nba_id'), player['team'])
            player["week"] = [("GAME" if day.isoformat() in player["actual_by_day"] else "OFF") if selected_season=="2025-26" else get_game_status(player["team"], day, schedule) for day in week_dates]


    # NBA directory does not provide Yahoo eligible positions. Search results must be assigned
    # a team and eligible positions explicitly before they can be used in the simulator.
    for player in CANDIDATES:
        player["week"] = ["OFF"] * 7

    HTML = """
    <div id="lineup-app">
      <div class="guide">名單依選秀輪次排序。拖曳新增球員到垃圾桶可移除；點擊先發球員即可編輯預測數據。</div>
      <div class="actions"><label>數據套用 <select id="bulk-profile"></select></label>
      <select id="bulk-side"><option value="both">雙方球隊</option><option value="my">我的球隊</option><option value="opp">對手球隊</option></select>
      <button id="bulk-apply" type="button">套用整週未完賽場次</button><span>已完賽實績與待補實績不受覆寫；缺少所選來源則保留原設定。</span></div>
      <div id="days" class="days"></div>
      <div class="board">
        <section class="roster"><h3>🔵 我的球隊</h3><div id="my-search" class="search-area"></div><div id="my-bench" class="bench"></div><div id="my-trash" class="trash">🗑️ 垃圾桶 · 拖入移除新增球員</div></section>
        <section class="middle">
          <h3>⚔️ 每日對位 <span id="current-day"></span></h3>
          <div class="head"><span>我的先發</span><span>位置</span><span>對手先發</span></div>
          <div id="lineup-rows"></div>
          <div id="message" role="status"></div>
        </section>
        <section class="roster"><h3>🟣 對手球隊</h3><div id="opp-search" class="search-area"></div><div id="opp-bench" class="bench"></div><div id="opp-trash" class="trash">🗑️ 垃圾桶 · 拖入移除新增球員</div></section>
      </div>
      <div class="actions">
        <button id="auto-day" type="button">⚡ 自動排入當天先發（依排名）</button><button id="auto-week" type="button">📅 一鍵排整週</button>
        <span>每天可獨立調整；使用下方儲存模擬保存整週設定。</span>
      </div>
      <section class="sim-save">
        <h3>💾 儲存與還原模擬</h3>
        <div class="sim-save-controls">
          <input id="sim-name" type="text" placeholder="模擬名稱，例如：Week 1 防守型排陣" maxlength="80" />
          <button id="sim-save" type="button">💾 儲存模擬</button>
          <select id="sim-list" aria-label="已儲存的模擬"><option value="">選擇已儲存模擬</option></select>
          <button id="sim-load" type="button">↩ 還原</button>
          <button id="sim-delete" type="button">🗑 刪除</button>
          <button id="sim-export" type="button">⬇ 匯出 JSON</button>
          <label class="sim-import-label">⬆ 匯入 JSON<input id="sim-import" type="file" accept=".json,application/json" hidden /></label>
        </div>
        <div class="note">登入 Google 後，按儲存會納入個人 Drive，同帳號電腦／手機共用；訪客保存於本瀏覽器。舊版紀錄請先還原，再按儲存移轉。儲存包含雙方七天先發、每日數據來源、自訂預測與新增球員。</div>
      </section>
      <section class="summary">
        <h3>📊 每週 9-Cat 預測與差距</h3><p class="cat-rule">9 個類別各自獨立比較：每贏 1 項得 1 分，TO 越低越好；不使用權重。</p>
        <div id="score" class="big-score"></div>
        <div id="weekly-table"></div><div id="weekly-analysis"></div>
        <div class="note">只計算有比賽且已填寫完整預測數據的先發球員。FG% / FT% 依出手及命中計算，TO 越低越好。尚未填寫的球員不會被當成 0 分。</div>
      </section>
      <div id="editor" class="editor-backdrop" hidden><div class="editor-panel"><div class="editor-top"><h3 id="editor-title">球員數據設定</h3><button id="editor-close" type="button">✕</button></div><div id="editor-description" class="note"></div><label class="editor-label">當天的數據來源<select id="editor-profile"></select></label><div id="editor-fields" class="editor-fields"></div><div class="editor-buttons"><button id="editor-save" type="button">儲存並重新計算</button><button id="editor-clear" type="button">清除本組數據</button></div><div class="note">NBA Stats 自動提供已存在的賽季／區間數據。每一天各自儲存預測來源；官方 Final + Box Score 的比賽數據鎖定。</div></div></div>
    </div>
    """

    CSS = """
    #lineup-app {color:#edf3ff;font-family:system-ui,sans-serif;font-size:13px}
    #lineup-app * {box-sizing:border-box}
    #lineup-app .sim-save {background:#171f30;border:1px solid #34415a;border-radius:12px;padding:14px;margin:14px 0}
    #lineup-app .sim-save-controls {display:flex;gap:8px;align-items:center;flex-wrap:wrap}
    #lineup-app .sim-save-controls input,#lineup-app .sim-save-controls select {background:#222e44;border:1px solid #4b6082;color:#edf3ff;border-radius:7px;padding:9px;min-width:185px}
    #lineup-app .sim-save-controls button,#lineup-app .sim-import-label {background:#305b88;border:1px solid #5b80aa;color:white;border-radius:7px;padding:9px 12px;cursor:pointer;font:inherit}
    #lineup-app .sim-save .note {margin-top:10px}
    #lineup-app h3 {font-size:15px;margin:0 0 12px}
    #lineup-app .guide {color:#b7c9e5;margin:10px 0}
    #lineup-app .days {display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:7px;margin:12px 0}
    #lineup-app .day {background:#202c40;color:#dce8ff;border:1px solid #42516a;border-radius:8px;padding:10px 4px;cursor:pointer}
    #lineup-app .day.active {background:#2b5d91;border-color:#8bd2ff;color:white;font-weight:700}
    #lineup-app .board {display:grid;grid-template-columns:minmax(145px,0.75fr) minmax(860px,6fr) minmax(145px,0.75fr);gap:10px;min-width:1180px}
    #lineup-app .roster,#lineup-app .middle,#lineup-app .summary {background:#151d2d;border:1px solid #35425b;border-radius:12px;padding:12px}
    #lineup-app .bench {background:#1d293b;border:1px dashed #506482;border-radius:8px;min-height:300px;padding:4px}
    #lineup-app .head,#lineup-app .lineup-row {display:grid;grid-template-columns:minmax(0,1fr) 39px minmax(0,1fr);align-items:stretch;gap:5px}
    #lineup-app .head {text-align:center;color:#aebfd9;font-size:11px;margin-bottom:7px}
    #lineup-app .lineup-row {margin-bottom:5px;min-height:67px}
    #lineup-app .pos {display:flex;align-items:center;justify-content:center;font-weight:750}
    #lineup-app .slot {background:#202b3e;border:1px dashed #5b6e89;border-radius:7px;padding:3px;min-height:67px;min-width:0}
    #lineup-app .slot.over,#lineup-app .bench.over {background:#2d4965;border-color:#64d9ff}
    #lineup-app .player {background:#315b94;color:white;border-radius:6px;padding:5px;margin:3px 0;cursor:grab;min-width:0}
    #lineup-app .player.opp {background:#7334a6}
    #lineup-app .player.off {background:#394357!important;color:#c7d0de;opacity:.85}
    #lineup-app .player.b2b {background:#7c5524!important}
    #lineup-app .player.game {background:#245b52!important}
    #lineup-app .player.opp.game {background:#4d517f!important}
    #lineup-app .player.opp.b2b {background:#78502b!important}
    #lineup-app .player.added {outline:1px solid #7cb5f0}
    #lineup-app .player.in-slot {cursor:pointer}
    #lineup-app .player.in-slot:hover {outline:2px solid #b9d9ff}
    #lineup-app .player-head {display:flex;gap:5px;align-items:center;justify-content:space-between;flex-wrap:nowrap}
    #lineup-app .player-name {font-weight:650;font-size:11px;line-height:1.2}
    #lineup-app .tag {font-size:10px;border-radius:4px;padding:2px 5px;background:#374151;white-space:nowrap;font-size:9px}
    #lineup-app .tag.game {background:#14532d;color:#b5f7ce}
    #lineup-app .tag.b2b {background:#78350f;color:#ffe5a1}
    #lineup-app .week-mini {display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:2px;margin-top:6px}
    #lineup-app .mini {text-align:center;background:#374151;border-radius:3px;font-size:9px;padding:3px 0}
    #lineup-app .mini.game {background:#166534}
    #lineup-app .mini.b2b {background:#92400e}
    #lineup-app .nine {display:flex;gap:2px;overflow-x:auto;white-space:nowrap;margin-top:6px;padding-bottom:3px;scrollbar-width:thin}
    #lineup-app .stat {display:flex;flex-direction:column;align-items:center;flex:1 0 0;min-width:30px;gap:2px;background:#17283f;border-radius:4px;padding:4px 2px}
    #lineup-app .stat small {font-size:9px;color:#c5d3e8}
    #lineup-app .stat b {font-size:9px}
    #lineup-app .search-area {margin-bottom:8px}
    #lineup-app .trash {margin-top:8px;border:1px dashed #9a7280;background:#362b38;border-radius:7px;padding:11px 5px;text-align:center;font-size:10px;color:#ffd7dc}
    #lineup-app .trash.over {background:#803e4c;border-color:#ff9ca9}
    #lineup-app .editor-backdrop {position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,.74);display:flex;align-items:center;justify-content:center;padding:20px}
    #lineup-app .editor-backdrop[hidden] {display:none}
    #lineup-app .editor-panel {width:min(720px,95vw);max-height:90vh;overflow-y:auto;background:#202b40;border:1px solid #667b9b;border-radius:14px;padding:20px;box-shadow:0 18px 50px #0009}
    #lineup-app .editor-top {display:flex;align-items:center;justify-content:space-between}
    #lineup-app .editor-panel button {background:#315d8e;color:white;border:1px solid #658bb7;border-radius:6px;padding:8px 12px;cursor:pointer}
    #lineup-app .editor-label {display:block;margin:12px 0;font-size:12px;color:#b8c9e5}
    #lineup-app .editor-label select {display:block;margin-top:6px;width:100%;background:#172238;color:white;border:1px solid #627795;padding:9px;border-radius:5px}
    #lineup-app .editor-fields {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px}
    #lineup-app .editor-fields label {font-size:11px;color:#cbd8ee}
    #lineup-app .editor-fields input {width:100%;margin-top:5px;padding:8px;border-radius:5px;background:#152237;border:1px solid #546a87;color:white}
    #lineup-app .editor-buttons {display:flex;gap:10px;margin-top:18px}
    #lineup-app .search-area input,#lineup-app .search-area select {width:100%;padding:7px;margin:3px 0;background:#26364c;border:1px solid #506482;border-radius:5px;color:#fff;font-size:11px}
    #lineup-app .search-area button {width:100%;margin:4px 0;padding:7px;background:#254c76;border:1px solid #487db4;border-radius:5px;color:white;cursor:pointer}
    #lineup-app .search-results {max-height:140px;overflow-y:auto}
    #lineup-app .search-results button {font-size:10px;text-align:left}
    #lineup-app .actions {display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:12px 0;color:#aebfd9;font-size:11px}
    #lineup-app button {font:inherit}
    #lineup-app .actions select {background:#202c40;border:1px solid #506482;border-radius:5px;color:white;padding:7px}
    #lineup-app .weights {background:#202b3e;border:1px solid #35425b;border-radius:8px;padding:10px;margin:10px 0}
    #lineup-app #weight-inputs {display:grid;grid-template-columns:repeat(9,minmax(0,1fr));gap:6px;margin-top:8px}
    #lineup-app .weight {display:flex;flex-direction:column;align-items:center;gap:3px;font-size:10px}
    #lineup-app .weight input {width:100%;min-width:0;color:#fff;background:#172238;border:1px solid #506482;border-radius:5px;padding:5px;text-align:center}
    #lineup-app .analysis-line {display:flex;align-items:center;gap:10px;margin:8px 0;font-size:11px}
    #lineup-app .analysis-line .bar {flex:1;height:8px;background:#493754;border-radius:8px;overflow:hidden}
    #lineup-app .analysis-line .bar i {display:block;height:100%;background:#4385a6}
    #lineup-app .analysis-note {color:#aebfd9;font-size:11px;line-height:1.7;margin-top:10px}
    @media(max-width:850px){#lineup-app #weight-inputs {grid-template-columns:repeat(5,minmax(0,1fr))}}
    #lineup-app .actions button {background:#244c77;border:1px solid #487db4;border-radius:7px;color:#fff;padding:9px 12px;cursor:pointer}
    #lineup-app #message {color:#ffcc80;min-height:18px;margin-top:8px}
    #lineup-app .summary {margin-top:12px}
    #lineup-app #score {font-size:19px;font-weight:750;margin:10px 0}
    #lineup-app .big-score {display:flex;align-items:center;justify-content:center;gap:18px;padding:20px 12px;background:#1c2b44;border:1px solid #46658d;border-radius:12px;margin:14px 0!important}
    #lineup-app .big-score strong {font-size:52px;line-height:1;font-variant-numeric:tabular-nums}
    #lineup-app .big-score small {display:block;color:#b6c9e6;font-size:12px;font-weight:400;text-align:center;margin-top:6px}
    #lineup-app .big-score .score-blue {color:#7cc7ff}
    #lineup-app .big-score .score-purple {color:#d5a0ff}
    #lineup-app .locked {border:1px solid #72a4d7;background:#223d52;padding:10px;border-radius:7px;color:#cce8ff}
    #lineup-app .diff {color:#aebed7;text-align:center;font-size:11px}
    #lineup-app .diff.my {color:#8cf0b6}
    #lineup-app .diff.opp {color:#e1b4ff}
    #lineup-app .cat-rule {font-size:12px;color:#bac9df;margin:7px 0}
    #lineup-app .table-wrap {overflow-x:auto}
    #lineup-app table {width:100%;border-collapse:collapse;min-width:700px;text-align:right;font-size:12px}
    #lineup-app th,#lineup-app td {padding:10px 9px;border-bottom:1px solid #35425b}
    #lineup-app th:first-child,#lineup-app td:first-child {text-align:left}
    #lineup-app .win {color:#8cf0b6;font-weight:750}
    #lineup-app .note {font-size:11px;color:#9eb1cf;margin-top:10px;line-height:1.6}
    @media(max-width:1100px){#lineup-app .board {overflow:visible}#lineup-app .days {min-width:650px}}
    """

    JS = r"""
    export default function(component) {
      const root = component.parentElement.querySelector("#lineup-app");
      if (!root) return;
      const data = component.data ?? {};
      const players = structuredClone(data.players ?? {my:[],opp:[]});
      const candidates = data.candidates ?? [];
      const teamWeeks = data.team_weeks ?? {};
      const weekDates = data.week_dates ?? [];
      const positions = ["PG","SG","G","PF","SF","F","C1","C2","UTIL1","UTIL2"];
      const cats = ["PTS","REB","AST","STL","BLK","3PM","FG%","FT%","TO"];
      const sums = ["PTS","REB","AST","STL","BLK","3PM","FGM","FGA","FTM","FTA","TO"];
      const dayNames = ["一","二","三","四","五","六","日"];
      const empty = () => ({my:Object.fromEntries(positions.map(p=>[p,null])),
                           opp:Object.fromEntries(positions.map(p=>[p,null]))});
      const state = weekDates.map(empty);
      function applyOfficialLineups(){
        for(let i=0;i<weekDates.length;i++)for(const side of ['my','opp']){
          const slots=data.official_lineups?.[weekDates[i]]?.[side];
          if(slots)state[i][side]=Object.fromEntries(positions.map(pos=>[pos,slots[pos]??null]));
        }
      }
      const searches={my:"",opp:""};
      let dayIndex = Math.max(0, weekDates.indexOf(data.selected_date));
      let dragging = null;
      let editing = null;
      const profileLabels={two_weeks:"2026–27 最近兩週（真實統計）",one_week:"2026–27 最近一週（真實統計）",month:"2026–27 最近一個月（真實統計）",season:"2025–26 賽季平均（真實統計）",manual:"自訂預測（手動編輯）"};
      const requiredStats=["PTS","REB","AST","STL","BLK","3PM","FGM","FGA","FTM","FTA","TO"];
      const completeStats=s=>requiredStats.every(k=>Number.isFinite(s?.[k])&&s[k]>=0) && s.FGM<=s.FGA && s.FTM<=s.FTA;
      const dailyChoices={my:{},opp:{}};
      // One record per matchup week, not tied to the selected day.
      const storageKey="fantasy-gm-v12-simulations:"+(data.owner??"guest");
      let savedDB=structuredClone(data.saved_simulations??{});
      const workingKey=storageKey+":"+JSON.stringify(data.context)+":"+weekDates[0];
      const snapshot=()=>({controller_date:data.selected_date,format:"fantasy-gm-simulation",version:1,week_dates:[...weekDates],
        players:structuredClone(players),lineups:structuredClone(state),
        daily_choices:structuredClone(dailyChoices),selected_day:dayIndex,
        context:data.context,saved_at:new Date().toISOString()});
      function restore(payload){
        if(!payload||payload.format!=="fantasy-gm-simulation"||payload.version!==1 ||
           JSON.stringify(payload.week_dates)!==JSON.stringify(weekDates) ||
           !Array.isArray(payload.lineups)||payload.lineups.length!==7 ||
           !payload.players||!Array.isArray(payload.players.my)||!Array.isArray(payload.players.opp) ||
           !payload.daily_choices) throw Error("檔案格式不符，或不是目前這一週的模擬。請先切換到對應週次。");
        for(const side of ["my","opp"]){
          players[side].splice(0,players[side].length,...structuredClone(payload.players[side]));
          const officialIds=new Set(Object.values(data.official_lineups??{}).flatMap(day=>Object.values(day[side]??{})));
          for(const current of data.players[side])if(officialIds.has(current.id)){
            const index=players[side].findIndex(p=>p.id===current.id);
            if(index<0)players[side].push(structuredClone(current));else players[side][index]=structuredClone(current);
          }
          players[side].forEach(p=>p.week=teamWeeks[p.team]??Array(7).fill("OFF"));
          dailyChoices[side]=structuredClone(payload.daily_choices[side]??{});
        }
        for(let i=0;i<7;i++){
          for(const side of ["my","opp"]){
            if(!payload.lineups[i]?.[side])throw Error("陣容資料不完整。");
            for(const pos of positions){
              const id=payload.lineups[i][side][pos]??null;
              const p=id?players[side].find(x=>x.id===id):null;
              state[i][side][pos]=(p&&plays(p,i)&&eligible(p,pos))?id:null;
            }
          }
        }
        dayIndex=Math.max(0,Math.min(6,Number(payload.selected_day)||0));
        render();
      }
      function readSaved(){return savedDB;}
      function legacySaved(){try{return JSON.parse(localStorage.getItem("fantasy-gm-v11-simulations")||"{}");}catch{return {};}}
      function writeSaved(v){
        savedDB=v;
        try{localStorage.setItem(storageKey,JSON.stringify(v));}catch{}
        component.setTriggerValue('simulation_change',{records:v,active:snapshot(),name:root.querySelector('#sim-name').value.trim()});return true;
      }
      function refreshSaved(){
        const sel=root.querySelector("#sim-list");const old=sel.value;
        sel.replaceChildren(new Option("選擇已儲存模擬",""));
        Object.keys(readSaved()).sort().forEach(n=>sel.add(new Option(n,n)));
        for(const n of Object.keys(legacySaved()).sort())if(!Object.hasOwn(readSaved(),n))sel.add(new Option('舊瀏覽器紀錄 · '+n,'legacy:'+n));
        if(Object.hasOwn(readSaved(),old))sel.value=old;
      }
      root.querySelector("#sim-save").onclick=()=>{
        const name=root.querySelector("#sim-name").value.trim();
        if(!name){setMessage("請先輸入模擬名稱。");return;}
        const db=readSaved();
        if(db[name]&&!confirm(`「${name}」已存在，要覆蓋嗎？`))return;
        db[name]=snapshot();if(writeSaved(db)){refreshSaved();root.querySelector("#sim-list").value=name;setMessage(`正在保存「${name}」…`);}
      };
      root.querySelector("#sim-load").onclick=()=>{
        const name=root.querySelector("#sim-list").value;
        if(!name){setMessage("請先選擇已儲存的模擬。");return;}
        try{const legacy=!Object.hasOwn(readSaved(),name);restore(legacy?legacySaved()[name.slice(7)]:readSaved()[name]);root.querySelector("#sim-name").value=legacy?name.slice(7):name;setMessage(`已還原「${name}」。`);}
        catch(e){setMessage("還原失敗："+e.message);}
      };
      root.querySelector("#sim-delete").onclick=()=>{
        const name=root.querySelector("#sim-list").value;
        if(!name||!confirm(`確定刪除「${name}」？`))return;
        const db=readSaved();delete db[name];if(writeSaved(db)){refreshSaved();setMessage(`已刪除「${name}」。`);}
      };
      root.querySelector("#sim-export").onclick=()=>{
        const payload=snapshot();const blob=new Blob([JSON.stringify(payload,null,2)],{type:"application/json"});
        const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;
        a.download=`fantasy-gm-${weekDates[0]}-${weekDates[6]}.json`;a.click();
        setTimeout(()=>URL.revokeObjectURL(url),1000);setMessage("已匯出目前模擬 JSON，請保留作為備份。");
      };
      root.querySelector("#sim-import").onchange=async e=>{
        const file=e.target.files?.[0];if(!file)return;
        try{const payload=JSON.parse(await file.text());restore(payload);setMessage(`已匯入 ${file.name}。如需長期保存，請再按「儲存模擬」。`);}
        catch(err){setMessage("匯入失敗："+err.message);}
        e.target.value="";
      };
      refreshSaved();

      const dailyKey=(p,idx)=>`${p.id}::${idx}`;
      const daySetting=(p,side,idx)=>{
        const setting=dailyChoices[side][dailyKey(p,idx)] ?? {profile:p.profile??"season",custom:null};
        return profileLabels[setting.profile]?setting:{profile:'season',custom:null};
      };
      // Server records remain authoritative, including after JSON restore.
      const actual=(p,idx)=>data.actual_by_player?.[p.evidence_id??p.nba_id]?.[weekDates[idx]]??data.actual_by_player?.[p.nba_id]?.[weekDates[idx]]??null;
      const past=(p,idx)=>Boolean(data.final_teams?.[weekDates[idx]]?.includes(p.team)) || weekDates[idx]<data.today || (data.uncertain_days??[]).includes(weekDates[idx]);

      const isLocked=(p,idx)=>actual(p,idx)!==null;
      const dailyStats=(p,side,idx)=>{
        if(isLocked(p,idx))return actual(p,idx);
        if(past(p,idx)||weekDates[idx]<=data.today)return {}; // Missing past/today evidence is not a prediction.
        const setting=daySetting(p,side,idx);
        return setting.profile==="manual"?(setting.custom??{}):(p.profiles?.[setting.profile]??{});
      };


      const getPlayer = (side,id) => players[side].find(p=>p.id===id);
      const location = (side,id,idx=dayIndex) => positions.find(p=>state[idx][side][p]===id);
      const status = (p,idx=dayIndex) => actual(p,idx)!==null?'GAME':data.historical?'OFF':(p.week?.[idx] ?? "OFF");
      const plays = (p,idx=dayIndex) => ["GAME","B2B"].includes(status(p,idx));
      const eligible = (p,pos) => {
        if(pos.startsWith("UTIL")) return true;
        if(pos.startsWith("C")) return p.eligible.includes("C");
        if(pos==="G") return p.eligible.some(x=>["PG","SG","G"].includes(x));
        if(pos==="F") return p.eligible.some(x=>["SF","PF","F"].includes(x));
        return p.eligible.includes(pos);
      };
      const setMessage = s => {root.querySelector("#message").textContent=s;};
      const fmt = (v,cat) => cat==="FG%"||cat==="FT%" ? v.toFixed(1)+"%" : v.toFixed(1);
      const percent = (n,d) => d>0 ? 100*n/d : 0;
      const statsOf = (p,side,idx=dayIndex) => {
        const s=dailyStats(p,side,idx);
        return {...s,"FG%":percent(s.FGM??0,s.FGA??0),"FT%":percent(s.FTM??0,s.FTA??0)};
      };

      function openEditor(p,side) {
        editing={id:p.id,side,idx:dayIndex};
        const modal=root.querySelector("#editor");
        const dateLabel=weekDates[dayIndex];
        const locked=isLocked(p,dayIndex)||weekDates[dayIndex]<=data.today;
        root.querySelector("#editor-title").textContent=`${p.name} · ${dateLabel} · 每日 9-Cat`;
        root.querySelector("#editor-description").textContent=locked
          ? `🔒 單日實績／即時數據（${dateLabel}），唯讀；未取得時留白。`
          : `${p.team} · ${p.eligible.join("/")}。這天的預測獨立設定，不影響其他日期。`;
        const select=root.querySelector("#editor-profile");select.replaceChildren();
        for(const [value,label] of Object.entries(profileLabels)) {
          const opt=document.createElement("option");opt.value=value;opt.textContent=label;select.appendChild(opt);
        }
        const setting=daySetting(p,side,dayIndex);
        select.value=locked?"season":setting.profile;
        select.disabled=locked;
        root.querySelector("#editor-save").disabled=locked;
        root.querySelector("#editor-clear").disabled=locked;
        const draw=()=>{
          const key=select.value;
          const values=locked?actual(p,dayIndex):(key==="manual"?(setting.custom??{}):(p.profiles?.[key]??{}));
          const holder=root.querySelector("#editor-fields");holder.replaceChildren();
          if(locked){
            const note=document.createElement("div");note.className="locked";
            note.textContent="🔒 已取得的實績自動更新；缺少數據不以預測代替。";holder.appendChild(note);
          }
          for(const stat of requiredStats) {
            const label=document.createElement("label");label.textContent=stat;
            const input=document.createElement("input");input.type="number";input.min="0";input.step="0.01";
            input.dataset.stat=stat;input.placeholder=locked?"未取得":key==="manual"?"未填":"資料來源無此數據";
            input.readOnly=locked||key!=="manual";
            input.value=values?.[stat]??"";
            label.appendChild(input);holder.appendChild(label);
          }
        };
        select.onchange=draw;draw();modal.hidden=false;
      }
      function saveEditor(clear=false) {
        if(!editing)return;
        const p=getPlayer(editing.side,editing.id);if(!p)return;
        const idx=editing.idx;
        if(isLocked(p,idx)||weekDates[idx]<=data.today){setMessage("過去與今天使用實績，請選未來日期編輯預測。");return;}
        const key=root.querySelector("#editor-profile").value;
        const values={};
        if(key==="manual"&&!clear){
          for(const input of root.querySelectorAll("#editor-fields input")) {
            if(input.value.trim()!=="")values[input.dataset.stat]=Number(input.value);
          }
          if(values.FGM>values.FGA||values.FTM>values.FTA){alert("FGM 不可大於 FGA，FTM 不可大於 FTA。");return;}
        }
        dailyChoices[editing.side][dailyKey(p,idx)]={profile:key,custom:key==="manual"?values:null};
        root.querySelector("#editor").hidden=true;
        setMessage(`${p.name} ${weekDates[idx]} 已使用 ${profileLabels[key]}${completeStats(dailyStats(p,editing.side,idx))?"":"（此來源資料不完整）"}。`);
        render();
      }
      root.querySelector("#editor-close").onclick=()=>{root.querySelector("#editor").hidden=true;};
      root.querySelector("#editor-save").onclick=()=>saveEditor(false);
      root.querySelector("#editor-clear").onclick=()=>saveEditor(true);
      root.querySelector("#editor").addEventListener("click",e=>{
        if(e.target.id==="editor")root.querySelector("#editor").hidden=true;
      });

      function card(p,side,inSlot=false) {
        const el=document.createElement("div");
        el.className="player"+(side==="opp"?" opp":"")+" "+status(p).toLowerCase()+(p.added?" added":"")+(inSlot?" in-slot":"");
        el.draggable=true;
        const head=document.createElement("div");
        head.className="player-head";
        const name=document.createElement("span");
        name.className="player-name";
        name.textContent=`${p.rank??"?"}. ${p.name}`;
        name.title=`${p.name} · ${p.team} · ${p.eligible.join("/")}`;
        const tag=document.createElement("span");
        const s=status(p);
        tag.className="tag "+(s==="GAME"?"game":s==="B2B"?"b2b":"");
        tag.textContent=s+" · "+p.team;
        head.append(name,tag);
        el.appendChild(head);
        const weekStrip=document.createElement("div");
        weekStrip.style.cssText="display:flex;gap:3px;margin-top:4px";
        const actualWeek=teamWeeks[p.team]??[];
        ["一","二","三","四","五","六","日"].forEach((label,i)=>{
          const box=document.createElement("span");
          const hasGame=data.historical ? actual(p,i)!==null : ["GAME","B2B"].includes(actualWeek[i]);
          box.textContent=label;
          box.style.cssText=`display:inline-flex;align-items:center;justify-content:center;width:15px;height:15px;border-radius:2px;font-size:9px;color:white;background:${hasGame?"#15803d":"#b91c1c"}`;
          box.title=`${weekDates[i]} ${p.team}：${data.historical?(hasGame?"實際有出賽":"未出賽／無紀錄"):(hasGame?"球隊有比賽":"無比賽")}`;
          weekStrip.appendChild(box);
        });
        el.appendChild(weekStrip);
        if (inSlot) {
          if(isLocked(p,dayIndex))el.style.outline="2px solid #83b9e8";
          el.title=isLocked(p,dayIndex)?"🔒 單日實績／即時數據（唯讀）":"點擊設定這位球員當天的預測數據";
          el.addEventListener("click",()=>openEditor(p,side));
          const nine=document.createElement("div");
          nine.className="nine";
          const values=statsOf(p,side);
          for(const cat of cats) {
            const item=document.createElement("span");
            item.className="stat";
            const label=document.createElement("small");label.textContent=cat;
            const val=document.createElement("b");val.textContent=completeStats(dailyStats(p,side,dayIndex)) ? fmt(values[cat]??0,cat) : "—";
            item.append(label,val);nine.appendChild(item);
          }
          el.appendChild(nine);
        } else {
          const info=document.createElement("div");
          info.style.cssText="font-size:9px;color:#e0e8f6;margin-top:3px";
          info.textContent=`${p.eligible.join("/")} · 本週 ${(p.week??[]).filter(x=>x==="GAME"||x==="B2B").length} 場`;
          el.appendChild(info);
          if(p.added) {
            const remove=document.createElement("button");remove.type="button";
            remove.textContent="🗑";remove.title="移除新增的球員";
            remove.style.cssText="background:transparent;border:0;color:#ffd4dc;float:right;cursor:pointer";
            remove.onclick=e=>{e.stopPropagation();removeAdded(side,p.id);};
            el.appendChild(remove);
          }
        }
        el.addEventListener("dragstart",e=>{
          dragging={side,id:p.id};
          e.dataTransfer.setData("text/plain",p.id);
          e.dataTransfer.effectAllowed="move";
        });
        el.addEventListener("dragend",()=>{dragging=null;});
        return el;
      }

      function removeAdded(side,id) {
        const p=getPlayer(side,id);
        if(!p||!p.added){setMessage("原始名單球員不能刪除；只能移除後來新增的球員。");return;}
        players[side]=players[side].filter(x=>x.id!==id);
        for(const day of state)for(const pos of positions)if(day[side][pos]===id)day[side][pos]=null;
        render();setMessage(`${p.name} 已從名單與本週排陣移除。`);
      }
      function trashTarget(el,side) {
        el.addEventListener("dragover",e=>{
          if(!dragging||dragging.side!==side)return;
          e.preventDefault();el.classList.add("over");
        });
        el.addEventListener("dragleave",()=>el.classList.remove("over"));
        el.addEventListener("drop",e=>{
          e.preventDefault();el.classList.remove("over");
          if(dragging&&dragging.side===side)removeAdded(side,dragging.id);
          dragging=null;
        });
      }

      function dropTarget(el,side,pos=null) {
        el.addEventListener("dragover",e=>{
          if(!dragging||dragging.side!==side)return;
          e.preventDefault();el.classList.add("over");
        });
        el.addEventListener("dragleave",()=>el.classList.remove("over"));
        el.addEventListener("drop",e=>{
          e.preventDefault();el.classList.remove("over");
          if(!dragging||dragging.side!==side)return;
          const p=getPlayer(side,dragging.id);
          if(!p)return;
          if(pos&&!plays(p)){setMessage(`${p.name} 當天 ${status(p)}，不能排入先發。`);return;}
          if(pos&&!eligible(p,pos)){setMessage(`${p.name} 不符合 ${pos} 位置資格。`);return;}
          const old=location(side,p.id);
          const occupant=pos?state[dayIndex][side][pos]:null;
          if(old===pos)return;
          // 佔位交換：被替換的球員只有在符合原位置資格時才交換；否則回板凳。
          if(old)state[dayIndex][side][old]=null;
          if(pos)state[dayIndex][side][pos]=p.id;
          if(occupant&&old) {
            const other=getPlayer(side,occupant);
            if(other&&plays(other)&&eligible(other,old))state[dayIndex][side][old]=occupant;
          }
          setMessage("");render();
        });
      }

      function totals(side) {
        const result=Object.fromEntries(sums.map(k=>[k,0]));
        let playerGames=0;
        for(let i=0;i<state.length;i++) {
          for(const pos of positions) {
            const id=state[i][side][pos];
            if(!id)continue;
            const p=getPlayer(side,id);
            if(!p||!plays(p,i))continue;
            playerGames++;
            const s=dailyStats(p,side,i);
            if(!completeStats(s)){result.missing=(result.missing??0)+1;continue;}
            result.validGames=(result.validGames??0)+1;
            for(const k of sums)result[k]+=Number(s[k]);
          }
        }
        result["FG%"]=percent(result.FGM,result.FGA);
        result["FT%"]=percent(result.FTM,result.FTA);
        result.playerGames=playerGames;
        return result;
      }

      function summary() {
        const a=totals("my"),b=totals("opp");
        const hasStats=(a.validGames??0)>0&&(b.validGames??0)>0;
        let my=0,opp=0,ties=0;
        const valid=hasStats;
        const provisional=Boolean(a.missing||b.missing);
        const rows=cats.map(cat=>{
          const av=a[cat]??0,bv=b[cat]??0;
          const diff=cat==="TO"?bv-av:av-bv;
          const winner=!valid||Math.abs(diff)<1e-8?"tie":diff>0?"my":"opp";
          if(valid){if(winner==="my")my++;else if(winner==="opp")opp++;else ties++;}
          return {cat,av,bv,winner};
        });
        const score=root.querySelector("#score");score.replaceChildren();
        const scoreHtml=`<div><strong class="score-blue">${my}</strong><small>🔵 我的球隊</small></div>
          <span style="font-size:30px;color:#9eb1cf">—</span>
          <div><strong class="score-purple">${opp}</strong><small>🟣 對手球隊</small></div>`;
        score.innerHTML=valid?scoreHtml:`<div style="text-align:center">—　—<small>雙方尚無可比較的有效球員數據</small></div>`;
        const coverage=document.createElement("div");coverage.className="analysis-note";
        coverage.textContent=`${provisional?"⚠️ 暫時比分｜":""}資料覆蓋：我方 ${a.validGames??0}/${a.playerGames}、對手 ${b.validGames??0}/${b.playerGames} 次球員上場${ties?`；${ties} 項平手`:""}。`;
        score.after(coverage);
        root.querySelectorAll(".summary > .analysis-note").forEach((n,i)=>{if(i>0)n.remove();});
        const holder=root.querySelector("#weekly-table");
        holder.replaceChildren();
        const wrap=document.createElement("div");wrap.className="table-wrap";
        const table=document.createElement("table");
        const thead=document.createElement("thead");
        const h=document.createElement("tr");
        ["9-Cat","我的球隊","差距（我方 − 對手）","對手球隊","領先方"].forEach(s=>{
          const th=document.createElement("th");th.textContent=s;h.appendChild(th);
        });
        thead.appendChild(h);table.appendChild(thead);
        const body=document.createElement("tbody");
        for(const r of rows) {
          const tr=document.createElement("tr");
          const delta=r.av-r.bv;
          const gap=valid?`${delta>0?"+":""}${fmt(delta,r.cat)}`:"—";
          const cells=[r.cat,(a.validGames??0)>0?fmt(r.av,r.cat):"—",gap,(b.validGames??0)>0?fmt(r.bv,r.cat):"—",
            !valid?"—":r.winner==="my"?"🔵 我方":r.winner==="opp"?"🟣 對手":"平手"];
          cells.forEach((v,i)=>{
            const td=document.createElement("td");td.textContent=v;
            if(valid&&((i===1&&r.winner==="my")||(i===3&&r.winner==="opp")))td.className="win";
            tr.appendChild(td);
          });
          body.appendChild(tr);
        }
        table.appendChild(body);wrap.appendChild(table);holder.appendChild(wrap);
        const analysis=root.querySelector("#weekly-analysis");analysis.replaceChildren();
        if(provisional||!valid){
          const note=document.createElement("div");note.className="analysis-note";
          note.textContent=`⚠️ 暫時比較：我方缺 ${a.missing??0} 場、對手缺 ${b.missing??0} 場。只加總有資料的球員，未取得數據不代表 0；目前比分可能隨補齊資料而改變。`;
          analysis.appendChild(note);
          if(!valid)return;
        }
        const note=document.createElement("div");note.className="analysis-note";
        note.textContent="過去／今天採已讀取的單日實績；未來依每天選定的場均預測，不是比賽勝率。FG%／FT% 以 FGM/FGA、FTM/FTA 加權；TO 越少越好。";
        analysis.appendChild(note);
      }

      // 搜尋候選球員：左右獨立；加入後排名接在既有球員之後。
      function renderSearch(side) {
        const host=root.querySelector("#"+side+"-search");
        host.replaceChildren();
        const input=document.createElement("input");
        input.placeholder="搜尋可加入的球員";
        input.value=searches[side];
        host.appendChild(input);
        const results=document.createElement("div");results.className="search-results";
        host.appendChild(results);
        const renderResults=()=>{
          searches[side]=input.value;
          results.replaceChildren();
          const q=input.value.trim().toLowerCase();
          if(q.length<2)return;
          const found=candidates.filter(p=>p.name.toLowerCase().includes(q)&&
            !players[side].some(x=>x.name.toLowerCase()===p.name.toLowerCase())).slice(0,12);
          for(const p of found){
            const btn=document.createElement("button");btn.type="button";
            btn.textContent=`＋ ${p.name} (${p.team})`;
            btn.addEventListener("click",()=>{
              const rank=players[side].length+1;
              const code=(p.team||"").toUpperCase();
              if(!teamWeeks[code]){
                setMessage(`${p.name} 的 NBA 球隊尚未從官方資料取得；請稍後重試，不會要求你手動輸入。`);
                return;
              }
              const eligibleText=prompt("請輸入 Yahoo 位置資格，逗號分隔（例如 PG,SG）", "PG,SG");
              if(eligibleText===null)return;
              const eligible=eligibleText.toUpperCase().split(",").map(x=>x.trim()).filter(x=>["PG","SG","SF","PF","C","G","F","UTIL"].includes(x));
              if(!eligible.length){alert("至少要有一個有效位置。");return;}
              const profiles=p.profiles??{};
              const profile=profiles.two_weeks?"two_weeks":"season";
              players[side].push({...p,id:side+"-add-"+Date.now()+"-"+Math.random(),rank,added:true,
                team:code,eligible,week:teamWeeks[code],profiles,profile,stats:profiles[profile]??{}});
              searches[side]="";render();setMessage(`${p.name} 已加入${side==="my"?"我的":"對手"}名單，排名 ${rank}。`);
            });results.appendChild(btn);
          }
          if(!found.length){const note=document.createElement("div");note.textContent="NBA 球員目錄無相符結果，或目錄暫時無法載入";note.style.fontSize="10px";results.appendChild(note);}
        };
        input.addEventListener("input",renderResults);renderResults();
        const addTitle=document.createElement("div");
        addTitle.textContent="找不到？手動新增球員";
        addTitle.style.cssText="font-size:10px;color:#aebfd9;margin-top:7px";
        host.appendChild(addTitle);
        const team=document.createElement("select");
        Object.keys(teamWeeks).sort().forEach(code=>{
          const opt=document.createElement("option");opt.value=code;opt.textContent=code;team.appendChild(opt);
        });
        host.appendChild(team);
        const pos=document.createElement("input");pos.placeholder="位置：PG,SG 或 PF,C";
        host.appendChild(pos);
        const add=document.createElement("button");add.type="button";
        add.textContent="＋ 加入輸入的球員";
        add.addEventListener("click",()=>{
          const name=input.value.trim();
          const eligible=pos.value.toUpperCase().split(/[,，\s]+/).filter(Boolean);
          const validPositions=["PG","SG","G","SF","PF","F","C"];
          if(!name||eligible.length===0||eligible.some(p=>!validPositions.includes(p))){
            setMessage("請輸入球員姓名，並填寫正確位置，例如 PG,SG。");return;
          }
          if(players[side].some(p=>p.name.toLowerCase()===name.toLowerCase())){
            setMessage("這位球員已經在名單內。");return;
          }
          const rank=players[side].length+1;
          players[side].push({id:side+"-custom-"+Date.now()+"-"+Math.random(),name,team:team.value,eligible,added:true,
            rank,stats:{},week:teamWeeks[team.value]??Array(7).fill("OFF")});
          searches[side]="";render();setMessage(`${name} 已加入名單，排名 ${rank}；9-Cat 待匯入。`);
        });
        host.appendChild(add);
      }

      // 優先保留較高排名，依位置限制尋找最多可安排的先發球員。
      // 用增廣路徑避免 C、G、F 等稀缺位置被一般 UTIL 佔掉。
      function autoFill(side,idx=dayIndex) {
        const ranked=[...players[side]].filter(p=>plays(p,idx)).sort((a,b)=>(a.rank??999)-(b.rank??999));
        const match=Object.fromEntries(positions.map(pos=>[pos,null]));
        function assign(p,seen) {
          const options=positions.filter(pos=>eligible(p,pos));
          // 對該球員優先使用專屬位置，最後才使用 UTIL。
          options.sort((a,b)=>Number(a.startsWith("UTIL"))-Number(b.startsWith("UTIL")));
          for(const pos of options){
            if(seen.has(pos))continue;
            seen.add(pos);
            if(!match[pos]||assign(match[pos],seen)){match[pos]=p;return true;}
          }
          return false;
        }
        for(const p of ranked)assign(p,new Set());
        state[idx][side]=Object.fromEntries(positions.map(pos=>[pos,match[pos]?.id??null]));
        return positions.filter(pos=>match[pos]).length;
      }

      function render() {
        applyOfficialLineups();
        try{localStorage.setItem(workingKey,JSON.stringify(snapshot()));}catch{}
        const days=root.querySelector("#days");days.replaceChildren();
        weekDates.forEach((d,i)=>{
          const btn=document.createElement("button");
          btn.type="button";btn.className="day"+(i===dayIndex?" active":"");
          btn.textContent=`週${dayNames[i]} · ${d.slice(5)}`;
          btn.addEventListener("click",()=>{dayIndex=i;setMessage("");render();});
          days.appendChild(btn);
        });
        root.querySelector("#current-day").textContent=weekDates[dayIndex]??"";
        for(const side of ["my","opp"]) {
          renderSearch(side);
          const trash=root.querySelector("#"+side+"-trash");trashTarget(trash,side);
          const bench=root.querySelector("#"+side+"-bench");
          bench.replaceChildren();dropTarget(bench,side);
          for(const p of players[side])if(!location(side,p.id))bench.appendChild(card(p,side));
        }
        const rows=root.querySelector("#lineup-rows");rows.replaceChildren();
        for(const pos of positions) {
          const row=document.createElement("div");row.className="lineup-row";
          const label=document.createElement("div");label.className="pos";
          label.textContent=pos.replace(/[12]$/,"");
          const slots={};
          for(const side of ["my","opp"]) {
            const slot=document.createElement("div");slot.className="slot";
            dropTarget(slot,side,pos);
            const id=state[dayIndex][side][pos];
            if(id) {const p=getPlayer(side,id);if(p)slot.appendChild(card(p,side,true));}
            slots[side]=slot;
          }
          row.append(slots.my,label,slots.opp);rows.appendChild(row);
        }
        summary();
      }

      root.querySelector("#auto-day").addEventListener("click",()=>{
        const a=autoFill("my",dayIndex),b=autoFill("opp",dayIndex);
        render();setMessage(`已按名單排名自動排陣：我方 ${a}/10、對手 ${b}/10。`);
      });

      root.querySelector("#auto-week").addEventListener("click",()=>{
        let my=0,opp=0;
        for(let i=0;i<weekDates.length;i++){
          my+=autoFill("my",i);
          opp+=autoFill("opp",i);
        }
        render();setMessage(`整週已排完：我方 ${my}、對手 ${opp} 球員場次；策略：名單排名。`);
      });

      const bulk=root.querySelector('#bulk-profile');
      for(const [value,label] of Object.entries(profileLabels)){
        if(value==='manual')continue;
        const option=document.createElement('option');option.value=value;option.textContent=label;bulk.appendChild(option);
      }
      bulk.value='season';
      root.querySelector('#bulk-apply').onclick=()=>{
        const target=root.querySelector('#bulk-side').value;
        let changed=0,skipped=0;
        for(const side of target==='both'?['my','opp']:[target])for(const p of players[side])for(let i=0;i<7;i++){
          if(isLocked(p,i)||past(p,i)||weekDates[i]<=data.today||!plays(p,i))continue;
          if(!completeStats(p.profiles?.[bulk.value])){skipped++;continue;}
          dailyChoices[side][dailyKey(p,i)]={profile:bulk.value,custom:null};changed++;
        }
        render();setMessage(`已套用 ${changed} 場；${skipped} 場缺少來源而保留。已完賽一律使用實績。`);
      };
      let working=null;try{working=JSON.parse(localStorage.getItem(workingKey)||'null');}catch{}
      const nonce=data.restore_nonce??'';
      let seenNonce='';try{seenNonce=localStorage.getItem(workingKey+':restore')??'';}catch{}
      const restored=nonce && nonce!==seenNonce ? data.restore : (working??data.restore);
      if(restored && JSON.stringify(restored.week_dates)===JSON.stringify(weekDates)){
        try{
          if(restored===working && working.controller_date!==data.selected_date)restored.selected_day=Math.max(0,weekDates.indexOf(data.selected_date));
          restore(restored);root.querySelector('#sim-name').value=data.restore_name??'';
          try{localStorage.setItem(workingKey+':restore',nonce);}catch{}
        }catch(e){render();setMessage('還原失敗：'+e.message);}
      }else render();
    }
    """

    if lite:
        from matchup_lite import LITE_CSS, enhance_lite
        HTML = HTML.replace("名單依選秀輪次排序。拖曳新增球員到垃圾桶可移除；點擊先發球員即可編輯預測數據。", "從底部選擇我的／對手球隊，拖曳或點選姓名再點位置；點頭像查看當天數據。")
        CSS += LITE_CSS
        JS = enhance_lite(JS)

    if st.session_state.get("visual_theme") == "戰術板草圖":
        from tactics_theme import COMPONENT_CSS
        CSS = COMPONENT_CSS.split(";",1)[0]+";"+CSS+COMPONENT_CSS.split(";",1)[1]

    if st.session_state.get("visual_theme") == "簡約淺色":
        from light_theme import COMPONENT_CSS
        CSS += COMPONENT_CSS

    theme_id = {"簡約淺色": "light", "戰術板草圖": "tactics"}.get(st.session_state.get("visual_theme"), "mirror")
    lineup = st.components.v2.component(
        ("fantasy_gm_matchup_lite" if lite else "fantasy_gm_integrated_9cat_v13") + "_" + theme_id,
        html=HTML, css=CSS, js=JS,
    )
    context={'season':selected_season,'my_team':my_team,'opp_team':opp_team}
    restore_payload=st.session_state.get('_sim_restore')
    if restore_payload and restore_payload.get('context')!=context:restore_payload=None
    result=lineup(
        on_simulation_change_change=lambda:None,
        key='matchup_board_'+('lite' if lite else 'desktop'),
        data={
            "owner":st.session_state.get('_account_id','guest'),
            "saved_simulations":saved_simulations,
            "context":context,
            "restore":restore_payload,
            "restore_nonce":st.session_state.get("_sim_restore_nonce",""),
            "restore_name":st.session_state.get('_sim_restore_name',''),
            "selected_date":selected_date.isoformat(),
            "today":today.isoformat(),
            "historical":selected_season=="2025-26",
            "uncertain_days":[d.isoformat() for d in week_dates if d<=today and d.isoformat() not in final_games and any(d in days for days in schedule.values())],
            "actual_by_player":actual_by_player,
            "official_lineups":official_lineups,
            "final_teams":final_teams,
            "week_dates":[d.isoformat() for d in week_dates],
            "players":PLAYERS,
            "candidates":CANDIDATES,
            "team_weeks": {team: [get_game_status(team, day, schedule) for day in week_dates] for team in TEAM_IDS},
        },
        height="content",
    )
    change=result.get('simulation_change')
    if change:
        try:
            save_simulations(change['records'])
            st.session_state['_sim_restore']=change.get('active')
            st.session_state['_sim_restore_name']=str(change.get('name',''))[:80]
            from browser_records import save_browser_records
            from account_store import finish_account
            save_browser_records();finish_account()
            if st.session_state.get('_account_conflict') or st.session_state.get('_account_save_error'):
                st.warning('此裝置已保存，但 Google 同步尚未完成，請到設定查看狀態。')
            else:
                st.session_state['_sim_saved_notice']=True
                st.rerun()
        except (ValueError,TypeError,KeyError) as exc:st.error('模擬未保存：'+str(exc))
    if st.session_state.pop('_sim_saved_notice',False):
        st.success('模擬已保存'+('至個人 Google Drive。' if st.session_state.get('_account_loaded') else '於本裝置。'))
    st.caption("過去／今天採已同步的 Fantasy 單日實績或 NBA 單場數據，顯示更新時間；未來可使用場均與自訂預測。資料缺失會留白。")
