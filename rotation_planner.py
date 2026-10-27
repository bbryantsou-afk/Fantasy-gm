"""Daily ownership-aware rotation planning before category/player recommendations."""
from datetime import date,timedelta
from collections import defaultdict
from ninecat_model import KEYS,CATS,weighted_z
from team_workbench import SLOTS,eligible,team_value,matchup_score

def assign_day(roster,pool,schedule,day,weights,ref):
    candidates=[]
    for r in roster:
        p=pool.get(str(r.get('id')))
        if r.get('status')=='IL' or not p or day not in schedule.get(p['team'],set()):continue
        candidates.append(p)
    candidates.sort(key=lambda p:weighted_z(p,ref,weights),reverse=True)
    assigned={}
    def place(i,seen):
        for slot,pos in enumerate(SLOTS):
            if slot in seen or not eligible(candidates[i],pos):continue
            seen.add(slot)
            if slot not in assigned or place(assigned[slot],seen):assigned[slot]=i;return True
        return False
    for i in range(len(candidates)):place(i,set())
    return {slot:candidates[i] for slot,i in assigned.items()}

def rotation_workflow(league,pool,schedule,team,opponent,start,drops,remaining,ref,weights,allowed=None,mode='本週對局',layout=None,pregame_teams=None):
    from weekly_planner import close_category_weights
    league={**league,"capacity":13 if str(league.get("sync_league"))=="71585" else league.get("capacity",13)}
    monday=start-timedelta(days=start.weekday());days=[monday+timedelta(days=i) for i in range(7)]
    future=[d for d in days if d>=start]
    from player_portraits import portrait_id,name_key,unique_roster
    def canonical(r):return str(r.get('id') or (portrait_id(r) if portrait_id(r) in pool else 'name:'+name_key(r.get('name',''))))
    roster=[{**r,'id':canonical(r)} for r in unique_roster(league['teams'][team])]
    opp=[{**r,'id':canonical(r)} for r in unique_roster(league['teams'].get(opponent,[]))]
    drop_alias={str(r.get('id') or r.get('name')):canonical(r) for r in league['teams'][team]}
    drop_alias.update({'missing:'+name_key(r.get('name','')):canonical(r) for r in league['teams'][team]})
    drops=[drop_alias.get(str(k),str(k)) for k in drops]
    active=[r for r in roster if r.get('status')!='IL'];drop_ids={str(x) for x in drops}
    drop_ids&={str(r.get('id')) for r in roster}
    vacancy=max(0,league.get('capacity',13)-len(active))
    core=[r for r in roster if str(r.get('id')) not in drop_ids]
    # Accept only the selected teams/week. A stale simulator never changes this week.
    layout=layout if isinstance(layout,dict) and layout.get('context',{}).get('my_team')==team and layout.get('context',{}).get('opp_team')==opponent and layout.get('week_dates')==[str(d) for d in days] else None
    names=['PG','SG','G','PF','SF','F','C1','C2','UTIL1','UTIL2']
    aliases={side:{str(p['id']):str(p.get('nba_id') or (portrait_id(p) if portrait_id(p) in pool else str(p['id']).removeprefix(side+'-'))) for p in layout.get('players',{}).get(side,[])} for side in ('my','opp')} if layout else {}
    returns={};planned=[];issues=[]
    all_owned={canonical(r) for rows in league['teams'].values() for r in rows}
    if layout:
        for player in layout['players'].get('my',[]):
            if not player.get('added'):continue
            key=aliases['my'][str(player['id'])]
            if key in {str(r['id']) for r in roster}:continue
            if key in all_owned:issues.append(player['name']+' 已屬於其他球隊，不能當成自由球員 add');continue
            if key not in pool:issues.append(player['name']+' 缺少場均資料，暫不能計算補強');continue
            placed=[d for d,line in zip(days,layout['lineups']) if str(player['id']) in line.get('my',{}).values()]
            requested=player.get('acquired_date') or (str(min(placed)) if placed else str(start))
            try:acquired=max(start,date.fromisoformat(requested))
            except (ValueError,TypeError):acquired=start
            if acquired>days[-1]:continue
            if any(x['key']==key for x in planned):continue
            planned.append({'key':key,'date':str(acquired),'name':pool[key]['PLAYER_NAME']})
            if player.get('eligible'):pool={**pool,key:{**pool[key],'eligible':set(player['eligible'])}}
    if len(planned)>remaining:issues.append('已計畫 add 超過本週剩餘次數')
    if layout:
        for player in layout['players'].get('my',[]):
            key=aliases['my'].get(str(player['id']))
            if player.get('status')=='IL' and player.get('return_date'):
                try:
                    returned=date.fromisoformat(player['return_date'])
                    if start<=returned<=days[-1]:returns[key]=returned
                except (ValueError,TypeError):pass
        injured={str(r.get('id')) for r in roster if r.get('status')=='IL'}
        for d,line in zip(days,layout['lineups']):
            if d<start:continue
            for raw in line.get('my',{}).values():
                key=aliases['my'].get(str(raw),str(raw))
                if key in injured:returns.setdefault(key,d)
    # An ineligible IL occupant must be activated before any add. Unknown is not O.
    layout_players={aliases.get('my',{}).get(str(p['id']),str(p['id'])):p for p in (layout or {}).get('players',{}).get('my',[])}
    il_blocked=[]
    for r in roster:
        if r.get('status')!='IL':continue
        key=str(r['id']);flag=layout_players.get(key,{}).get('injury_status',r.get('injury_status'))
        if flag is None:
            if key not in returns:issues.append(r['name']+'：請確認 IL 傷病標示（O／非 O），再規劃加人')
        elif flag!='O':
            il_blocked.append(key)
    vacancy=max(0,league['capacity']-sum(r.get('status')!='IL' or str(r['id']) in returns and returns[str(r['id'])]<=start for r in roster))
    def selected_slots(rows,day,side='my'):
        available={str(r.get('id')) for r in rows if r.get('status')!='IL' or side=='my' and str(r.get('id')) in returns and day>=returns[str(r.get('id'))]};out={};used=set()
        if not layout:out=assign_day([{**r,'status':'active'} if str(r.get('id')) in returns and day>=returns[str(r.get('id'))] else r for r in rows],pool,schedule,day,weights,ref);used={str(p['PLAYER_ID']) for p in out.values()}
        for i,name in enumerate(names) if layout else []:
            raw=layout['lineups'][days.index(day)].get(side,{}).get(name)
            key=aliases[side].get(str(raw),str(raw));p=pool.get(key)
            if key in available and key not in used and p and eligible(p,SLOTS[i]) and day in schedule.get(p['team'],set()):out[i]=p;used.add(key)
        if day==start and pregame_teams is not None:
            for i,p in list(out.items()):
                if p['team'] not in pregame_teams:del out[i]
        # A started player's exact dated slot/stat line is immutable.
        counters={'C':0,'UTIL':0}
        for r in league.get('daily_rosters',{}).get(str(day),{}).get('teams',{}).get(team if side=='my' else opponent,[]):
            raw=str(r.get('slot','')).upper()
            if r.get('status')!='active' or raw not in ('PG','SG','G','PF','SF','F','C','UTIL'):continue
            if raw in counters:counters[raw]+=1;raw+=str(counters[raw])
            if r.get('daily_stats') is None or raw not in names:continue
            key=canonical(r);p=pool.get(key)
            if not p:continue
            for i,other in list(out.items()):
                if str(other['PLAYER_ID'])==key:del out[i]
            out[names.index(raw)]={**p,**{c:float(r['daily_stats'].get(c,0)) for c in KEYS}}
        original_ids={str(r.get('id')) for r in (roster if side=='my' else opp)}
        # New streamers fill vacant eligible slots; protected players keep their chosen slots.
        used={str(p['PLAYER_ID']) for p in out.values()}
        for key in sorted(available-original_ids-used):
            p=pool.get(key)
            if not p or day not in schedule.get(p['team'],set()) or (day==start and pregame_teams is not None and p['team'] not in pregame_teams):continue
            for i,pos in enumerate(SLOTS):
                if i not in out and eligible(p,pos):out[i]=p;break
        # Actual locked games take precedence over custom predictions.
        for i,p in list(out.items()):
            key=str(p['PLAYER_ID']);actual=None
            for r in league.get('daily_rosters',{}).get(str(day),{}).get('teams',{}).get(team if side=='my' else opponent,[]):
                if canonical(r)==key and r.get('daily_stats') is not None:actual=r['daily_stats'];break
            raw=next((raw for raw,k in aliases.get(side,{}).items() if k==key),key)
            choice=(layout or {}).get('daily_choices',{}).get(side,{}).get(raw+'::'+str(days.index(day)),{})
            custom=choice.get('custom')
            values=actual if actual is not None else custom
            if values is not None:out[i]={**p,**{c:float(values.get(c,values.get({'FG3M':'3PM','TOV':'TO'}.get(c,c),0))) for c in KEYS}}
        return out
    def projection(rows):
        total=dict.fromkeys(KEYS,0.);counts={};lineups={}
        for day in future:
            slots=selected_slots(rows,day,'opp' if rows is opp else 'my');lineups[str(day)]=slots
            for p in slots.values():
                key=str(p['PLAYER_ID']);counts[key]=counts.get(key,0)+1
                for c in KEYS:total[c]+=p[c]
        # Already elapsed dates use saved daily starters, never today's roster.
        for day in days:
            if day>=start:continue
            for r in league.get('daily_rosters',{}).get(str(day),{}).get('teams',{}).get(team if rows is not opp else opponent,[]):
                if r.get('status')!='active' or r.get('slot') not in ('PG','SG','G','SF','PF','F','C','Util','UTIL') or r.get('daily_stats') is None:continue
                for c in KEYS:total[c]+=r['daily_stats'].get(c,0)
        return {'g':sum(counts.values()),'tot':total,'counts':counts,'missing':[],'lineups':lineups}
    # Compare transactions with keeping current IL ownership unchanged, rather
    # than crediting an activation before its required release has happened.
    planned_returns=dict(returns);returns.clear()
    before=projection(roster);enemy=projection(opp)
    returns.update(planned_returns)
    scale={c:abs(team_value(enemy,c) or 0) or (ref[c]['mean'] if c in ('FG','FT') else max(ref[c]['mean']*max(enemy['g'],1),1)) for c in CATS}
    priority,margins=close_category_weights(before,enemy,weights)
    original,parts=matchup_score(before,enemy,priority,scale)
    focus=sorted((c for c in margins if weights[c]>0 and margins[c][1]>=.6),key=lambda c:margins[c][1],reverse=True)[:3]
    report=[]
    for day in days:
        if day<start:
            rows=league.get('daily_rosters',{}).get(str(day),{}).get('teams',{}).get(team)
            report.append({'date':str(day),'historical':True,'known':rows is not None,'rows':rows or [],'open':[]});continue
        assigned=before['lineups'][str(day)];retained=selected_slots(core,day)
        slot_ids={str(p['PLAYER_ID']):SLOTS[i] for i,p in assigned.items()}
        rows=[{**r,'slot':slot_ids.get(str(r.get('id')),'IL' if r.get('status')=='IL' else 'BN'),'rotation':str(r.get('id')) in drop_ids} for r in roster]
        report.append({'date':str(day),'historical':False,'known':True,'rows':rows,'open':[pos for i,pos in enumerate(SLOTS) if i not in assigned],'rotation_open':[pos for i,pos in enumerate(SLOTS) if i not in retained]})
    owners=all_owned
    keys=[str(k) for k in (allowed if allowed is not None else pool) if str(k) in pool and str(k) not in owners]
    results=[];team_plans={}
    if remaining and (vacancy or drop_ids):
        for key in keys:
            p=pool[key]
            for drop in ([None]+sorted(drop_ids) if vacancy else sorted(drop_ids)):
                new=[r for r in roster if str(r.get('id'))!=drop]+[{'id':key,'name':p['PLAYER_NAME'],'team':p['team'],'eligible':sorted(p['eligible']),'status':'active','games':1}]
                if any(sum(r.get('status')!='IL' or str(r['id']) in returns and d>=returns[str(r['id'])] for r in new)>league['capacity'] for d in future):continue
                after=projection(new)
                # Adding a streamer may not push a protected core player off the court.
                displaces_core=False
                for d in future:
                    retained=selected_slots([r for r in roster if str(r.get('id')) not in drop_ids],d)
                    required={str(x['PLAYER_ID']) for x in retained.values()}
                    actual={str(x['PLAYER_ID']) for x in after['lineups'][str(d)].values()}
                    if not required.issubset(actual):displaces_core=True;break
                if displaces_core or not after['counts'].get(key):continue
                windows=[{'date':d,'position':SLOTS[i]} for d,slots in after['lineups'].items() for i,x in slots.items() if str(x['PLAYER_ID'])==key]
                score,contributions=matchup_score(after,enemy,priority,scale);gains={c:contributions[c]-parts[c] for c in CATS}
                item={'key':key,'drop':drop,'rows':new,'after':after,'gain':score-original,'long':weighted_z(p,ref,weights)-(weighted_z(pool[drop],ref,weights) if drop in pool else 0),'best':max(gains,key=gains.get),'targets':[c for c in focus if gains[c]>0],'windows':windows,'nba_team':p['team']}
                results.append(item)
                group=team_plans.setdefault(p['team'],{'team':p['team'],'windows':set(),'games':0,'net':-999,'candidates':set()})
                group['windows'].update((w['date'],w['position']) for w in windows);group['games']=max(group['games'],len(windows));group['net']=max(group['net'],after['g']-before['g']);group['candidates'].add(key)
    team_recs=sorted(team_plans.values(),key=lambda r:(r['net'],r['games'],len(r['windows'])),reverse=True)
    for r in team_recs:r['windows']=sorted(r['windows']);r['candidates']=len(r['candidates'])
    results.sort(key=lambda r:r['gain'] if mode=='本週對局' else r['long'],reverse=True)
    missing_history=[r['date'] for r in report if r['historical'] and not r['known'] and any(date.fromisoformat(r['date']) in ds for ds in schedule.values())]
    # Non-O IL blocks adds, not waiting. Compare activating on each remaining day
    # against leaving the roster alone, so today's useful streamer is not lost early.
    fixed_returns=dict(returns);automatic=[k for k in il_blocked if k not in fixed_returns]
    variants=[None] if not automatic else [*future,days[-1]+timedelta(days=1)]
    sequences=[]
    for activation in variants:
        returns.clear();returns.update(fixed_returns)
        if activation is not None:returns.update({k:activation for k in automatic})
        sequences.extend(weekly_sequences(roster,pool,schedule,future,drop_ids,vacancy,remaining,ref,weights,keys,enemy,priority,scale,before,selected_slots,league,team,returns,planned,blocked_il=set(il_blocked)))
    returns.clear();returns.update(fixed_returns)
    distinct={}
    for plan in sorted(sequences,key=lambda p:(p['gain'],p['net_games'],-p['adds'],tuple(x['date'] for x in p['steps'])),reverse=True):
        identity=tuple((x['date'],x['add'],x['drop']) for x in plan['steps'])
        distinct.setdefault(identity,plan)
    sequences=list(distinct.values())[:5]
    if issues:sequences=[]
    return {'issues':issues,'planned_adds':planned,'returns':{k:str(v) for k,v in returns.items()},'sequences':sequences,'missing_history':missing_history,'days':report,'rotation_slots':vacancy+len(drop_ids),'vacancies':vacancy,'capacity':league['capacity'],'active_count':sum(r.get('status')!='IL' for r in roster),'il_blocked':il_blocked,'drops':sorted(drop_ids),'teams':team_recs,'results':results,'before':before,'enemy':enemy,'focus':focus,'margins':margins}

