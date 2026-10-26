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

def rotation_workflow(league,pool,schedule,team,opponent,start,drops,remaining,ref,weights,allowed=None,mode='本週對局'):
    from weekly_planner import close_category_weights
    monday=start-timedelta(days=start.weekday());days=[monday+timedelta(days=i) for i in range(7)]
    future=[d for d in days if d>=start]
    roster=league['teams'][team];opp=league['teams'].get(opponent,[])
    active=[r for r in roster if r.get('status')!='IL'];drop_ids={str(x) for x in drops}
    drop_ids&={str(r.get('id')) for r in active}
    vacancy=max(0,league.get('capacity',14)-len(active))
    core=[r for r in roster if str(r.get('id')) not in drop_ids]
    def projection(rows):
        total=dict.fromkeys(KEYS,0.);counts={};lineups={}
        for day in future:
            slots=assign_day(rows,pool,schedule,day,weights,ref);lineups[str(day)]=slots
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
    before=projection(roster);enemy=projection(opp)
    scale={c:abs(team_value(enemy,c) or 0) or (ref[c]['mean'] if c in ('FG','FT') else max(ref[c]['mean']*max(enemy['g'],1),1)) for c in CATS}
    priority,margins=close_category_weights(before,enemy,weights)
    original,parts=matchup_score(before,enemy,priority,scale)
    focus=sorted((c for c in margins if weights[c]>0 and margins[c][1]>=.6),key=lambda c:margins[c][1],reverse=True)[:3]
    report=[]
    for day in days:
        if day<start:
            rows=league.get('daily_rosters',{}).get(str(day),{}).get('teams',{}).get(team)
            report.append({'date':str(day),'historical':True,'known':rows is not None,'rows':rows or [],'open':[]});continue
        assigned=before['lineups'][str(day)];retained=assign_day(core,pool,schedule,day,weights,ref)
        slot_ids={str(p['PLAYER_ID']):SLOTS[i] for i,p in assigned.items()}
        rows=[{**r,'slot':slot_ids.get(str(r.get('id')),'IL' if r.get('status')=='IL' else 'BN'),'rotation':str(r.get('id')) in drop_ids} for r in roster]
        report.append({'date':str(day),'historical':False,'known':True,'rows':rows,'open':[pos for i,pos in enumerate(SLOTS) if i not in retained]})
    owners={str(r.get('id')) for rs in league['teams'].values() for r in rs}
    keys=[str(k) for k in (allowed if allowed is not None else pool) if str(k) in pool and str(k) not in owners]
    results=[];team_plans={}
    if remaining and (vacancy or drop_ids):
        for key in keys:
            p=pool[key]
            for drop in ([None]+sorted(drop_ids) if vacancy else sorted(drop_ids)):
                new=[r for r in roster if str(r.get('id'))!=drop]+[{'id':key,'name':p['PLAYER_NAME'],'team':p['team'],'eligible':sorted(p['eligible']),'status':'active','games':1}]
                after=projection(new)
                # Adding a streamer may not push a protected core player off the court.
                displaces_core=False
                for d in future:
                    retained=assign_day([r for r in roster if str(r.get('id')) not in drop_ids],pool,schedule,d,weights,ref)
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
    return {'missing_history':missing_history,'days':report,'rotation_slots':vacancy+len(drop_ids),'vacancies':vacancy,'drops':sorted(drop_ids),'teams':team_recs,'results':results,'before':before,'enemy':enemy,'focus':focus,'margins':margins}

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
    if day<today or not date(2026,10,19)<=day<=date(2027,4,18):raise ValueError('開始日期須為今天或未來')
    remaining=body.get('remaining',0)
    if type(remaining) is not int or not 0<=remaining<=4:raise ValueError('剩餘 add 不符')
    snapshot,entries=load_data();players=snapshot['players'];draft={str(e.get('playerId')):e for e in entries}
    pool={}
    for p in players:
        pid=str(p['PLAYER_ID']);match=re.search(r'\((\w+)\s*-\s*([^)]*)',draft.get(pid,{}).get('position',''))
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
    result=rotation_workflow(league,pool,schedule,team,opponent,day,drops,remaining,ref,weights,allowed)
    def public(a):return {k:v for k,v in a.items() if k!='lineups'}
    result['before']=public(result['before']);result['enemy']=public(result['enemy'])
    selected=[];seen=set()
    for r in result['results']:
        if r['key'] in seen:continue
        seen.add(r['key']);p=pool[r['key']]
        selected.append({**{k:v for k,v in r.items() if k not in ('rows','after')},'after':public(r['after']),'name':p['PLAYER_NAME'],'stats':{c:p[c] for c in KEYS},'drop_name':pool[r['drop']]['PLAYER_NAME'] if r['drop'] else None,'confirmed':r['key'] in league.get('free',[])})
        if len(selected)==5:break
    result['results']=selected;return result
