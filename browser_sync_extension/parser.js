// This function is also executed in Yahoo tabs. Keep it self-contained.
function parseYahooDocument(doc, expectedDate, requireDaily=false) {
  const tables=Array.from(doc.querySelectorAll('table'));
  const table=tables.find(t=>/Players roster for \d{4}-\d{2}-\d{2}/.test(t.textContent));
  if (!table) throw new Error('沒有讀到 Yahoo 陣容。請先登入 Yahoo；若有驗證畫面，請自行完成。');
  const found=table.textContent.match(/Players roster for (\d{4}-\d{2}-\d{2})/)[1];
  if (found!==expectedDate) throw new Error('Yahoo 回傳日期不符，已停止同步。');
  const headers=[...table.querySelectorAll('thead tr')].at(-1);
  // Yahoo's other-team Action header spans trade + watch cells.
  // Index both headers and rows by physical column, including colspan.
  const expand=cells=>Array.from(cells).flatMap(c=>Array(Math.max(1,Number(c.colSpan)||1)).fill(c));
  const columns=headers?expand(headers.cells).map(c=>c.textContent.trim()):[];
  const dailySelected=[...doc.querySelectorAll('li.Selected a[href]')].some(a=>{const u=new URL(a.getAttribute('href'),'https://basketball.fantasysports.yahoo.com');return u.searchParams.get('stat1')==='S'&&u.searchParams.get('stat2')==='D';});
  const daily=!!(requireDaily&&dailySelected&&['FGM/A*','FTM/A*','PTS','REB','AST','ST','BLK','TO','3PTM'].every(k=>columns.includes(k)));
  if(requireDaily&&!daily)throw Error('Yahoo 未確認為單日統計，避免誤用賽季累積。');
  const rows=[];let slots=0;
  for(const tr of table.querySelectorAll('tr')) {
    const cells=expand(tr.cells);const pos=cells[0]?.textContent.trim();
    if(!['PG','SG','G','SF','PF','F','C','Util','UTIL','BN','IL','IL+','IR','IR+'].includes(pos)) continue;
    slots++;
    const link=Array.from(tr.querySelectorAll('a')).find(a=>/^https:\/\/sports.yahoo.com\/nba\/players\/\d+\/?$/.test(a.href));
    if(!link){if(!tr.textContent.includes('(Empty)'))throw new Error('球員欄位無法辨識。');continue;}
    const name=link.textContent.trim();const id=link.href.match(/players\/(\d+)/)[1];
    const cell=link.closest('td');const text=cell.innerText||cell.textContent;
    const nba=text.match(/\b([A-Z]{2,3})\s*-\s*((?:PG|SG|SF|PF|C)(?:,(?:PG|SG|SF|PF|C))*)/);
    if(!name || !nba)throw new Error('無法辨識球員位置／NBA 隊伍。');
    const row={yahooPlayerId:id,name,position:pos,eligible:nba[2].split(','),nbaTeam:nba[1]};
    if(daily){
      const text=k=>cells[columns.indexOf(k)]?.textContent.trim()??'';
      const numeric=s=>/^\d+(?:\.\d+)?$/.test(s)?Number(s):null;
      const counts={PTS:text('PTS'),FG3M:text('3PTM'),REB:text('REB'),AST:text('AST'),STL:text('ST'),BLK:text('BLK'),TOV:text('TO')};
      const hasStats=Object.values(counts).some(s=>numeric(s)!==null);
      row.daily_stats=null;
      if(hasStats){
        try {
        const shotEvidence=['FGM/A*','FTM/A*'].some(k=>/^\d+\/\d+$/.test(text(k)));
        const stats={};for(const [k,v] of Object.entries(counts)){stats[k]=(v==='-'&&shotEvidence)?0:numeric(v);if(stats[k]===null)throw Error('單日計數不完整，未套用。');}
        for(const [label,prefix] of [['FGM/A*','FG'],['FTM/A*','FT']]){
          const values=text(label).split('/');
          if(values.length!==2)throw Error('單日命中／出手格式不符。');
          const pair=values.map(v=>v==='-'?0:numeric(v));
          if(pair.some(v=>v===null)||pair[0]>pair[1])throw Error('單日命中／出手數據不符。');
          stats[prefix+'M']=pair[0];stats[prefix+'A']=pair[1];
        }
        row.daily_stats=stats;
        } catch (error) {
          // Keep verified ownership/slots even when a live stat cell is unavailable.
          // Do not turn missing counts into zero or reject every team in the league.
          row.daily_stats=null;row.stats_warning=String(error.message);
        }
      }
      row.game_status=cell.querySelector?.('.ysf-game-status')?.textContent.trim().slice(0,100)??'';
    }
    rows.push(row);
  }
  if(!slots || !rows.length || new Set(rows.map(r=>r.yahooPlayerId)).size!==rows.length)throw new Error('名單不完整或有重複球員，未套用。');
  const name=table.textContent.match(/([^\n]+)'s Players roster for/)[1].trim();
  return {date:found,name,rows,slots,...(daily?{statsScope:'day'}:{})};
}
if(typeof module!=='undefined')module.exports={parseYahooDocument};

async function collectYahooRosterWeek(read,league,ids,day,report=()=>{},cache={},force=false){
  const parts=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
  const val=t=>parts.find(p=>p.type===t).value;const today=val('year')+'-'+val('month')+'-'+val('day');
  if(day>today)throw Error('未來日期不當作實績同步。');
  const start=new Date(day+'T12:00:00Z');start.setUTCDate(start.getUTCDate()-(start.getUTCDay()+6)%7);
  const days=[];for(let i=0;i<7;i++){const d=new Date(start);d.setUTCDate(d.getUTCDate()+i);const key=d.toISOString().slice(0,10);if(key<=today)days.push(key);}
  const snapshots=[];
  for(const date of days){
    if(!force&&date<today&&cache[date]?.checked===today&&cache[date]?.parserVersion===2){snapshots.push(cache[date].snapshot);continue;}
    report('讀取 '+date+' 的 Fantasy 排陣與單日數據');
    const teams=[];let cursor=0;
    async function worker(){while(cursor<ids.length){const id=ids[cursor++];const doc=await read(`/nba/${league}/${id}/team?date=${date}&stat1=S&stat2=D`);teams.push({id,...parseYahooDocument(doc,date,true)});}}
    try{await Promise.all([worker(),worker()]);}catch(e){if(date===day)throw e;continue;}
    const pids=teams.flatMap(t=>t.rows.map(r=>r.yahooPlayerId));if(new Set(pids).size!==pids.length)throw Error('聯盟有重複球員，請重試。');
    const snapshot={schema:1,league,date,capturedAt:new Date().toISOString(),teams,statsScope:'day'};
    snapshots.push(snapshot);cache[date]={checked:today,parserVersion:2,snapshot};
  }
  for(const key of Object.keys(cache).sort().slice(0,-14))delete cache[key];
  return {primary:snapshots.find(s=>s.date===day),history:snapshots.filter(s=>s.date!==day),archives:cache};
}

// Read only the public-facing matchup section, never React state or account data.
function parseYahooMatchupWeek(doc,league,week){
  const base='https://basketball.fantasysports.yahoo.com';
  const dates=[];
  for(const a of doc.querySelectorAll('a[href]')){
    const u=new URL(a.getAttribute('href'),base);
    if(u.pathname!==`/nba/${league}/matchup` || Number(u.searchParams.get('week'))!==week)continue;
    const d=u.searchParams.get('date');if(/^\d{4}-\d{2}-\d{2}$/.test(d??''))dates.push(d);
  }
  const days=[...new Set(dates)].sort();
  if(!days.length)throw Error('Yahoo Week '+week+' 尚無可確認日期。');
  const heading=[...doc.querySelectorAll('h2,h3')].find(h=>h.textContent.trim()==='Matchups');
  const section=heading?.parentElement;
  if(!section)return {week,start:days[0],end:days.at(-1),pairs:[]};
  if(!new RegExp('Week\\s+'+week+'\\s+Matchups').test(section.textContent))throw Error('Yahoo 回傳週次不符。');
  const pairs=[],seen=new Set();
  const teamId=a=>new URL(a.getAttribute('href'),base).pathname.match(new RegExp('^/nba/'+league+'/(\\d+)/?$'))?.[1];
  for(const a of section.querySelectorAll('a[href]')){
    if(!teamId(a))continue;
    let node=a.parentElement;
    while(node && node!==section){
      const ids=[...new Set([...node.querySelectorAll('a[href]')].map(teamId).filter(Boolean))];
      if(ids.length===2){
        const key=[...ids].sort().join(':');
        if(!seen.has(key)){seen.add(key);pairs.push(ids);}break;
      }
      if(ids.length>2)break;node=node.parentElement;
    }
  }
  return {week,start:days[0],end:days.at(-1),pairs};
}

async function collectYahooSchedule(read,league,report=()=>{}){
  const first=await read(`/nba/${league}/matchup?week=1&date=totals`);
  const nums=[...new Set([...first.querySelectorAll('select option')].map(o=>Number(new URL(o.getAttribute('value')??'',`https://basketball.fantasysports.yahoo.com/nba/${league}/matchup`).searchParams.get('week'))).filter(n=>n>0&&n<=40))];
  if(!nums.length)throw Error('Yahoo 尚未提供週次清單。');
  const weeks=[],errors=[];
  // Future weeks use Yahoo's server-rendered team schedule; live cards may be client-only.
  const teamLinks=[...new Set([...first.querySelectorAll('a[href]')].map(a=>new URL(a.getAttribute('href'),'https://basketball.fantasysports.yahoo.com').pathname.match(new RegExp('^/nba/'+league+'/(\\d+)/?$'))?.[1]).filter(Boolean))];
  const home=await read(`/nba/${league}/?module=standings&lhst=sched&sctype=team&scmid=${teamLinks[0]??1}`);
  const ids=[...new Set([...home.querySelectorAll('#schedsubnav a[href]')].map(a=>new URL(a.getAttribute('href'),'https://basketball.fantasysports.yahoo.com').searchParams.get('scmid')).filter(Boolean))];
  if(ids.length<2 || ids.length>30)throw Error('無法確認對戰表的全部球隊。');
  const teamWeeks={};let teamCursor=0;
  async function readTeam(){while(teamCursor<ids.length){const id=ids[teamCursor++];
    const doc=await read(`/nba/${league}/?module=standings&lhst=sched&sctype=team&scmid=${id}`);
    teamWeeks[id]=parseYahooTeamSchedule(doc,league);
  }}
  await Promise.all([readTeam(),readTeam()]);
  // Low concurrency: collect the full season once per day, not on every roster check.
  let cursor=0;
  async function worker(){while(cursor<nums.length){const week=nums[cursor++];
    report('讀取 Yahoo 對戰排程 Week '+week+'/'+Math.max(...nums));
    try{
      const w=parseYahooMatchupWeek(await read(`/nba/${league}/matchup?week=${week}&date=totals`),league,week);
      const pairs=[],seen=new Set();
      for(const id of ids){const other=teamWeeks[id][week];
        if(other && teamWeeks[other]?.[week]===id && !seen.has(id) && !seen.has(other)){seen.add(id);seen.add(other);pairs.push([id,other]);}
      }
      w.pairs=pairs;weeks.push(w);
    }
    catch(e){errors.push('Week '+week+'：'+e.message);}
  }}
  await Promise.all([worker(),worker()]);
  if(!weeks.some(w=>w.pairs.length))throw Error('尚未讀到可確認的對戰配對。');
  return {weeks:weeks.sort((a,b)=>a.week-b.week),errors};
}
function parseYahooTeamSchedule(doc,league){
  const table=[...doc.querySelectorAll('table')].find(t=>/\bWk\b/.test(t.textContent)&&/Opponent/.test(t.textContent));
  if(!table)throw Error('未讀到 Yahoo 球隊對戰表。');
  const out={};
  for(const row of table.querySelectorAll('tbody tr')){
    const week=Number(row.cells[0]?.textContent.trim());
    if(!Number.isInteger(week)||week<1||week>40)continue;
    const ids=[...new Set([...row.querySelectorAll('a[href]')].map(a=>new URL(a.getAttribute('href'),'https://basketball.fantasysports.yahoo.com').pathname.match(new RegExp('^/nba/'+league+'/(\\d+)/?$'))?.[1]).filter(Boolean))];
    if(ids.length===1)out[week]=ids[0];
  }
  return out;
}
if(typeof module!=='undefined')Object.assign(module.exports,{parseYahooMatchupWeek,parseYahooTeamSchedule,collectYahooSchedule,collectYahooRosterWeek});

function parseYahooMatchupTotals(doc,league,expectedIds){
  const table=doc.querySelector('#matchup-wall-header table');
  if(!table)throw Error('Yahoo 對局總表尚未載入。');
  const headers=[...table.querySelectorAll('thead th')].map(c=>c.textContent.trim());
  const counts={'3PTM':'FG3M','PTS':'PTS','REB':'REB','AST':'AST','ST':'STL','BLK':'BLK','TO':'TOV'};
  const index=label=>{const n=headers.indexOf(label);if(n<0)throw Error('Yahoo 對局缺少 '+label);return n;};
  const rows=[...table.querySelectorAll('tbody tr')].map(row=>{
    const link=[...row.querySelectorAll('a[href]')].find(a=>new URL(a.getAttribute('href'),'https://basketball.fantasysports.yahoo.com').pathname.match(new RegExp('^/nba/'+league+'/\\d+/?$')));
    const id=link&&new URL(link.getAttribute('href'),'https://basketball.fantasysports.yahoo.com').pathname.split('/').filter(Boolean).at(-1);
    if(!id)throw Error('Yahoo 對局隊伍無法確認。');
    const totals={};
    for(const [label,key] of Object.entries(counts)){
      const raw=row.cells[index(label)]?.textContent.trim().replaceAll(',','');
      if(!/^\d+(\.\d+)?$/.test(raw??''))throw Error('Yahoo 對局數據未完整，保留上次比分。');
      totals[key]=Number(raw);
    }
    for(const prefix of ['FG','FT']){
      const raw=row.cells[index(prefix+'M/A*')]?.textContent.trim().replaceAll(',','');
      const match=/^(\d+)\/(\d+)$/.exec(raw??'');
      if(!match||Number(match[1])>Number(match[2]))throw Error('Yahoo 對局命中／出手不完整。');
      totals[prefix+'M']=Number(match[1]);totals[prefix+'A']=Number(match[2]);
    }
    const scoreText=row.cells[headers.length-1]?.textContent.trim();
    if(!/^[0-9]$/.test(scoreText??''))throw Error('Yahoo 官方比分欄位未完整，未更新比分。');
    return {id,totals,score:Number(scoreText)};
  });
  if(rows.length!==2||rows[0].id===rows[1].id||expectedIds.some(id=>!rows.some(r=>r.id===id)))throw Error('Yahoo 對局隊伍不符。');
  return rows.map((r,i)=>({...r,opponent:rows[1-i].id}));
}
async function collectYahooMatchupResults(read,league,day,schedule,report=()=>{}){
  const week=(schedule??[]).find(w=>w.start<=day&&day<=w.end);
  if(!week||!week.pairs?.length)throw Error('尚無所選日期的官方對手配對。');
  const teams=[];let cursor=0;
  async function worker(){while(cursor<week.pairs.length){
    const pair=week.pairs[cursor++];report('讀取 Yahoo Week '+week.week+' 官方比分…');
    const doc=await read(`/nba/${league}/matchup?week=${week.week}&date=totals&mid1=${pair[0]}&mid2=${pair[1]}`);
    const dates=parseYahooMatchupWeek(doc,league,week.week);
    if(dates.start!==week.start||dates.end!==week.end)throw Error('Yahoo 比分週次／日期不符。');
    teams.push(...parseYahooMatchupTotals(doc,league,pair));
  }}
  await Promise.all([worker(),worker()]);
  if(new Set(teams.map(t=>t.id)).size!==week.pairs.length*2)throw Error('Yahoo 比分隊伍重複。');
  return {week:week.week,start:week.start,end:week.end,capturedAt:new Date().toISOString(),teams};
}
if(typeof module!=='undefined')Object.assign(module.exports,{parseYahooMatchupTotals,collectYahooMatchupResults});