def weekly_sequences(roster,pool,schedule,days,drops,vacancy,budget,ref,weights,allowed,enemy,priority,scale,before,select_slots,league,team,returns=None,planned=None,blocked_il=None):
    """Bounded beam search across dated transactions; each state owns its own roster.

    Finalized dates are carried as actual totals. Transactions take effect only on
    their date, consume an add, and never mutate the real roster. Dropped players
    cannot be reacquired (waiver availability is not known).
    """
    if not days or (not budget and not returns) or not (drops or vacancy or planned):return []
    budget=min(int(budget),4);returns=returns or {};planned=planned or []
    if len(planned)>budget:return []
    blocked_il=blocked_il or set()
    def adds_blocked(rows,d):return any(str(r['id']) in blocked_il and (str(r['id']) not in returns or d<returns[str(r['id'])]) for r in rows)
    planned_keys={x['key'] for x in planned}
    historical={c:before['tot'][c]-sum(p[c] for slots in before['lineups'].values() for p in slots.values()) for c in KEYS}
    initial_ids={str(r.get('id')) for r in roster}
    locked={str(d):{str(r.get('id')) for r in league.get('daily_rosters',{}).get(str(d),{}).get('teams',{}).get(team,[]) if r.get('daily_stats') is not None} for d in days}
    # Reserve core players' chosen positions for each date.
    required={str(d):{str(p['PLAYER_ID']) for p in select_slots([r for r in roster if str(r.get('id')) not in drops],d).values()} for d in days}
    def active_count(rows,d):return sum(r.get('status')!='IL' or str(r.get('id')) in returns and d>=returns[str(r.get('id'))] for r in rows)
    def day_value(rows,d):
        if active_count(rows,d)>league.get('capacity',13):return None
        slots=select_slots(rows,d)
        if not required[str(d)].issubset({str(p['PLAYER_ID']) for p in slots.values()}):return None
        return slots
    def add_stats(total,slots):return {c:total[c]+sum(p[c] for p in slots.values()) for c in KEYS}
    def score(total):return matchup_score({'tot':total,'g':1},enemy,priority,scale)[0]
    def estimate(state,index):
        total=state['tot']
        for d in days[index:]:
            slots=day_value(state['rows'],d)
            if slots is None:
                projected=[r for r in state['rows'] if str(r['id']) not in drops and (str(r['id']) in initial_ids or r.get('status')=='IL')]
                slots=select_slots(projected,d)
            total=add_stats(total,slots)
        return score(total)
    states=[{'rows':roster,'tot':historical,'steps':[],'removed':set(),'games':0,'calendar':[]}]
    for index,d in enumerate(days):
        # Candidates are ranked for this remaining schedule, not just today's points.
        holes={future:[pos for i,pos in enumerate(SLOTS) if i not in select_slots([r for r in roster if str(r['id']) not in drops],future)] for future in days[index:]}
        ranked=sorted((k for k in allowed if k not in planned_keys and any(future in schedule.get(pool[k]['team'],set()) and any(eligible(pool[k],pos) for pos in positions) for future,positions in holes.items())),key=lambda k:sum(x in schedule.get(pool[k]['team'],set()) for x in days[index:])*(1+max(-.9,weighted_z(pool[k],ref,priority))),reverse=True)
        # Preserve schedule diversity, including a lower-ranked team with useful B2B dates.
        representatives={}
        for key in ranked:representatives.setdefault(pool[key]['team'],key)
        candidates=list(representatives.values())
        candidates+=(key for key in ranked if key not in candidates)
        candidates=candidates[:40]
        # A returning IL player may need a release, which consumes no add.
        ready=[]
        for state in states:
            variants=[state]
            for _ in range(len(returns)):
                expanded=[]
                for v in variants:
                    if active_count(v['rows'],d)<=league.get('capacity',13):expanded.append(v);continue
                    for r in v['rows']:
                        key=str(r.get('id'))
                        if (key not in drops and key in initial_ids) or (r.get('status')=='IL' and (key not in returns or d<returns[key])) or key in locked[str(d)]:continue
                        step={'date':str(d),'add':None,'add_name':'IL 回歸','nba_team':'','drop':key,'drop_name':r['name'],'confirmed':True,'release_only':True}
                        expanded.append({**v,'rows':[x for x in v['rows'] if x is not r],'steps':v['steps']+[step],'removed':v['removed']|{key}})
                variants=expanded[:12]
            ready.extend(v for v in variants if active_count(v['rows'],d)<=league.get('capacity',13))
        # Fixed user plans are transactions on their own date, never backfilled.
        for fixed in (x for x in planned if x['date']==str(d)):
            acquired=[];key=fixed['key'];p=pool[key]
            for state in ready:
                if adds_blocked(state['rows'],d):continue
                if sum(x['add'] is not None for x in state['steps'])+sum(x['date']>str(d) for x in planned)>=budget:continue
                held={str(r['id']) for r in state['rows']}
                if key in held or key in state['removed']:continue
                choices=sorted(((held&drops)|(held-initial_ids))-locked[str(d)])
                if active_count(state['rows'],d)<league.get('capacity',13):choices=[None]+choices
                for drop in choices:
                    rows=[r for r in state['rows'] if str(r['id'])!=drop]+[{'id':key,'name':p['PLAYER_NAME'],'team':p['team'],'eligible':sorted(p['eligible']),'status':'active'}]
                    if day_value(rows,d) is None:continue
                    step={'date':str(d),'add':key,'add_name':p['PLAYER_NAME'],'nba_team':p['team'],'drop':drop,'drop_name':pool[drop]['PLAYER_NAME'] if drop in pool else None,'confirmed':key in league.get('free',[]),'planned':True}
                    acquired.append({**state,'rows':rows,'steps':state['steps']+[step],'removed':state['removed']|({drop} if drop else set())})
            ready=sorted(acquired,key=lambda state:estimate(state,index),reverse=True)[:12]
        frontier=ready;options=list(ready)
        for depth in range(budget):
            expanded=[]
            for state in frontier:
                if adds_blocked(state['rows'],d):continue
                if sum(x['add'] is not None for x in state['steps'])+sum(x['date']>str(d) for x in planned)>=budget:continue
                held={str(r.get('id')) for r in state['rows']}
                droppable=sorted(((held&drops)|(held-initial_ids))-locked[str(d)])
                if sum(r.get('status')!='IL' or str(r.get('id')) in returns and d>=returns[str(r.get('id'))] for r in state['rows'])<league.get('capacity',13):droppable=[None]+droppable
                for key in candidates:
                    if key in held or key in state['removed']:continue
                    p=pool[key]
                    for drop in droppable:
                        rows=[r for r in state['rows'] if str(r.get('id'))!=drop]+[{'id':key,'name':p['PLAYER_NAME'],'team':p['team'],'eligible':sorted(p['eligible']),'status':'active'}]
                        if sum(r.get('status')!='IL' or str(r.get('id')) in returns and d>=returns[str(r.get('id'))] for r in rows)>league.get('capacity',13):continue
                        slots=day_value(rows,d)
                        # No speculative add today solely to replace it again today.
                        if slots is None or not any(str(v['PLAYER_ID'])==key for v in slots.values()):continue
                        if state['steps'] and state['steps'][-1]['date']==str(d) and drop==state['steps'][-1]['add']:continue
                        step={'date':str(d),'add':key,'add_name':p['PLAYER_NAME'],'nba_team':p['team'],'drop':drop,'drop_name':pool[drop]['PLAYER_NAME'] if drop in pool else None,'confirmed':key in league.get('free',[])}
                        expanded.append({**state,'rows':rows,'steps':state['steps']+[step],'removed':state['removed']|({drop} if drop else set())})
            # Keep distinct holdings and budgets; otherwise redundant operations crowd out good paths.
            unique={}
            for state in expanded:
                identity=(tuple(sorted(str(r.get('id')) for r in state['rows'])),sum(x['add'] is not None for x in state['steps']),tuple(sorted(state['removed'])))
                value=estimate(state,index)
                if identity not in unique or value>unique[identity][0]:unique[identity]=(value,state)
            frontier=[s for _,s in sorted(unique.values(),key=lambda x:x[0],reverse=True)[:12]]
            options+=frontier
            if not frontier:break
        unique={}
        for state in options:
            slots=day_value(state['rows'],d)
            if slots is None:continue
            state={**state,'tot':add_stats(state['tot'],slots),'games':state['games']+len(slots),'calendar':state['calendar']+[{'date':str(d),'lineup':[{'slot':SLOTS[i],'id':str(p['PLAYER_ID']),'name':p['PLAYER_NAME']} for i,p in slots.items()]}]}
            identity=(tuple(sorted(str(r.get('id')) for r in state['rows'])),sum(x['add'] is not None for x in state['steps']),tuple(sorted(state['removed'])))
            value=estimate(state,index+1)
            if identity not in unique or value>unique[identity][0]:unique[identity]=(value,state)
        states=[s for _,s in sorted(unique.values(),key=lambda x:(x[0],-len(x[1]['steps'])),reverse=True)[:12]]
    baseline=score(before['tot']);plans=[];seen=set()
    for state in sorted(states,key=lambda s:(score(s['tot']),-len(s['steps'])),reverse=True):
        if not state['steps']:continue
        if score(state['tot'])-baseline<=1e-9 or state['games']<before['g']:continue
        identity=tuple((s['date'],s['add'],s['drop']) for s in state['steps'])
        if identity in seen:continue
        seen.add(identity)
        plans.append({'steps':state['steps'],'adds':sum(x['add'] is not None for x in state['steps']),'remaining':budget-sum(x['add'] is not None for x in state['steps']),'gain':score(state['tot'])-baseline,'net_games':state['games']-before['g'],'tot':state['tot'],'calendar':state['calendar']})
        if len(plans)==5:break
    return plans

def workflow_request(body):
    """Validated PWA adapter, with no writes to shared rosters or simulations."""
    import json,re
    from pathlib import Path
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from pwa.server import validate_profile
    from ninecat_strategy import load_data
    from ninecat_model import baseline,cohort_ids
    from dashboard_model import regular_schedule
    profile=validate_profile(body['profile']);league=profile['files']['league_rosters.json']
    team=body['team'];opponent=body['opponent']
    if team not in league['teams'] or opponent not in league['teams'] or team==opponent:raise ValueError('球隊不符')
    day=date.fromisoformat(body['start']);today=datetime.now(ZoneInfo('America/New_York')).date()
    if day<today and day-timedelta(days=day.weekday())==today-timedelta(days=today.weekday()):day=today
    if day<today or not date(2026,10,19)<=day<=date(2027,4,18):raise ValueError('開始日期須為今天或未來')
    remaining=body.get('remaining',0)
    if type(remaining) is not int or not 0<=remaining<=4:raise ValueError('剩餘 add 不符')
    snapshot,entries=load_data();players=snapshot['players'];draft={str(e.get('playerId')):e for e in entries}
    pool={}
    for p in players:
        pid=str(p['PLAYER_ID']);match=re.search(r'\((\w+)\s*-\s*([^)]*)',draft.get(pid,{}).get('position',''))
        pool[pid]={**p,'team':match.group(1) if match else p['TEAM_ABBREVIATION'],'eligible':set(match.group(2).split(',')) if match else set()}
    for p in json.loads((Path(__file__).parent/'ninecat_assets/data_2026_27.json').read_text()).get('players',[]):
        pid=str(p['PLAYER_ID'])
        if pid not in pool:
            match=re.search(r'\((\w+)\s*-\s*([^)]*)',draft.get(pid,{}).get('position',''))
            pool[pid]={**p,'team':match.group(1) if match else p['TEAM_ABBREVIATION'],'eligible':set(match.group(2).split(',')) if match else set()}
    for pid,meta in league.get('player_meta',{}).items():
        if pid in pool:pool[pid].update(team=meta.get('team') or pool[pid]['team'],eligible=set(meta.get('eligible',pool[pid]['eligible'])))
    for rows in league['teams'].values():
        for r in rows:
            pid=str(r.get('id'))
            if pid in pool:pool[pid].update(team=r.get('team') or pool[pid]['team'],eligible=set(r.get('eligible') or pool[pid]['eligible']))
    drops=body.get('drops',[])
    if not isinstance(drops,list) or len(drops)>28:raise ValueError('輪轉球員不符')
    weights={c:float(profile['prefs'].get('nc_weight_'+c,1)) for c in CATS}
    ref=baseline(players,cohort_ids(players,entries,'draft'))
    schedule,_=regular_schedule(json.loads((Path(__file__).parent/'nba_schedule_2026_27.json').read_text()))
    allowed=[k for k,p in pool.items() if p.get('GP',0)>=20 and (body.get('research') is True or k in league.get('free',[]))]
    layout=body.get('layout')
    if layout is not None:
        from matchup_records import validate_simulations
        layout=validate_simulations({'planner':layout})['planner']
    from daily_evidence import nba_today
    pregame=set(nba_today(str(day)).get('scheduled_teams',[])) if day==today else None
    result=rotation_workflow(league,pool,schedule,team,opponent,day,drops,remaining,ref,weights,allowed,layout=layout,pregame_teams=pregame)
    def public(a):return {k:v for k,v in a.items() if k!='lineups'}
    result['before']=public(result['before']);result['enemy']=public(result['enemy'])
    selected=[];seen=set()
    for r in result['results']:
        if r['key'] in seen:continue
        seen.add(r['key']);p=pool[r['key']]
        selected.append({**{k:v for k,v in r.items() if k not in ('rows','after')},'after':public(r['after']),'name':p['PLAYER_NAME'],'stats':{c:p[c] for c in KEYS},'drop_name':pool[r['drop']]['PLAYER_NAME'] if r['drop'] else None,'confirmed':r['key'] in league.get('free',[])})
        if len(selected)==5:break
    result['results']=selected;return result
